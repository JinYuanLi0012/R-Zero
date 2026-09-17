import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
NAME = 'octothinker_3b_hybrid_base_rzero_8k_5round_v1'


def setup(tmp_path):
    scripts = tmp_path / 'scripts'
    scripts.mkdir()
    shutil.copy(ROOT / 'scripts/run_octothinker_base.sh', scripts)
    (scripts / 'main.sh').write_text('printf "ARGS:%s\\n" "$*"\nenv\n')
    binaries = tmp_path / 'bin'
    binaries.mkdir()
    python = binaries / 'python3'
    # Stub only heavyweight model resolution. Execute the real entry shell.
    python.write_text(f'#!{sys.executable}\nprint("/cache/original-octo-base")\n')
    python.chmod(0o755)
    # Avoid leaving compile cache directories after each CPU unit test.
    (binaries / 'mktemp').write_text(f'#!/bin/sh\nmkdir -p "{tmp_path}/cache"\nprintf "%s\\n" "{tmp_path}/cache"\n')
    (binaries / 'mktemp').chmod(0o755)
    env = dict(os.environ, PATH=str(binaries) + os.pathsep + os.defpath,
               STORAGE_PATH=str(tmp_path / 'storage'), HUGGINGFACENAME='test-user',
               VALIDITY_RZERO_ENABLED='1', VALIDITY_RZERO_MODEL_FAMILY='qwen',
               VALIDITY_RZERO_INITIAL_SOLVER='/old/step10', VALIDITY_RZERO_SEMANTIC_MODEL='/old/judge',
               VALIDITY_RZERO_REWARD_BORROW_GPUS='1', TERRA_REPLAY_RATIO='0.1',
               SOLVER_NEGATIVE_ONLY='1', SOLVER_DYNAMIC_VOTE='1', SOLVER_TOKEN_MASKING='1',
               RZERO_INITIAL_QUESTIONER='/old/q', RZERO_FIRST_ROUND='6', RZERO_NUM_ROUNDS='10',
               RZERO_RUN_ROOT='/old/run', OCTO_FROZEN_JUDGE_MODEL='/sft/judge',
               QUESTIONER_LOAD_CHECKPOINT='/old/resume', SOLVER_TRAIN_FILES='old@train',
               SOLVER_DATASET_READY='1', SOLVER_GENERATE_SAMPLES='2500',
               VLLM_SERVER_N='9', VLLM_PORT='42521', VLLM_DP_MASTER_PORT='42521',
               WANDB_MODE='disabled', WANDB_DISABLED='true', WANDB_RUN_ID='old',
               RZERO_RAY_TMPDIR='/tmp/ray-job', RZERO_SOLVER_VLLM_PORT_BASE='12000',
               VLLM_PORT_BASE='25654', QUESTION_EVAL_TIMEOUT_SECONDS='43200')
    env.pop('OCTO_BASE_RZERO_NAME', None)
    return scripts / 'run_octothinker_base.sh', env


@pytest.mark.parametrize('resume', [False, True])
def test_clean_baseline_environment_and_entry(tmp_path, resume):
    entry, env = setup(tmp_path)
    if resume:
        state = tmp_path / 'storage/rzero_runs' / NAME / 'state/run_state.json'
        state.parent.mkdir(parents=True)
        state.write_text('{"original":"unchanged"}')
    result = subprocess.run(['bash', str(entry)] + (['--resume'] if resume else []),
                            env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    values = dict(line.split('=', 1) for line in result.stdout.splitlines() if '=' in line)
    assert values['BASE_MODEL'] == '/cache/original-octo-base'
    assert values['VALIDITY_RZERO_ENABLED'] == '0'
    assert values['VALIDITY_RZERO_MODEL_FAMILY'] == 'octothinker'
    assert values['RZERO_NUM_ROUNDS'] == '5' and values['RZERO_FIRST_ROUND'] == '1'
    assert values['SOLVER_GENERATE_SAMPLES'] == '2000'
    assert values['QUESTIONER_MAX_STEPS'] == '5' and values['SOLVER_MAX_STEPS'] == '15'
    assert values['QUESTIONER_MAX_RESPONSE_LENGTH'] == values['SOLVER_MAX_RESPONSE_LENGTH'] == '4096'
    assert values['QUESTION_GPU_IDS'] == '0,1,2,3'
    assert values['QUESTIONER_TRAIN_GPU_IDS'] == '0,1' and values['VLLM_GPU_IDS'] == '2,3'
    for key in ['SOLVER_NEGATIVE_ONLY', 'SOLVER_DYNAMIC_VOTE', 'SOLVER_TOKEN_MASKING', 'SOLVER_EVAL_DUAL']:
        assert values[key] == '0'
    for key in ['VALIDITY_RZERO_INITIAL_SOLVER', 'VALIDITY_RZERO_SEMANTIC_MODEL',
                'VALIDITY_RZERO_REWARD_BORROW_GPUS', 'TERRA_REPLAY_RATIO', 'RZERO_INITIAL_QUESTIONER',
                'RZERO_RUN_ROOT', 'OCTO_FROZEN_JUDGE_MODEL', 'QUESTIONER_LOAD_CHECKPOINT',
                'SOLVER_TRAIN_FILES', 'SOLVER_DATASET_READY', 'WANDB_RUN_ID', 'WANDB_DISABLED',
                'VLLM_PORT', 'VLLM_DP_MASTER_PORT']:
        assert key not in values
    assert values['VLLM_SERVER_N'] == '10'
    assert values['WANDB_MODE'] == 'online'
    assert json.loads(values['QUESTIONER_LOGGER']) == json.loads(values['SOLVER_LOGGER']) == ['console', 'wandb']
    for key in ['RZERO_RAY_TMPDIR', 'RZERO_SOLVER_VLLM_PORT_BASE', 'VLLM_PORT_BASE', 'QUESTION_EVAL_TIMEOUT_SECONDS']:
        assert values[key] == env[key]
    args = f'ARGS:--no-eval --rounds 5 {"--resume " if resume else ""}/cache/original-octo-base {NAME}'
    assert args in result.stdout
    if resume:
        assert state.read_text() == '{"original":"unchanged"}'


@pytest.mark.parametrize('case', ['existing_run', 'existing_model', 'missing_resume', 'bad_flag'])
def test_refuse_unsafe_or_invalid_launch(tmp_path, case):
    entry, env = setup(tmp_path)
    args = []
    if case == 'existing_run':
        (tmp_path / 'storage/rzero_runs' / NAME).mkdir(parents=True)
    elif case == 'existing_model':
        (tmp_path / 'storage/models' / f'{NAME}_solver_v1').mkdir(parents=True)
    elif case == 'missing_resume':
        args = ['--resume']
    else:
        args = ['--rounds', '10']
    result = subprocess.run(['bash', str(entry), *args], env=env, capture_output=True, text=True)
    assert result.returncode == 2
    assert 'ARGS:' not in result.stdout
