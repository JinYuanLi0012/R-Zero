"""Real CPU process trees exercise cleanup; no GPU or vLLM imports."""

import json
import os
from pathlib import Path
import signal
import shutil
import subprocess
import sys
import time

import pytest

from question_evaluate import result_io


ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize('override,expected', [(None, 43200), ('17', 17)])
def test_real_shell_entry_timeout_override_gpu_mapping_and_quoted_arguments(tmp_path, override, expected):
    package = tmp_path / 'question_evaluate'
    package.mkdir()
    for name in ('evaluate.sh', 'run_workers.py'):
        shutil.copyfile(ROOT / 'question_evaluate' / name, package / name)
    (package / 'evaluate.py').write_text('''
import json, os, sys
from pathlib import Path
Path('args_' + os.environ['CUDA_VISIBLE_DEVICES'] + '.json').write_text(json.dumps(sys.argv[1:]))
''')
    env = dict(os.environ, PATH=str(Path(sys.executable).parent) + os.pathsep + os.defpath,
               PYTHONPATH=str(tmp_path), QUESTION_GPU_IDS='1,3', VALIDITY_RZERO_ENABLED='0')
    env.pop('QUESTION_EVAL_TIMEOUT_SECONDS', None)
    if override is not None:
        env['QUESTION_EVAL_TIMEOUT_SECONDS'] = override
    result = subprocess.run(['bash', 'question_evaluate/evaluate.sh', '/model with spaces', 'save with spaces'],
                            cwd=tmp_path, env=env, capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stdout + result.stderr
    assert f'question evaluation timeout: {expected}s' in result.stdout
    for index, gpu in enumerate(('1', '3')):
        assert json.loads((tmp_path / f'args_{gpu}.json').read_text()) == [
            '--model', '/model with spaces', '--suffix', str(index), '--save_name', 'save with spaces']


def live(pid):
    # A briefly unreaped orphan zombie owns no GPU and cannot execute work.
    result = subprocess.run(['ps', '-o', 'stat=', '-p', str(pid)], capture_output=True, text=True)
    return result.returncode == 0 and bool(result.stdout.strip()) and not result.stdout.strip().startswith('Z')


@pytest.mark.parametrize('mode,expected', [('success', 0), ('failure', 1), ('timeout', 124),
                                          ('term', 143), ('int', 130), ('spawn_error', 1)])
def test_real_worker_and_stubborn_grandchild_cleanup(tmp_path, mode, expected):
    worker_path = tmp_path / 'worker.py'
    worker_path.write_text('''
import json, os, signal, subprocess, sys, time
from pathlib import Path
output, mode = Path(sys.argv[1]), sys.argv[2]
child_ready = str(output) + '.child'
child = subprocess.Popen([sys.executable, '-c',
    "import os, signal, sys, time; from pathlib import Path; "
    "signal.signal(signal.SIGTERM, signal.SIG_IGN); "
    "Path(sys.argv[1]).write_text(str(os.getpid())); time.sleep(60)", child_ready])
while not Path(child_ready).exists():
    time.sleep(.01)
output.write_text(json.dumps({'parent': os.getpid(), 'child': child.pid, 'gpu': os.environ['CUDA_VISIBLE_DEVICES']}))
if mode == 'success':
    sys.exit(0)
if mode == 'failure':
    time.sleep(.25)
    sys.exit(7)
time.sleep(60)
''')
    driver = tmp_path / 'driver.py'
    driver.write_text('''
import sys
from question_evaluate.run_workers import run_workers
worker, root, mode = sys.argv[1:]
commands = [[sys.executable, worker, root + '/worker0.json', mode],
            [sys.executable, worker, root + '/worker1.json', 'success' if mode == 'success' else 'timeout']]
if mode == 'spawn_error':
    # A genuine exec failure after launching a previous worker.
    commands[1] = ['/does-not-exist/rzero-test-worker']
sys.exit(run_workers(commands, ['0', '1'], 1.5 if mode == 'timeout' else 15, grace_seconds=.2))
''')
    env = dict(os.environ, PYTHONPATH=str(ROOT))
    # Independent unrelated process must remain untouched by every cleanup.
    unrelated = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'], start_new_session=True)
    supervisor = subprocess.Popen([sys.executable, str(driver), str(worker_path), str(tmp_path), mode],
                                  env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                  start_new_session=True)
    records = []
    try:
        if mode in ('term', 'int'):
            deadline = time.monotonic() + 8
            while not all((tmp_path / f'worker{i}.json').exists() for i in range(2)):
                assert time.monotonic() < deadline
                time.sleep(.02)
            supervisor.send_signal(signal.SIGTERM if mode == 'term' else signal.SIGINT)
        output, _ = supervisor.communicate(timeout=12)
        assert supervisor.returncode == expected, output
        for path in tmp_path.glob('worker*.json'):
            records.append(json.loads(path.read_text()))
        if mode != 'spawn_error':
            assert len(records) == 2
            assert {row['gpu'] for row in records} == {'0', '1'}
        deadline = time.monotonic() + 3
        while any(live(row[key]) for row in records for key in ('parent', 'child')) and time.monotonic() < deadline:
            time.sleep(.05)
        assert not any(live(row[key]) for row in records for key in ('parent', 'child')), output
        assert unrelated.poll() is None
    finally:
        if supervisor.poll() is None:
            supervisor.kill()
            supervisor.wait()
        # Defensive test cleanup if an assertion failed before records loaded.
        for path in tmp_path.glob('worker*.json'):
            try:
                row = json.loads(path.read_text())
                os.killpg(row['parent'], signal.SIGKILL)
            except (ProcessLookupError, json.JSONDecodeError):
                pass
        unrelated.terminate()
        unrelated.wait()


def test_failed_output_commit_preserves_input_and_previous_result(tmp_path, monkeypatch):
    source, target = tmp_path / 'input.json', tmp_path / 'results.json'
    source.write_text('[{"question":"q"}]')
    target.write_text('["previous"]')
    def fail(*_args):
        raise OSError('write failed')
    monkeypatch.setattr(result_io.os, 'replace', fail)
    with pytest.raises(OSError, match='write failed'):
        result_io.save_results(['new'], target, source)
    assert source.exists() and json.loads(target.read_text()) == ['previous']
    assert not list(tmp_path.glob('.*.tmp-*'))


@pytest.mark.parametrize('rows', [[], [{'question': 'q', 'score': .5}]])
def test_successful_output_commit_then_removes_input(tmp_path, rows):
    source, target = tmp_path / 'input.json', tmp_path / 'results.json'
    source.write_text('[]')
    result_io.save_results(rows, target, source)
    assert json.loads(target.read_text()) == rows and not source.exists()
