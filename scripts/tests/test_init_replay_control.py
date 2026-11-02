"""CPU-only orchestration tests; training processes are replaced with fixtures."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
BRIDGE = r'''
import json, os, sys
from pathlib import Path
args=sys.argv[1:]
script=args[0]
if script not in ('scripts/questioner_train_penalty.sh','scripts/solver_train.sh'):
    os.execv('/bin/bash',['bash',*args])
solver,questioner,name=args[1:4]
with open(os.environ['CALLS'],'a') as f:
    f.write(json.dumps(dict(script=script,solver=solver,questioner=questioner,
        gate=os.getenv('VALIDITY_RZERO_ENABLED','0'), control=os.getenv('RZERO_INIT_REPLAY_ONLY','0'),
        prepare=os.getenv('SOLVER_PREPARE_ONLY','0')))+'\n')
if os.getenv('SOLVER_PREPARE_ONLY')=='1':
    p=Path(os.environ['SOLVER_DATASET_RECEIPT']);p.parent.mkdir(parents=True,exist_ok=True)
    audit=p.with_name(p.stem+'_phase_b.jsonl');audit.write_text('{}\n')
    p.write_text(json.dumps(dict(dataset_id=os.environ['HUGGINGFACENAME']+'/'+name,
        filtered_count=1000,rzero_sample_count=900,terra_replay_sample_count=100,
        actual_replay_ratio=.1,phase_b_audit=str(audit))))
else:
    step=5 if 'questioner' in script else 15
    p=Path(os.environ['STORAGE_PATH'])/'models'/name/f'global_step_{step}/actor/huggingface'
    p.mkdir(parents=True,exist_ok=True);(p/'config.json').write_text('{}')
    (p/'model.safetensors').write_bytes(b'fixture')
'''


class InitReplayControlTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        shutil.copytree(ROOT/'scripts',self.root/'scripts')
        (self.root/'bin').mkdir()
        stub=self.root/'bin/bash'
        stub.write_text('#!'+sys.executable+'\n'+BRIDGE)
        stub.chmod(0o755)
        self.initial=self.root/'init/global_step_15/actor/huggingface'
        self.initial.mkdir(parents=True)
        (self.initial/'config.json').write_text('{}')
        (self.initial/'model.safetensors').write_bytes(b'fixture')
        self.env={k:v for k,v in os.environ.items() if not k.startswith(
            ('VALIDITY_','RZERO_','TERRA_','QUESTIONER_','SOLVER_','RQUEST_'))}
        self.env.update(PATH=str(self.root/'bin')+os.pathsep+os.environ['PATH'],
            STORAGE_PATH=str(self.root/'storage'),HUGGINGFACENAME='test',
            CALLS=str(self.root/'calls.jsonl'),RZERO_NUM_ROUNDS='2',
            SOLVER_MAX_STEPS='15',SOLVER_MERGE_STEP='15',
            VALIDITY_RZERO_INITIAL_SOLVER=str(self.initial),TERRA_REPLAY_RATIO='.1',
            TERRA_REPLAY_DATASET='fixture/terra')

    def run_pipeline(self,env=None,resume=False):
        return subprocess.run(['/bin/bash','scripts/main.sh','--no-eval',
            *(['--resume'] if resume else []),'fixture/base','control'],
            cwd=self.root,env=env or self.env,text=True,capture_output=True)

    def state(self):
        return json.loads((self.root/'storage/rzero_runs/control/state/run_state.json').read_text())

    def test_control_initialization_two_rounds_and_resume(self):
        self.env.update(VALIDITY_RZERO_ENABLED='0',RZERO_INIT_REPLAY_ONLY='1')
        result=self.run_pipeline()
        self.assertEqual(result.returncode,0,result.stderr+result.stdout)
        calls=[json.loads(line) for line in (self.root/'calls.jsonl').read_text().splitlines()]
        self.assertTrue(all(c['gate']=='0' and c['control']=='1' for c in calls))
        self.assertEqual(calls[0]['solver'],str(self.initial))
        self.assertEqual(calls[0]['questioner'],'fixture/base')
        self.assertTrue(calls[3]['solver'].endswith('control_solver_v1/global_step_15/actor/huggingface'))
        self.assertEqual(len(self.state()['stages']),6)
        result=self.run_pipeline(resume=True)
        self.assertEqual(result.returncode,0,result.stderr+result.stdout)
        self.assertEqual(len((self.root/'calls.jsonl').read_text().splitlines()),6)
        changed=dict(self.env,TERRA_REPLAY_RATIO='.2')
        self.assertNotEqual(self.run_pipeline(changed,resume=True).returncode,0)

    def test_default_rquest_and_explicit_off_resume_identically(self):
        self.env.update(VALIDITY_RZERO_ENABLED='1',VALIDITY_RZERO_DIVERSITY_MODE='semantic_novelty_gate')
        result=self.run_pipeline()
        self.assertEqual(result.returncode,0,result.stderr+result.stdout)
        before=self.state()
        result=self.run_pipeline(dict(self.env,RZERO_INIT_REPLAY_ONLY='0'),resume=True)
        self.assertEqual(result.returncode,0,result.stderr+result.stdout)
        self.assertEqual(before,self.state())

    def test_plain_rzero_keeps_base_initialization(self):
        self.env['VALIDITY_RZERO_ENABLED']='0'
        # An optional Questioner checkpoint must not change the Base Solver.
        self.env['RZERO_INITIAL_QUESTIONER']=str(self.initial)
        result=self.run_pipeline()
        self.assertEqual(result.returncode,0,result.stderr+result.stdout)
        first=json.loads((self.root/'calls.jsonl').read_text().splitlines()[0])
        self.assertEqual(first['solver'],'fixture/base')

    def test_solver_routes_replay_rewards_without_enabling_gates(self):
        stub=self.root/'bin/python3'
        stub.write_text('#!'+sys.executable+'\nimport json,os,sys\n'
            'from pathlib import Path\n'
            'Path(os.environ["TRAIN_ARGS"]).write_text(json.dumps({"args":sys.argv[1:],'
            '"gate":os.getenv("VALIDITY_RZERO_ENABLED")}))\n')
        stub.chmod(0o755)
        sleep=self.root/'bin/sleep';sleep.write_text('#!/bin/sh\nexit 0\n');sleep.chmod(0o755)
        self.env.update(VALIDITY_RZERO_ENABLED='0',RZERO_INIT_REPLAY_ONLY='1',
            SOLVER_DATASET_READY='1',SOLVER_SKIP_MERGE='1',SOLVER_SKIP_FINAL_EVAL='1',
            TRAIN_ARGS=str(self.root/'train_args.json'))
        result=subprocess.run(['/bin/bash','scripts/solver_train.sh',str(self.initial),'base','control'],
            cwd=self.root,env=self.env,text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr+result.stdout)
        command=json.loads((self.root/'train_args.json').read_text())
        self.assertEqual(command['gate'],'0')
        self.assertIn('worker.reward.reward_function=./methods/validity_rzero/mixed_reward.py:compute_score',command['args'])
        self.assertIn('data.format_prompt_by_source.terra=./methods/validity_rl/validity_solver.jinja',command['args'])

    def test_conflicting_or_invalid_switch_fails_before_training(self):
        for gate,control in [('1','1'),('0','invalid')]:
            result=self.run_pipeline(dict(self.env,VALIDITY_RZERO_ENABLED=gate,RZERO_INIT_REPLAY_ONLY=control))
            self.assertNotEqual(result.returncode,0)
            self.assertFalse((self.root/'calls.jsonl').exists())

    def test_replay_mixer_accepts_ungated_baseline_rows(self):
        from methods.validity_rzero.prepare_solver_dataset import build_mixed_rows
        fresh=[{'question':str(i),'answer':str(i),'score':.5} for i in range(9)]
        teacher=[{'id':'teacher','question':'invalid problem','terra_validity':'INVALID',
                  'validity_rl_target':'INVALID','split':'train'}]
        mixed,stats=build_mixed_rows(fresh,teacher,.3,.8,.1,1)
        self.assertEqual(stats['rzero_sample_count'],9)
        self.assertEqual(stats['terra_replay_sample_count'],1)
        self.assertEqual(stats['actual_replay_ratio'],.1)
        self.assertEqual(stats['discarded_by_validity_count'],0)
        self.assertEqual([r['answer'] for r in mixed if r['source']=='terra'],['INVALID'])


if __name__=='__main__': unittest.main()
