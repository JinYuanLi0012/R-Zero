"""Evaluate N checkpoint paths sequentially with a local Qwen3 judge and a score summary."""

import argparse
import csv
from datetime import datetime
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys

DATASETS = ['math', 'gsm8k', 'amc', 'minerva', 'olympiad', 'aime2024', 'aime2025']
JUDGE = {'backend': 'local', 'model': 'Qwen/Qwen3-32B', 'revision': None,
         'prompt_version': 'math-recheck-local-v1', 'enable_thinking': False,
         'temperature': 0.0, 'max_tokens': 32}
COLUMNS = ['id', 'name', 'status'] + DATASETS + ['ave', 'model', 'results_file']


def plan(paths):
    models = []
    seen = set()
    for number, supplied in enumerate(paths, 1):
        path = Path(supplied).expanduser().absolute()
        model = path if (path / 'config.json').is_file() else path / 'global_step_15/actor/huggingface'
        config = model / 'config.json'
        if not config.is_file() or not config.stat().st_size:
            raise ValueError(f'Missing merged checkpoint config: {config}')
        if not isinstance(json.loads(config.read_text()), dict):
            raise ValueError(f'Invalid checkpoint config: {config}')
        if model.resolve() in seen:
            raise ValueError(f'Duplicate model path: {model}')
        seen.add(model.resolve())
        name = model.parents[2].name if model.name == 'huggingface' and model.parent.name == 'actor' else model.name
        models.append(dict(id=number, name=name, model=str(model), status='pending',
                           results_file=f'{number:03d}/final_results.jsonl'))
    return models


def summarize(batch, manifest):
    columns = COLUMNS
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
                except (ValueError, KeyError, TypeError, AttributeError):
                    invalid = True
        status = item['status']
        if invalid:
            status = 'invalid_results'
        elif status == 'complete' and len(scores) != len(DATASETS):
            status = 'incomplete_results'
        mean = round(sum(scores.values()) / len(DATASETS), 2) if status == 'complete' else ''
        row = [item['id'], item['name'], status] + [scores.get(d, '') for d in DATASETS]
        table.append(row + [mean, item['model'], str(path)])
    # These two generated summary files are refreshed; original per-model results stay intact.
    with (batch / 'summary.csv').open('w', newline='') as output:
        writer = csv.writer(output)
        writer.writerow(columns)
        writer.writerows(table)
    with (batch / 'summary.md').open('w') as output:
        output.write('Scores are percentages. ave is an unweighted mean, not an official aggregate.\n\n')
        output.write('| ' + ' | '.join(columns[:11]) + ' |\n')
        output.write('| ' + ' | '.join(['---'] * 11) + ' |\n')
        for row in table:
            output.write('| ' + ' | '.join(str(value) for value in row[:11]) + ' |\n')
    return table


def copy_to_checkpoints(batch, manifest, table):
    """Publish only validated complete scores next to each exact checkpoint."""
    for item, row in zip(manifest['models'], table):
        if row[2] != 'complete':
            continue
        destination = Path(item['model']) / 'evaluations' / f'{batch.name}_{item["id"]:03d}'
        metadata_file = destination / 'evaluation.json'
        identity = {'batch_dir': str(batch.resolve()), 'model': item['model']}
        if destination.exists():
            if not metadata_file.is_file():
                raise FileExistsError(f'Refusing to overwrite an unrecognized result directory: {destination}')
            previous = json.loads(metadata_file.read_text())
            if any(previous.get(key) != value for key, value in identity.items()):
                raise FileExistsError(f'Refusing to overwrite results from another batch: {destination}')
        else:
            destination.mkdir(parents=True, exist_ok=False)
            metadata_file.write_text(json.dumps(dict(identity, status='copying'), indent=2) + '\n')
        source = batch / item['results_file']
        shutil.copyfile(source, destination / 'final_results.jsonl')
        with (destination / 'summary.csv').open('w', newline='') as output:
            writer = csv.writer(output)
            writer.writerow(COLUMNS)
            writer.writerow(row)
        with (destination / 'summary.md').open('w') as output:
            output.write('Scores are percentages. ave is an unweighted mean, not an official aggregate.\n\n')
            output.write('| ' + ' | '.join(COLUMNS[:11]) + ' |\n')
            output.write('| ' + ' | '.join(['---'] * 11) + ' |\n')
            output.write('| ' + ' | '.join(str(value) for value in row[:11]) + ' |\n')
        metadata = dict(identity, status='complete', judge=manifest['judge'],
                        source_results_file=str(source.resolve()),
                        source_log_dir=str((source.parent / 'logs').resolve()))
        if manifest.get('storage_path'):
            metadata['source_raw_results_dir'] = str(Path(manifest['storage_path']) / 'evaluation' /
                                                   item['model'].replace('/', '_'))
        metadata_file.write_text(json.dumps(metadata, indent=2) + '\n')
        item['checkpoint_results_dir'] = str(destination)


def save(batch, manifest):
    # Keep the central scores even if a checkpoint-side copy fails (e.g. permissions).
    (batch / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    table = summarize(batch, manifest)
    copy_to_checkpoints(batch, manifest, table)
    (batch / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return table


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('paths', nargs='*', help='Run directories or merged checkpoint directories')
    parser.add_argument('--storage-path', default=os.getenv('STORAGE_PATH'), help='Base evaluation output storage; independent of checkpoint location')
    parser.add_argument('--gpu-ids', default=os.getenv('CUDA_VISIBLE_DEVICES') or '0,1,2,3')
    parser.add_argument('--dry-run', action='store_true', help='Check all checkpoint configs; no GPU or output writes')
    parser.add_argument('--batch-dir', type=Path, help='New output directory (must not already exist)')
    parser.add_argument('--summary-only', type=Path, metavar='BATCH_DIR', help='Refresh and print an existing batch summary')
    parser.add_argument('--copy-to-checkpoints', action='store_true', help='With --summary-only, copy completed results beside checkpoints without GPU work')
    args = parser.parse_args()
    if args.summary_only:
        if args.paths or args.dry_run or args.batch_dir:
            parser.error('--summary-only cannot be combined with paths, --dry-run or --batch-dir')
        batch = args.summary_only.resolve()
        manifest = json.loads((batch / 'manifest.json').read_text())
        if args.copy_to_checkpoints:
            save(batch, manifest)
        else:
            summarize(batch, manifest)
        print((batch / 'summary.md').read_text())
        print(f'CSV: {batch / "summary.csv"}')
        return
    if args.copy_to_checkpoints:
        parser.error('--copy-to-checkpoints requires --summary-only')
    if not args.paths:
        parser.error('Provide one or more model paths')
    if not args.storage_path:
        parser.error('Set STORAGE_PATH or pass --storage-path')
    storage = Path(args.storage_path).expanduser().absolute()
    gpu_ids = args.gpu_ids.split(',')
    if not all(gpu_ids) or len(gpu_ids) != len(set(gpu_ids)):
        parser.error('--gpu-ids must be a nonempty list without duplicates')
    try:
        models = plan(args.paths)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    for item in models:
        print(f'OK {item["id"]}: {item["model"]}', flush=True)
    if args.dry_run:
        print(f'All {len(models)} configs found. Dry run only; weights/environment are not GPU-tested.')
        return
    root = Path(__file__).resolve().parents[1]
    batch = (args.batch_dir or storage / 'evaluation_batches' /
             ('math_qwen3_32b_' + datetime.now().strftime('%Y%m%d_%H%M%S_%f'))).absolute()
    batch.mkdir(parents=True, exist_ok=False)
    env = os.environ.copy()
    judge = dict(JUDGE, revision=env.get('RECHECK_LOCAL_REVISION') or None)
    env['STORAGE_PATH'] = str(storage)
    env.update(RECHECK_BACKEND='local', RECHECK_LOCAL_MODEL=JUDGE['model'],
               RECHECK_MAX_COMPLETION_TOKENS='32', RECHECK_CONCURRENCY='8',
               RECHECK_GPU_IDS=args.gpu_ids, RECHECK_TENSOR_PARALLEL_SIZE=str(len(gpu_ids)),
               EVAL_GPU_IDS=args.gpu_ids, EVAL_TENSOR_PARALLEL_SIZE='1',
               EVAL_MATH_ONLY='1', EVAL_TASKS=','.join(DATASETS))
    env.setdefault('RECHECK_LOCAL_TMP_ROOT', '/tmp')
    env.setdefault('RECHECK_STARTUP_TIMEOUT', '3600')
    # evaluate.bash invokes "python"; ensure it uses this activated interpreter.
    env['PATH'] = str(Path(sys.executable).parent) + os.pathsep + env.get('PATH', '')
    manifest = {'judge': judge, 'storage_path': str(storage), 'models': models}
    save(batch, manifest)
    print(f'BATCH_DIR={batch}', flush=True)
    print(f'Live summary: {batch / "summary.csv"}', flush=True)
    try:
        for item in models:
            output = batch / item['results_file']
            output.parent.mkdir(parents=True, exist_ok=True)
            env.update(EVAL_ARTIFACT_DIR=str(output.parent), EVAL_LOG_DIR=str(output.parent / 'logs'),
                       FINAL_RESULTS_FILE=str(output), EVAL_RUN_ID=f'model_{item["id"]}_{batch.name}')
            item['status'] = 'running'
            save(batch, manifest)
            print(f'START [{item["id"]}/{len(models)}] {item["name"]}', flush=True)
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
            result_row = next(row for row in table if row[0] == item['id'])
            if code or result_row[2] != 'complete':
                raise SystemExit(f'Stopped at model {item["id"]}; inspect {output.parent / "logs"}')
            print(f'DONE [{item["id"]}/{len(models)}] {item["name"]}; ave={result_row[10]}', flush=True)
            print(f'Checkpoint result copy: {item["checkpoint_results_dir"]}', flush=True)
    finally:
        save(batch, manifest)
        print((batch / 'summary.md').read_text(), flush=True)
        print(f'CSV: {batch / "summary.csv"}', flush=True)


if __name__ == '__main__':
    main()
