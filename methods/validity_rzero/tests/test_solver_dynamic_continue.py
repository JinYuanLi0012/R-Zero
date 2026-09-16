"""Run the real continuation/state loop with GPU stages replaced by CPU files."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from methods.validity_rzero.tests.test_novelty_invalid_reward import pipeline_init


ROOT = Path(__file__).resolve().parents[3]
RUN = "qwen3_4b_validity_rzero_semantic_novelty_gate_k8_solver_dynamic_mask_4gpu_v1"
OLD = "qwen3_4b_validity_rzero_semantic_novelty_gate_k8_solver_negative_4gpu_v1"


def checkpoint(path):
    path.mkdir(parents=True, exist_ok=True)
    (path / 'config.json').write_text('{}')
    (path / 'model.safetensors').write_bytes(b'CPU-test-placeholder')


def setup(tmp_path):
    for name in ('methods/validity_rzero/continue_solver_dynamic_k8.sh', 'methods/validity_rzero/run.sh',
                 'scripts/main.sh', 'scripts/rzero_pipeline_state.py', 'scripts/validate_hf_checkpoint.py',
                 'scripts/find_resume_checkpoint.py'):
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    storage = tmp_path / 'storage'
    checkpoint(storage / f'models/{RUN}_solver_v1/global_step_15/actor/huggingface')
    checkpoint(storage / f'models/{OLD}_questioner_v1/global_step_5/actor/huggingface')
    # Mimic the standalone round-1 files; continuation must leave them intact.
    run_root = storage / 'rzero_runs' / RUN
    run_root.mkdir(parents=True)
    (run_root / 'run_config.json').write_text('{"round1": true}')
    (run_root / 'training_complete').touch()
    (tmp_path / 'gpu_stage.py').write_text('''
import json, os, sys
from pathlib import Path
kind, solver, questioner, name = sys.argv[1:]
if kind == 'solver' and os.environ.get('SOLVER_PREPARE_ONLY') == '1':
    kind = 'dataset'
record = dict(kind=kind, solver=solver, questioner=questioner, name=name,
              static_dataset=os.environ.get('SOLVER_TRAIN_FILES'),
              flags=[os.environ.get(k) for k in ['SOLVER_NEGATIVE_ONLY', 'SOLVER_DYNAMIC_VOTE', 'SOLVER_TOKEN_MASKING']],
              k=os.environ.get('VALIDITY_RZERO_NOVELTY_K'),
              scope=os.environ.get('VALIDITY_RZERO_NOVELTY_SCOPE'),
              hits=os.environ.get('VALIDITY_RZERO_NOVELTY_MIN_SAME_HITS'))
with Path('calls.jsonl').open('a') as f:
    f.write(json.dumps(record) + '\\n')
if kind == 'dataset':
    if Path('fail_dataset').exists():
        sys.exit(124)
    receipt = Path(os.environ['SOLVER_DATASET_RECEIPT'])
    receipt.parent.mkdir(parents=True, exist_ok=True)
    audit = receipt.with_name(receipt.stem + '_phase_b.jsonl')
    audit.write_text('{}\\n')
    receipt.write_text(json.dumps(dict(dataset_id='test-user/' + name, filtered_count=1000,
        rzero_sample_count=900, terra_replay_sample_count=100, actual_replay_ratio=.1, phase_b_audit=str(audit))))
else:
    step = 5 if kind == 'questioner' else 15
    model = Path(os.environ['STORAGE_PATH']) / 'models' / name / f'global_step_{step}/actor/huggingface'
    model.mkdir(parents=True)
    (model / 'config.json').write_text('{}')
    (model / 'model.safetensors').write_bytes(b'CPU-test-placeholder')
''')
    for name, kind in (('questioner_train_penalty.sh', 'questioner'), ('solver_train.sh', 'solver')):
        (tmp_path / 'scripts' / name).write_text(f'exec python3 gpu_stage.py {kind} "$@"\n')
    (tmp_path / 'evaluation').mkdir()
    (tmp_path / 'evaluation/evaluate_models.py').write_text('''
import json, sys
from pathlib import Path
args = sys.argv
mode = args[args.index('--judge-prompt-mode')+1]
model = args[-1]
with Path('calls.jsonl').open('a') as f:
    f.write(json.dumps(dict(kind='eval', mode=mode, model=model)) + '\\n')
if Path('fail_eval').exists() and '_solver_v3/' in model and mode == 'corrected':
    sys.exit(1)
batch = Path(args[args.index('--batch-dir')+1])
(batch / '001').mkdir(parents=True)
for name in ['manifest.json', '001/final_results.jsonl', 'summary.csv', 'summary.md']:
    (batch / name).write_text(mode + '\\n')
''')
    return {'PATH': str(Path(sys.executable).parent) + os.pathsep + os.defpath,
            'STORAGE_PATH': str(storage), 'HUGGINGFACENAME': 'test-user',
            'SOLVER_TRAIN_FILES': 'stale/round1@train', 'SOLVER_DATASET_READY': '1',
            'SOLVER_PREPARE_ONLY': '1', 'SOLVER_LOAD_CHECKPOINT': '/degraded',
            'RZERO_FIRST_ROUND': '1', 'RZERO_NUM_ROUNDS': '99', 'SOLVER_DYNAMIC_VOTE': '0'}


def run(tmp_path, env, resume=False):
    return subprocess.run(['bash', 'methods/validity_rzero/continue_solver_dynamic_k8.sh']
                          + (['--resume'] if resume else []), cwd=tmp_path, env=env,
                          capture_output=True, text=True, timeout=60)


def calls(tmp_path):
    return [json.loads(row) for row in (tmp_path / 'calls.jsonl').read_text().splitlines()]


def test_four_rounds_use_previous_models_fresh_data_and_both_evaluators(tmp_path):
    env = setup(tmp_path)
    result = run(tmp_path, env)
    assert result.returncode == 0, result.stdout + result.stderr
    history = calls(tmp_path)
    assert len(history) == 20  # Q, dataset, S, eval-original, eval-corrected x4
    for round_ in range(2, 6):
        q, data, solver, original, corrected = history[(round_ - 2)*5:(round_ - 1)*5]
        assert [x['kind'] for x in [q, data, solver, original, corrected]] == ['questioner', 'dataset', 'solver', 'eval', 'eval']
        assert q['name'] == f'{RUN}_questioner_v{round_}'
        assert f'{RUN}_solver_v{round_-1}/global_step_15/actor/huggingface' in q['solver']
        previous_q = OLD if round_ == 2 else RUN
        assert f'{previous_q}_questioner_v{round_-1}/global_step_5/actor/huggingface' in q['questioner']
        assert data['questioner'].endswith(f'{RUN}_questioner_v{round_}/global_step_5/actor/huggingface')
        assert solver['solver'] == q['solver']
        assert data['name'] == solver['name'] == f'{RUN}_solver_v{round_}'
        assert solver['static_dataset'] is None
        assert solver['flags'] == ['1', '1', '1']
        assert (q['k'], q['scope'], q['hits']) == ('8', 'global', '1')
        assert [original['mode'], corrected['mode']] == ['rzero-original', 'corrected']
        assert original['model'].endswith(f'{RUN}_solver_v{round_}/global_step_15/actor/huggingface')
    root = Path(env['STORAGE_PATH']) / 'rzero_runs' / RUN
    assert json.loads((root / 'run_config.json').read_text()) == {'round1': True}
    state = json.loads((root / 'state/run_state.json').read_text())
    assert state['configuration']['first_round'] == '2'
    assert len(state['stages']) == 20
    assert not any(name.startswith('round_1/') for name in state['stages'])
    summary = json.loads((root / 'summary.json').read_text())
    assert (summary['first_round'], summary['executed_rounds'], summary['rounds']) == (2, 4, 5)
    assert run(tmp_path, env).returncode == 2
    result = run(tmp_path, env, resume=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert calls(tmp_path) == history


def test_resume_mid_continuation_retries_eval_then_advances_models(tmp_path):
    env = setup(tmp_path)
    (tmp_path / 'fail_eval').touch()
    assert run(tmp_path, env).returncode != 0
    assert len(calls(tmp_path)) == 10
    (tmp_path / 'fail_eval').unlink()
    result = run(tmp_path, env, resume=True)
    assert result.returncode == 0, result.stdout + result.stderr
    history = calls(tmp_path)
    assert len(history) == 21
    assert len([row for row in history if row['kind'] == 'solver']) == 4
    assert history[10]['kind'] == 'eval' and history[10]['mode'] == 'corrected'
    assert '_solver_v3/' in history[11]['solver']  # round4 starts from completed S3


def test_continuation_origin_is_part_of_resume_fingerprint(tmp_path):
    q = tmp_path / 'q1'
    checkpoint(q)
    env = {'RZERO_FIRST_ROUND': '2', 'RZERO_INITIAL_QUESTIONER': str(q)}
    result, state = pipeline_init(tmp_path, env)
    assert result.returncode == 0, result.stderr
    result, _ = pipeline_init(tmp_path, dict(env, RZERO_FIRST_ROUND='3'), resume=True)
    assert result.returncode != 0
    assert 'run configuration changed' in result.stderr


def test_label_timeout_change_resumes_dataset_without_retraining_questioner(tmp_path):
    env = setup(tmp_path)
    env['QUESTION_EVAL_TIMEOUT_SECONDS'] = '14400'
    (tmp_path / 'fail_dataset').touch()
    result = run(tmp_path, env)
    assert result.returncode != 0
    assert [row['kind'] for row in calls(tmp_path)] == ['questioner', 'dataset']
    (tmp_path / 'fail_dataset').unlink()
    env['QUESTION_EVAL_TIMEOUT_SECONDS'] = '43200'
    result = run(tmp_path, env, resume=True)
    assert result.returncode == 0, result.stdout + result.stderr
    history = calls(tmp_path)
    assert len([row for row in history if row['kind'] == 'questioner']) == 4
    assert history[2]['kind'] == 'dataset'  # Q2 is already committed, no new Q2 training
