"""Supervise annotation workers and their process groups without a watchdog."""

import argparse
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


def _signal_group(pgid, signum):
    try:
        os.killpg(pgid, signum)
    except ProcessLookupError:
        pass


def _group_exists(pgid):
    try:
        os.killpg(pgid, 0)
        return True
    except ProcessLookupError:
        return False


def cleanup_workers(workers, grace_seconds):
    # Signal the recorded group even when its Python leader already exited:
    # an EngineCore descendant may still hold GPU memory in that session.
    for worker in workers:
        _signal_group(worker.pid, signal.SIGTERM)
    deadline = time.monotonic() + grace_seconds
    while time.monotonic() < deadline:
        for worker in workers:
            worker.poll()  # reap exited direct children
        if not any(_group_exists(worker.pid) for worker in workers):
            break
        time.sleep(0.05)
    for worker in workers:
        _signal_group(worker.pid, signal.SIGKILL)
    for worker in workers:
        worker.wait(timeout=10)


def run_workers(commands, gpu_ids, timeout_seconds, grace_seconds=10):
    if timeout_seconds <= 0 or grace_seconds < 0 or len(commands) != len(gpu_ids) or not commands:
        raise ValueError("Positive timeout and one GPU per worker are required")
    workers = []
    interrupted = None

    def on_signal(signum, _frame):
        # Defer interruption until Popen's returned process is recorded. Do
        # not block signals around spawn: the children would inherit the mask.
        nonlocal interrupted
        interrupted = signum

    def interrupted_status():
        print(f"[question_eval] Signal {interrupted}; stopping owned worker process groups.", flush=True)
        return 128 + interrupted

    original_handlers = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM)}
    for sig in original_handlers:
        signal.signal(sig, on_signal)
    started = time.monotonic()
    print(f"question evaluation timeout: {timeout_seconds:g}s", flush=True)
    try:
        for index, (command, gpu_id) in enumerate(zip(commands, gpu_ids)):
            if interrupted is not None:
                return interrupted_status()
            env = os.environ.copy()
            env['CUDA_VISIBLE_DEVICES'] = gpu_id
            worker = subprocess.Popen(command, env=env, start_new_session=True)
            workers.append(worker)
            print(f"[question_eval] worker={index} gpu={gpu_id} pid={worker.pid} pgid={worker.pid}", flush=True)
        pending = set(range(len(workers)))
        while pending:
            if interrupted is not None:
                return interrupted_status()
            for index in list(pending):
                status = workers[index].poll()
                if status is not None:
                    print(f"[question_eval] worker={index} exit_code={status}", flush=True)
                    if status != 0:
                        return 1
                    pending.remove(index)
            if not pending:
                return 0
            if time.monotonic() - started >= timeout_seconds:
                print("[question_eval] Timeout reached; stopping owned worker process groups.", flush=True)
                return 124
            time.sleep(0.1)
    finally:
        # A second Ctrl-C must not interrupt the bounded cleanup itself.
        for sig in original_handlers:
            signal.signal(sig, signal.SIG_IGN)
        try:
            cleanup_workers(workers, grace_seconds)
        finally:
            for sig, handler in original_handlers.items():
                signal.signal(sig, handler)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', required=True)
    parser.add_argument('--save-name', required=True)
    args = parser.parse_args()
    gpu_ids = [value.strip() for value in os.getenv('QUESTION_GPU_IDS', '0,1,2,3').split(',')]
    if not all(gpu_ids) or len(set(gpu_ids)) != len(gpu_ids):
        parser.error('QUESTION_GPU_IDS must contain distinct nonempty GPU IDs')
    timeout_seconds = int(os.getenv('QUESTION_EVAL_TIMEOUT_SECONDS', '43200'))
    if timeout_seconds <= 0:
        parser.error('QUESTION_EVAL_TIMEOUT_SECONDS must be positive')
    root = Path(__file__).resolve().parents[1]
    os.environ['PYTHONPATH'] = str(root) + os.pathsep + os.environ.get('PYTHONPATH', '')
    commands = [[sys.executable, str(root / 'question_evaluate/evaluate.py'), '--model', args.model,
                 '--suffix', str(index), '--save_name', args.save_name] for index in range(len(gpu_ids))]
    return run_workers(commands, gpu_ids, timeout_seconds)


if __name__ == '__main__':
    sys.exit(main())
