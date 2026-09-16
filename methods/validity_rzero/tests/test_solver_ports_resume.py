import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time

import pytest

from vllm_service_init.solver_ports import check_available, port_plan

ROOT = Path(__file__).resolve().parents[3]


def test_port_blocks_follow_physical_gpu_not_pool_index():
    assert port_plan(['2', '3'], 25654) == [(25654, 12512, 12640), (25655, 12768, 12896)]
    assert port_plan(['0', '1'], 25656) == [(25656, 12000, 12128), (25657, 12256, 12384)]
    for ids, http, base in [(['2', '2'], 25000, 12000), (['x'], 25000, 12000),
                            (['2'], 12512, 12000), (['3'], 25000, 65000)]:
        with pytest.raises(ValueError):
            port_plan(ids, http, base)


def test_preflight_detects_owned_internal_port_without_killing_owner():
    with socket.socket() as owner:
        owner.bind(('127.0.0.1', 0))
        occupied = owner.getsockname()[1]
        # Put the owned socket at the beginning of the checked block.
        with pytest.raises(RuntimeError, match=str(occupied)):
            check_available([(occupied, occupied, occupied + 128)])
        assert owner.getsockname()[1] == occupied


@pytest.mark.parametrize('invocation', ['initial', 'handoff'])
def test_real_start_shell_overrides_inherited_vllm_ports(tmp_path, invocation):
    service = tmp_path / 'vllm_service_init'
    service.mkdir()
    shutil.copy(ROOT / 'vllm_service_init/start.sh', service)
    # Stub bind checks only: verify actual shell environment reaching children.
    (service / 'solver_ports.py').write_text('print("25654 12512 12640\\n25655 12768 12896")\n')
    (service / 'start_vllm_server.py').write_text(
        'import os,json\nprint(json.dumps({k:os.environ[k] for k in '
        '["CUDA_VISIBLE_DEVICES","VLLM_PORT","VLLM_DP_MASTER_PORT"]}),flush=True)\n')
    bin_dir = tmp_path / 'bin'
    bin_dir.mkdir()
    (bin_dir / 'setsid').write_text('#!/bin/sh\nexec "$@"\n')
    (bin_dir / 'setsid').chmod(0o755)
    logs = tmp_path / 'logs'
    env = dict(os.environ, PATH=str(bin_dir) + os.pathsep + os.defpath,
               PYTHON_EXECUTABLE=sys.executable, VLLM_GPU_IDS='2,3', VLLM_PORT_BASE='25654',
               VLLM_PORT='42521', VLLM_DP_MASTER_PORT='42521', VLLM_LOG_DIR=str(logs),
               QUESTIONER_VLLM_PID_FILE=str(tmp_path / 'pids'))
    if invocation == 'initial':
        subprocess.run(['bash', str(service / 'start.sh'), 'model', 'run'], cwd=tmp_path,
                       env=env, check=True, capture_output=True)
    else:
        from unittest.mock import patch
        from methods.validity_rzero.service_handoff import SolverServiceConfig, start_solver_services
        config = SolverServiceConfig(tmp_path, 'model', 'run', tmp_path / 'pids', ('2', '3'), 25654)
        with patch.dict(os.environ, env, clear=True), patch(
                'methods.validity_rzero.service_handoff.wait_services_healthy'):
            start_solver_services(config)
    paths = [logs / f'vllm_solver_run_gpu{gpu}_port{port}.log' for gpu, port in [(2, 25654), (3, 25655)]]
    deadline = time.monotonic() + 5
    while not all(path.exists() and path.stat().st_size for path in paths) and time.monotonic() < deadline:
        time.sleep(.02)
    rows = [json.loads(path.read_text()) for path in paths]
    assert [row['VLLM_PORT'] for row in rows] == ['12512', '12768']
    assert [row['VLLM_DP_MASTER_PORT'] for row in rows] == ['12640', '12896']
    assert [row['CUDA_VISIBLE_DEVICES'] for row in rows] == ['2', '3']
    assert len((tmp_path / 'pids').read_text().splitlines()) == 2


@pytest.mark.parametrize('resume,existing,success', [(False, False, True), (False, True, False),
                                                   (True, False, False), (True, True, True)])
def test_sftjudge_entry_preserves_fresh_guard_and_forwards_resume(tmp_path, resume, existing, success):
    method = tmp_path / 'method'
    method.mkdir()
    shutil.copy(ROOT / 'methods/validity_rzero/run_octothinker_sftjudge.sh', method)
    (method / 'run_octothinker.sh').write_text('printf "ARGS:%s ROUNDS:%s NAME:%s\\n" "$*" "$OCTO_NUM_ROUNDS" "$OCTO_MODEL_ABBR"\n')
    root = tmp_path / 'custom-run'
    if existing:
        (root / 'state').mkdir(parents=True)
        (root / 'state/run_state.json').write_text('{"original":"untouched"}')
    env = dict(os.environ, STORAGE_PATH=str(tmp_path), OCTO_FROZEN_JUDGE_MODEL='/fixed/judge',
               OCTO_MODEL_ABBR='same-experiment', RZERO_RUN_ROOT=str(root))
    command = ['bash', str(method / 'run_octothinker_sftjudge.sh')] + (['--resume'] if resume else [])
    result = subprocess.run(command, env=env, capture_output=True, text=True)
    assert (result.returncode == 0) == success, result.stderr
    if success:
        assert f'ARGS:{"--resume" if resume else ""} ROUNDS:5 NAME:same-experiment' in result.stdout
    if existing:
        assert (root / 'state/run_state.json').read_text() == '{"original":"untouched"}'
