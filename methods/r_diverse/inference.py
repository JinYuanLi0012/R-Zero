"""File-backed, process-isolated GPU inference. No shared R-Zero services."""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import numpy as np

from methods.r_diverse.core import read_json, write_json


ROOT = Path(__file__).resolve().parents[2]


def run_workers(mode, rows, model, gpu_ids, config, work, phase='reward', seed=1):
    if not rows:
        return []
    work = Path(work)
    work.mkdir(parents=True, exist_ok=True)
    processes, logs, outputs = [], [], []
    try:
        for shard, gpu in enumerate(gpu_ids):
            shard_rows = [dict(row, id=i) for i, row in enumerate(rows) if i % len(gpu_ids) == shard]
            if not shard_rows:
                continue
            inp, out = work / f'{mode}_{shard}.input.json', work / f'{mode}_{shard}.output.json'
            out.unlink(missing_ok=True)
            write_json(inp, {'mode': mode, 'rows': shard_rows, 'model': model,
                             'config': config, 'phase': phase, 'seed': seed + shard})
            env = os.environ.copy()
            for key in ['RANK', 'WORLD_SIZE', 'LOCAL_RANK', 'MASTER_ADDR', 'MASTER_PORT']:
                env.pop(key, None)
            env.update(CUDA_VISIBLE_DEVICES=str(gpu), VLLM_WORKER_MULTIPROC_METHOD='spawn',
                       PYTHONPATH=str(ROOT) + os.pathsep + env.get('PYTHONPATH', ''))
            log_path = work / f'{mode}_{shard}.log'
            log = log_path.open('w')
            logs.append(log)
            python = os.getenv('RDIVERSE_SAM_PYTHON', sys.executable) if mode in {'code', 'embed'} else sys.executable
            proc = subprocess.Popen([python, '-m', 'methods.r_diverse.gpu_worker',
                                     '--input', str(inp), '--output', str(out)],
                                    cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT,
                                    start_new_session=True)
            processes.append((proc, log_path))
            outputs.append(out)
        pending = list(processes)
        while pending:
            for proc, path in list(pending):
                status = proc.poll()
                if status is None:
                    continue
                if status:
                    tail = path.read_text(errors='replace')[-6000:]
                    raise RuntimeError(f'{mode} worker exit={status}; log={path}\n{tail}')
                pending.remove((proc, path))
            if pending:
                time.sleep(0.5)
        result = sorted([r for out in outputs for r in read_json(out)], key=lambda r: r['id'])
        if [r['id'] for r in result] != list(range(len(rows))):
            raise RuntimeError(f'{mode} worker row coverage/order mismatch')
        return result
    finally:
        # Kill only our process groups, including any vLLM children left after failure.
        for proc, _ in processes:
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        for proc, _ in processes:
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
        for log in logs:
            log.close()


def sam(questions, config, gpu_ids, work):
    """Exact-text computational cache; restore duplicate multiplicity on return."""
    template = Path(__file__).with_name('code_prompt.txt').read_text()
    context = {k: config[k] for k in ['coder_model', 'embedding_model', 'code_tokens', 'embedding_tokens']}
    context['prompt'] = template
    context['embedding_protocol'] = 'raw-code-last-token-l2-v1'
    prefix = json.dumps(context, sort_keys=True)
    cache = Path(config['run_root']) / 'sam_cache'
    cache.mkdir(parents=True, exist_ok=True)
    keys = [hashlib.sha256((prefix + '\n' + q).encode()).hexdigest() for q in questions]
    unique = dict(zip(keys, questions))
    missing = [{'key': key, 'question': q} for key, q in unique.items()
               if not (cache / f'{key}.json').is_file()]
    if missing:
        codes = run_workers('code', missing, config['coder_model'], gpu_ids, config, work)
        embedded = run_workers('embed', codes, config['embedding_model'], gpu_ids, config, work)
        for row in embedded:
            write_json(cache / f"{row['key']}.json", row)
    records = [read_json(cache / f'{key}.json') for key in keys]
    return np.asarray([row['embedding'] for row in records], dtype=np.float32), records
