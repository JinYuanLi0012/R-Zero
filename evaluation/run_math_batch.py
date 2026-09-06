"""Evaluate three experiment groups with a local Qwen3 judge and a live CSV summary."""

import argparse
import csv
from datetime import datetime
import json
import math
import os
from pathlib import Path
import subprocess
import sys

DATASETS = ['math', 'gsm8k', 'amc', 'minerva', 'olympiad', 'aime2024', 'aime2025']
GROUPS = [
    ('rzero_8k', 'qwen3_4b_rzero_8k_5round_solver_v'),
    ('novelty_k8', 'qwen3_4b_validity_rzero_semantic_novelty_gate_k8_4gpu_v1_solver_v'),
    ('validity_clean', 'qwen3_4b_validity_rzero_clean_formal_r10_initstep15_v1_solver_v'),
]
JUDGE = {'backend': 'local', 'model': 'Qwen/Qwen3-32B', 'revision': None,
         'prompt_version': 'math-recheck-local-v1', 'enable_thinking': False,
         'temperature': 0.0, 'max_tokens': 32}


def plan(storage):
    return [dict(group=group, round=v, model=str(storage / 'models' / (prefix + str(v)) /
                'global_step_15/actor/huggingface'), status='pending')
            for group, prefix in GROUPS for v in range(1, 6)]


def summarize(batch, manifest):
    columns = ['group', 'round', 'status'] + DATASETS + ['mean_7', 'model', 'results_file']
    table = []
    for item in manifest['models']:
        scores = {}
        path = batch / item['results_file']
        invalid = False
        if path.exists():
            for line in path.read_text().splitlines():
                try:
                    record = json.loads(line)
                    dataset = record['dataset']
                    score = float(record['score'])
                    if (record['model'] != item['model'] or record.get('recheck') != manifest['judge']
                            or dataset not in DATASETS or dataset in scores
                            or not math.isfinite(score) or not 0 <= score <= 100):
                        raise ValueError('Invalid or mixed result')
                    scores[dataset] = score
                except (ValueError, KeyError, TypeError):
                    invalid = True
        status = item['status']
        if invalid:
            status = 'invalid_results'
        elif status == 'complete' and len(scores) != len(DATASETS):
            status = 'incomplete_results'
        mean = round(sum(scores.values()) / len(DATASETS), 2) if status == 'complete' else ''
        row = [item['group'], item['round'], status] + [scores.get(d, '') for d in DATASETS]
        table.append(row + [mean, item['model'], str(path)])
    # These two generated summary files are refreshed; original per-model results stay intact.
    with (batch / 'summary.csv').open('w', newline='') as output:
        writer = csv.writer(output)
        writer.writerow(columns)
        writer.writerows(table)
    with (batch / 'summary.md').open('w') as output:
        output.write('Scores are percentages. mean_7 is an unweighted mean, not an official aggregate.\n\n')
        output.write('| ' + ' | '.join(columns[:11]) + ' |\n')
        output.write('| ' + ' | '.join(['---'] * 11) + ' |\n')
        for row in table:
            output.write('| ' + ' | '.join(str(value) for value in row[:11]) + ' |\n')
    return table


def save(batch, manifest):
    (batch / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return summarize(batch, manifest)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run', action='store_true', help='Check 15 checkpoint configs; no GPU or output writes')
    parser.add_argument('--batch-dir', type=Path, help='New output directory (must not already exist)')
    parser.add_argument('--summary-only', type=Path, metavar='BATCH_DIR', help='Refresh and print an existing batch summary')
    args = parser.parse_args()
    if args.summary_only:
        batch = args.summary_only.resolve()
        manifest = json.loads((batch / 'manifest.json').read_text())
        summarize(batch, manifest)
        print((batch / 'summary.md').read_text())
        print(f'CSV: {batch / "summary.csv"}')
        return
    if not os.getenv('STORAGE_PATH'):
        parser.error('Set STORAGE_PATH first')
    storage = Path(os.environ['STORAGE_PATH']).absolute()
    models = plan(storage)
    missing = []
    for item in models:
        config = Path(item['model']) / 'config.json'
        valid = config.is_file() and config.stat().st_size > 0
        print(f'{"OK" if valid else "MISSING"} {item["group"]} V{item["round"]}: {config}', flush=True)
        if not valid:
            missing.append(str(config))
    if missing:
        raise SystemExit('Missing checkpoint configs; no evaluation started.')
    if args.dry_run:
        print('All 15 configs found. Dry run only; weights/environment are not GPU-tested.')
        return
    root = Path(__file__).resolve().parents[1]
    batch = (args.batch_dir or storage / 'evaluation_batches' /
             ('three_groups_qwen3_32b_' + datetime.now().strftime('%Y%m%d_%H%M%S_%f'))).absolute()
    batch.mkdir(parents=True, exist_ok=False)
    for item in models:
        item['results_file'] = f'{item["group"]}/v{item["round"]}/final_results.jsonl'
    env = os.environ.copy()
    for key in ('RECHECK_LOCAL_REVISION', 'RECHECK_LOCAL_SERVED_MODEL'):
        env.pop(key, None)
    env.update(RECHECK_BACKEND='local', RECHECK_LOCAL_MODEL=JUDGE['model'],
               RECHECK_MAX_COMPLETION_TOKENS='32', RECHECK_CONCURRENCY='8',
               RECHECK_GPU_IDS='0,1,2,3', RECHECK_TENSOR_PARALLEL_SIZE='4',
               EVAL_GPU_IDS='0,1,2,3', EVAL_TENSOR_PARALLEL_SIZE='1',
               EVAL_MATH_ONLY='1', EVAL_TASKS=','.join(DATASETS))
    env.setdefault('RECHECK_LOCAL_TMP_ROOT', '/tmp')
    env.setdefault('RECHECK_STARTUP_TIMEOUT', '3600')
    # evaluate.bash invokes "python"; ensure it uses this activated interpreter.
    env['PATH'] = str(Path(sys.executable).parent) + os.pathsep + env.get('PATH', '')
    manifest = {'judge': JUDGE, 'models': models}
    save(batch, manifest)
    print(f'BATCH_DIR={batch}', flush=True)
    print(f'Live summary: {batch / "summary.csv"}', flush=True)
    try:
        for item in models:
            output = batch / item['results_file']
            output.parent.mkdir(parents=True, exist_ok=True)
            env.update(EVAL_ARTIFACT_DIR=str(output.parent), EVAL_LOG_DIR=str(output.parent / 'logs'),
                       FINAL_RESULTS_FILE=str(output), EVAL_RUN_ID=f'{item["group"]}_v{item["round"]}_{batch.name}')
            item['status'] = 'running'
            save(batch, manifest)
            print(f'START {item["group"]} V{item["round"]}', flush=True)
            try:
                code = subprocess.call(['bash', str(root / 'evaluation/evaluate.bash'), item['model']],
                                       cwd=root, env=env)
            except KeyboardInterrupt:
                item['status'] = 'interrupted'
                raise
            except OSError:
                item['status'] = 'failed'
                raise
            item['status'] = 'complete' if code == 0 else 'failed'
            table = save(batch, manifest)
            result_row = next(row for row in table if row[:2] == [item['group'], item['round']])
            if code or result_row[2] != 'complete':
                raise SystemExit(f'Stopped at {item["group"]} V{item["round"]}; inspect {output.parent / "logs"}')
            print(f'DONE {item["group"]} V{item["round"]}; mean_7={result_row[10]}', flush=True)
    finally:
        save(batch, manifest)
        print((batch / 'summary.md').read_text(), flush=True)
        print(f'CSV: {batch / "summary.csv"}', flush=True)


if __name__ == '__main__':
    main()
