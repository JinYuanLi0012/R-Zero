import ast
from contextlib import nullcontext
import json
from pathlib import Path
import random
import types
import pytest
from methods.validity_rzero.domain_curriculum.core import DOMAINS, validated_parents, training_rows
from methods.validity_rzero.semantic_novelty_gate import sample_references_per_candidate
from methods.validity_rzero import semantic_novelty_gate_online as online
from methods.validity_rzero.question_filter import question_skip_reason
from methods.validity_rzero.tests.test_novelty_invalid_reward import pipeline_init
from methods.validity_rzero.tests.test_questioner_diversity import _load_compute_score, _validity_result


def paths():
    return [f'{p} → {leaf}' for p, leaves in DOMAINS for leaf in leaves]


def test_parent_pool_not_leaf_or_shared_panel():
    labels = [paths()[0], paths()[1]] * 12 + [paths()[3]] * 9
    parents = validated_parents(labels, len(labels))
    refs = sample_references_per_candidate(range(len(labels)), 4, 43, parents)
    assert refs == sample_references_per_candidate(range(len(labels)), 4, 43, parents)
    assert len({tuple(v) for v in refs.values()}) > 20
    assert any(labels[i] != labels[j] for i, js in refs.items() for j in js)
    for i, js in refs.items():
        assert len(js) == len(set(js)) == 4
        assert i not in js
        assert all(parents[i] == parents[j] for j in js)
    assert sample_references_per_candidate([0],4,43,{0:'A'}) == {0:[]}
    assert sample_references_per_candidate([0,1],4,43,{0:'A',1:'A'}) == {0:[1],1:[0]}


def test_legacy_sampling_exactly_matches_old_algorithm():
    import hashlib
    expected={}
    for i in range(20):
        seed=int.from_bytes(hashlib.sha256(f'43:{i}'.encode()).digest()[:8],'big')
        expected[i]=random.Random(seed).sample([j for j in range(20) if i!=j],8)
    assert sample_references_per_candidate(range(20),8,43) == expected


@pytest.mark.parametrize('labels',[None,[],['unknown'],['Geometry'],[None]])
def test_missing_or_bad_domains_fail_even_empty_question(monkeypatch,labels):
    monkeypatch.setenv('VALIDITY_RZERO_NOVELTY_SCOPE','parent_domain')
    with pytest.raises(ValueError):online.compute_online_novelty([''],domains=labels)


@pytest.mark.parametrize('question', ['A box holds 3 balls', 'Distribute into boxes', 'BOXES', r'A boxing match', r'\boxedness'])
def test_ordinary_boxes_pass(question):
    assert question_skip_reason(question,'2','latex_only') is None
    assert question_skip_reason(question,'2') == 'box_substring'


@pytest.mark.parametrize('question',[r'Find \boxed{x}',r'Find \boxed {x}',r'Find \boxed'])
def test_latex_boxed_question_still_filtered(question):
    assert question_skip_reason(question,'2','latex_only') == 'latex_boxed_question'


def test_other_filters_and_answer_box_unchanged():
    assert question_skip_reason('证明 x', '2','latex_only') == 'proof_question'
    assert question_skip_reason('q',r'\text{yes}','latex_only') == 'text_answer'
    assert question_skip_reason('q',r'\boxed{2}','latex_only') is None


@pytest.mark.parametrize('env',[{'RZERO_QUESTION_BOX_FILTER':'latex_only'},
    {'VALIDITY_RZERO_DOMAIN_MODE':'balanced_v1','VALIDITY_RZERO_NOVELTY_SCOPE':'parent_domain','VALIDITY_RZERO_NOVELTY_K':'4','RZERO_QUESTION_BOX_FILTER':'latex_only'}])
def test_new_fingerprints_resume_and_reject_changes(tmp_path,env):
    result,state=pipeline_init(tmp_path,env);assert result.returncode==0,result.stderr
    assert state['configuration']['question_box_filter']=='latex_only'
    result,resumed=pipeline_init(tmp_path,env,resume=True);assert result.returncode==0,result.stderr
    assert state==resumed
    for changed in [dict(env,RZERO_QUESTION_BOX_FILTER='legacy'),dict(env,VALIDITY_RZERO_NOVELTY_SCOPE='global') if 'VALIDITY_RZERO_NOVELTY_SCOPE' in env else {}]:
        result,_=pipeline_init(tmp_path,changed,resume=True)
        assert result.returncode!=0


def test_scope_requires_domain_mode(tmp_path):
    result,_=pipeline_init(tmp_path,{'VALIDITY_RZERO_NOVELTY_SCOPE':'parent_domain'})
    assert result.returncode!=0
    assert 'requires balanced_v1' in result.stderr


def test_repeat_reorder_reward_online_alignment(tmp_path,monkeypatch):
    # Start with real domain schedule; mirror repeat then an arbitrary length-balancing permutation.
    import numpy as np
    rows=training_rows(16,1,43,'round1')
    labels=np.repeat([r['domain'] for r in rows],4).tolist()
    permutation=list(range(len(labels)));random.Random(7).shuffle(permutation)
    labels=[labels[i] for i in permutation]
    questions=[f'q{i}' for i in permutation]
    captured=[]
    def fake_gpu(tasks,*args,**kwargs):
        captured.extend(tasks)
        return ({t.cache_key:{'parsed_label':'SAME_TYPE' if t.candidate_index%2==0 else 'DIFFERENT'} for t in tasks},
          {'wall_seconds':0,'retry':{'first_pass_batch_count':1,'first_pass_failure_count':0,'retry_batch_count':0,'retried_request_count':0},'prefix_cache':{'token_hit_rate':None,'enabled_explicitly':True}})
    monkeypatch.setenv('VALIDITY_RZERO_ENABLED','1')
    monkeypatch.setenv('VALIDITY_RZERO_DIVERSITY_MODE','semantic_novelty_gate')
    monkeypatch.setenv('VALIDITY_RZERO_NOVELTY_SCOPE','parent_domain')
    monkeypatch.setenv('VALIDITY_RZERO_NOVELTY_K','4')
    monkeypatch.setenv('VALIDITY_RZERO_SEMANTIC_GPU_IDS','0,1,2,3')
    monkeypatch.setenv('STORAGE_PATH',str(tmp_path))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(online,'resolve_frozen_model',lambda:('/base','rev'))
    monkeypatch.setattr(online.SolverServiceConfig,'from_environment',lambda:types.SimpleNamespace(gpu_ids=('2','3')))
    monkeypatch.setattr(online,'semantic_gpu_handoff',lambda _:nullcontext())
    monkeypatch.setattr(online,'run_gpu_tasks',fake_gpu)
    result_rows=[dict(_validity_result(),question=q) for q in questions]
    compute=_load_compute_score(result_rows,None)
    scores=compute([f'<question>{q}</question> \\boxed{{2}}' for q in questions],['2']*len(questions),domain=labels,uid=[str(i//4) for i in permutation])
    assert len(captured)==len(questions)*4
    parents=validated_parents(labels,len(labels))
    for task in captured:
        assert parents[task.candidate_index]==parents[task.panel_index]
        assert questions[task.candidate_index] in task.prompt
    assert [s['overall'] for s in scores]==[0 if i%2==0 else .4 for i in range(len(questions))]


def test_production_repeat_reorder_and_reward_metadata():
    import numpy as np
    root=Path(__file__).resolve().parents[3]
    def method(path, cls, name):
        tree=ast.parse((root/path).read_text())
        c=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==cls)
        f=next(n for n in c.body if isinstance(n,ast.FunctionDef) and n.name==name)
        mod=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),f],type_ignores=[])
        env={'np':np,'DataProto':types.SimpleNamespace}
        exec(compile(ast.fix_missing_locations(mod),path,'exec'),env)
        return env[name]
    labels=np.array(paths(),dtype=object)
    batch=types.SimpleNamespace(batch=None,non_tensor_batch={'domain':labels,'uid':np.arange(28)},meta_info={})
    repeated=method('verl/protocol.py','DataProto','repeat')(batch,4,True)
    class FakeBatch:
        def __getitem__(self,key): return self
    class Indices:
        def detach(self): return self
        def numpy(self): return order
    order=np.random.default_rng(11).permutation(112)
    repeated.batch=FakeBatch()
    method('verl/protocol.py','DataProto','reorder')(repeated,Indices())
    manager=types.SimpleNamespace(config=types.SimpleNamespace(reward_function_data_keys=[],reward_function_optional_data_keys=['domain','uid']))
    metadata=method('verl/workers/reward/function.py','FunctionRewardManager','reward_data')(manager,repeated)
    assert metadata['domain']==np.repeat(labels,4)[order].tolist()
    for label,uid in zip(metadata['domain'],metadata['uid']):assert label==labels[uid]


def test_new_launchers_only_differ_in_scope_k_and_name():
    root=Path(__file__).resolve().parents[3]/'methods/validity_rzero/domain_curriculum'
    global_script=(root/'run_global_k8_latexonly.sh').read_text()
    local_script=(root/'run_parent_k4_latexonly.sh').read_text()
    assert global_script.replace('global_k8','parent_k4').replace('NOVELTY_K=8','NOVELTY_K=4').replace('NOVELTY_SCOPE=global','NOVELTY_SCOPE=parent_domain')==local_script
    assert 'RZERO_QUESTION_BOX_FILTER=latex_only' in global_script
    assert 'RZERO_QUESTION_BOX_FILTER' not in (root/'run_k8.sh').read_text()
