"""Exercise the real solver-only launcher and solver_train.sh with CPU stubs
for trainer, checkpoint merger and benchmark subprocesses only.
"""
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[3]
RUN = "qwen3_4b_validity_rzero_semantic_novelty_gate_k8_solver_dynamic_mask_4gpu_v1"
SOURCE = "qwen3_4b_validity_rzero_semantic_novelty_gate_k8_solver_negative_4gpu_v1_solver_v1"


def setup(tmp_path):
    for name in ("methods/validity_rzero/run_solver_dynamic_k8.sh", "scripts/solver_train.sh"):
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    (tmp_path / "scripts/validate_hf_checkpoint.py").write_text('''
import sys
from pathlib import Path
assert (Path(sys.argv[1]) / 'config.json').exists()
''')
    (tmp_path / "scripts/model_merger.py").write_text('''
import sys
from pathlib import Path
target = Path(sys.argv[sys.argv.index('--local_dir')+1]) / 'huggingface'
target.mkdir(parents=True, exist_ok=True)
(target / 'config.json').write_text('{}')
''')
    (tmp_path / "fake_train.py").write_text('''
import json, sys
from pathlib import Path
args = dict(arg.split('=', 1) for arg in sys.argv[1:] if '=' in arg)
with Path('train_calls.jsonl').open('a') as f:
    f.write(json.dumps(args) + '\\n')
target = Path(args['trainer.save_checkpoint_path']) / 'global_step_15'
(target / 'actor').mkdir(parents=True, exist_ok=True)
(target / 'dataloader.pt').touch()
(target / 'actor/model_world_size_4_rank_0.pt').touch()
''')
    (tmp_path / "evaluation").mkdir()
    (tmp_path / "evaluation/evaluate_models.py").write_text('''
import json, sys
from pathlib import Path
args = sys.argv
mode = args[args.index('--judge-prompt-mode')+1]
with Path('eval_calls.jsonl').open('a') as f:
    f.write(json.dumps(dict(mode=mode, model=args[-1])) + '\\n')
if mode == 'corrected' and Path('fail_corrected').exists():
    sys.exit(1)
batch = Path(args[args.index('--batch-dir')+1])
batch.mkdir()
(batch / 'summary.csv').write_text('complete\\n')
(batch / 'summary.md').write_text(mode + '\\n')
''')
    binaries = tmp_path / "bin"
    binaries.mkdir()
    python = binaries / "python3"
    python.write_text('#!/bin/bash\nif [ "$1" = "-m" ] && [ "$2" = "verl.trainer.main" ]; then\n'
                      'shift 2\nexec ' + shlex.quote(sys.executable) + ' fake_train.py "$@"\nfi\n'
                      'exec ' + shlex.quote(sys.executable) + ' "$@"\n')
    python.chmod(0o755)
    (binaries / "python").symlink_to("python3")
    (binaries / "sleep").write_text('#!/bin/bash\nexit 0\n')
    (binaries / "sleep").chmod(0o755)
    storage = tmp_path / "storage"
    initial = storage / "models/qwen3_4b_validity_rl_terra_clean_v1/global_step_15/actor/huggingface"
    initial.mkdir(parents=True)
    (initial / "config.json").write_text('{}')
    return {"PATH": str(binaries) + os.pathsep + os.defpath,
            "STORAGE_PATH": str(storage), "HUGGINGFACENAME": "test-user",
            "SOLVER_LOAD_CHECKPOINT": "/old/degraded", "SOLVER_MAX_STEPS": "999",
            "VALIDITY_RZERO_DIVERSITY_MODE": "semantic_novelty_gate"}


def run(tmp_path, env, *args):
    return subprocess.run(["bash", "methods/validity_rzero/run_solver_dynamic_k8.sh", *args],
                          cwd=tmp_path, env=env, capture_output=True, text=True, timeout=30)


def test_reuses_dataset_starts_clean_and_evaluates_both_modes(tmp_path):
    env = setup(tmp_path)
    result = run(tmp_path, env)
    assert result.returncode == 0, result.stdout + result.stderr
    calls = [json.loads(row) for row in (tmp_path / "train_calls.jsonl").read_text().splitlines()]
    assert len(calls) == 1
    config = calls[0]
    assert config['data.train_files'] == f'test-user/{SOURCE}@train'
    assert 'terra_clean_v1/global_step_15/actor/huggingface' in config['worker.actor.model.model_path']
    assert 'trainer.load_checkpoint_path' not in config
    assert config['trainer.max_steps'] == '15'
    assert config['trainer.save_freq'] == '3'
    assert config['algorithm.solver_dynamic_vote'] == config['algorithm.solver_token_masking'] == 'true'
    assert config['algorithm.solver_negative_only'] == 'true'
    assert 'worker.rollout.n' not in config  # original 5, R-Zero 16 is source-specific
    assert 'data.format_prompt_by_source.terra' in config
    evals = [json.loads(row) for row in (tmp_path / "eval_calls.jsonl").read_text().splitlines()]
    assert [row['mode'] for row in evals] == ['rzero-original', 'corrected']
    assert all(RUN + '_solver_v1/global_step_15/actor/huggingface' in row['model'] for row in evals)
    assert run(tmp_path, env).returncode == 2  # no accidental overwrite
    result = run(tmp_path, env, '--resume')
    assert result.returncode == 0, result.stdout + result.stderr
    assert len((tmp_path / 'train_calls.jsonl').read_text().splitlines()) == 1
    assert len((tmp_path / 'eval_calls.jsonl').read_text().splitlines()) == 2


def test_eval_failure_resume_does_not_retrain_or_repeat_completed_mode(tmp_path):
    env = setup(tmp_path)
    (tmp_path / 'fail_corrected').touch()
    assert run(tmp_path, env).returncode != 0
    (tmp_path / 'fail_corrected').unlink()
    result = run(tmp_path, env, '--resume')
    assert result.returncode == 0, result.stdout + result.stderr
    assert len((tmp_path / 'train_calls.jsonl').read_text().splitlines()) == 1
    evals = [json.loads(row)['mode'] for row in (tmp_path / 'eval_calls.jsonl').read_text().splitlines()]
    assert evals == ['rzero-original', 'corrected', 'corrected']
