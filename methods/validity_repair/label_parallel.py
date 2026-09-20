#!/usr/bin/env python3
"""One base-Solver replica per visible GPU; fixed disjoint data shards."""
import argparse
import fcntl
import os
from pathlib import Path
import subprocess
import sys
import time


def gpu_ids(value):
    ids = [v.strip() for v in value.split(',')]
    if not ids or any(not x or x == '-1' for x in ids) or len(set(ids)) != len(ids):
        raise ValueError('GPU list must contain unique, nonempty device IDs or UUIDs')
    return ids


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gpus', default=os.environ.get('LABEL_GPU_IDS', os.environ.get('CUDA_VISIBLE_DEVICES', '0,1,2,3')))
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--prepare-only', action='store_true')
    args, remaining = parser.parse_known_args()
    # Scheduling flags belong to this coordinator, not forwarded user arguments.
    for token in remaining:
        if token.split('=')[0] in ('--num-shards','--shard-index','--tensor-parallel-size','--finalize-only'):
            parser.error('do not override worker scheduling flags')
    devices = gpu_ids(args.gpus)
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    base = [sys.executable, str(Path(__file__).with_name('label_pairs.py')),
            '--output-dir', str(out), '--tensor-parallel-size', '1',
            '--num-shards', str(len(devices)), *remaining]
    children, handles = [], []
    with (out / '.parallel.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        subprocess.run([*base, '--prepare-only'], check=True)
        if args.prepare_only:
            print(f'[parallel] prepared {len(devices)} shards; no GPU model loaded', flush=True)
            return
        try:
            logdir = out / 'logs'
            logdir.mkdir(exist_ok=True)
            for rank, device in enumerate(devices):
                logfile = logdir / f'worker_{rank}.log'
                handle = logfile.open('a', buffering=1)
                handles.append(handle)
                env = dict(os.environ, CUDA_VISIBLE_DEVICES=device, PYTHONUNBUFFERED='1')
                child = subprocess.Popen([*base, '--shard-index', str(rank)], env=env, stdout=handle, stderr=subprocess.STDOUT)
                children.append(child)
                print(f'[parallel] worker={rank} GPU={device} pid={child.pid} log={logfile}', flush=True)
            active = set(range(len(children)))
            while active:
                for rank in list(active):
                    code = children[rank].poll()
                    if code is None:
                        continue
                    if code != 0:
                        raise RuntimeError(f'worker {rank} exited {code}; inspect {logdir / f"worker_{rank}.log"}')
                    print(f'[parallel] worker={rank} complete', flush=True)
                    active.remove(rank)
                if active:
                    time.sleep(2)
            subprocess.run([*base, '--finalize-only'], check=True)
        finally:
            for child in children:
                if child.poll() is None:
                    child.terminate()
            for child in children:
                try:
                    child.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait()
            for handle in handles:
                handle.close()


if __name__ == '__main__':
    main()
