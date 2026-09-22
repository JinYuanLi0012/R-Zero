"""Generation + ordinary majority vote only. Never train, upload or delete inputs."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from question_evaluate.run_workers import run_workers
from .worker import read_rows, write_rows
from .protocol import QUESTIONER_CHAT, QUESTIONER_SAMPLING, SOLVER_SYSTEM, SOLVER_SAMPLING

ROOT = Path(__file__).resolve().parents[2]


def model_pairs(storage, experiment, rounds):
    models = Path(storage) / 'models'
    return [dict(round=r,
        questioner=str(models / f'{experiment}_questioner_v{r}/global_step_5/actor/huggingface'),
        solver='Qwen/Qwen3-4B-Base' if r == 1 else str(models / f'{experiment}_solver_v{r-1}/global_step_15/actor/huggingface'))
        for r in rounds]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--storage', type=Path, default=os.environ.get('STORAGE_PATH', '/engrfs/project/jiaxinh/jinyuan/R-zero-storage'))
    parser.add_argument('--experiment', default='qwen3_4b_rzero_8k_5round')
    parser.add_argument('--rounds', default='1,2,3,4,5')
    parser.add_argument('--per-round', type=int, default=200)
    parser.add_argument('--gpu-ids', default='0,1,2,3')
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--timeout-seconds', type=int, default=14400)
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--plan-only', action='store_true')
    args = parser.parse_args()
    rounds = [int(r) for r in args.rounds.split(',')]
    gpu_ids = args.gpu_ids.split(',')
    if not rounds or len(set(rounds)) != len(rounds) or any(r < 1 for r in rounds):
        parser.error('rounds must be distinct positive integers')
    if not all(gpu_ids) or len(set(gpu_ids)) != len(gpu_ids) or args.per_round < len(gpu_ids) or args.timeout_seconds <= 0:
        parser.error('Need distinct GPUs, positive timeout, and at least one sample per GPU')
    pairs = model_pairs(args.storage, args.experiment, rounds)
    counts = [args.per_round // len(gpu_ids) + (i < args.per_round % len(gpu_ids)) for i in range(len(gpu_ids))]
    config = dict(protocol='ordinary_rzero_phase_b_raw_audit_v1', experiment=args.experiment,
        pairs=pairs, per_round=args.per_round, gpu_ids=gpu_ids, shard_counts=counts,
        seeds=list(range(len(gpu_ids))), sampling_unit='raw_generation', deduplication='none',
        questioner_chat=QUESTIONER_CHAT, questioner_sampling=QUESTIONER_SAMPLING,
        solver_system=SOLVER_SYSTEM, solver_sampling=SOLVER_SAMPLING,
        score_denominator='nonempty_extracted_solver_answers',
        filtering='annotate_only_keep_every_row', pairing='Q_r_with_S_r_minus_1',
        code_sha256={name: hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
                     for name in ['protocol.py', 'worker.py', 'run.py']})
    print(json.dumps(config, indent=2, ensure_ascii=False), flush=True)
    if args.plan_only:
        return
    # Model checks are read-only and run before output creation or GPU launch.
    for path in sorted({p[k] for p in pairs for k in ['questioner', 'solver']} - {'Qwen/Qwen3-4B-Base'}):
        subprocess.run([sys.executable, str(ROOT / 'scripts/validate_hf_checkpoint.py'), path], check=True)
    output = args.output_dir.resolve()
    manifest = output / 'manifest.json'
    if manifest.exists():
        if not args.resume:
            raise SystemExit('Output exists; use --resume with the same settings or a new directory')
        if json.loads(manifest.read_text()) != config:
            raise SystemExit('Audit configuration changed; use a new output directory')
    else:
        if output.exists() and any(output.iterdir()):
            raise SystemExit('Nonempty output directory without a manifest')
        output.mkdir(parents=True, exist_ok=True)
        temporary = output / 'manifest.json.tmp'
        temporary.write_text(json.dumps(config, indent=2, ensure_ascii=False) + '\n')
        os.replace(temporary, manifest)
    # Only affects this subprocess; no inherited experiment can enable gating.
    os.environ.update(VALIDITY_RZERO_ENABLED='0', RZERO_NOVELTY_ONLY='0')
    os.environ.pop('VALIDITY_RZERO_MODEL_FAMILY', None)
    os.environ['PYTHONPATH'] = str(ROOT) + os.pathsep + os.environ.get('PYTHONPATH', '')
    all_rows, summaries = [], []
    for pair in pairs:
        r = pair['round']
        directory = output / f'round_{r}'
        for stage in ['generate', 'vote']:
            commands, devices = [], []
            for shard, (gpu, count) in enumerate(zip(gpu_ids, counts)):
                target = directory / f'{stage}_shard_{shard}.jsonl'
                if target.exists():
                    saved = read_rows(target)
                    if len(saved) != count or any(row['round'] != r or row['shard'] != shard for row in saved):
                        raise ValueError(f'Incomplete or mismatched shard: {target}')
                    continue
                command = [sys.executable, '-m', 'methods.rzero_raw_audit.worker', '--stage', stage,
                    '--model', pair['questioner' if stage == 'generate' else 'solver'],
                    '--round', str(r), '--shard', str(shard), '--count', str(count), '--output', str(target)]
                if stage == 'vote':
                    command += ['--input', str(directory / f'generate_shard_{shard}.jsonl')]
                commands.append(command)
                devices.append(gpu)
            if commands:
                print(f'[audit] round={r} stage={stage} shards={len(commands)}', flush=True)
                status = run_workers(commands, devices, args.timeout_seconds)
                if status:
                    raise SystemExit(status)
        rows = [row for shard in range(len(gpu_ids)) for row in read_rows(directory / f'vote_shard_{shard}.jsonl')]
        if len(rows) != args.per_round or len({row['id'] for row in rows}) != args.per_round:
            raise ValueError('Round row count or ID uniqueness violation')
        write_rows(output / f'round_{r}.jsonl', rows)
        all_rows.extend(rows)
        summary = dict(round=r, rows=len(rows), questioner_parse_ok=sum(row['questioner_parse_ok'] for row in rows),
            majority_available=sum(row['majority_answer'] is not None for row in rows),
            would_pass_original_filter=sum(row['would_pass_original_filter'] for row in rows))
        summaries.append(summary)
        print(f'[audit] round complete: {json.dumps(summary)}', flush=True)
    write_rows(output / 'all_rounds.jsonl', all_rows)
    (output / 'summary.json').write_text(json.dumps(summaries, indent=2) + '\n')
    print(f'[audit] complete: {len(all_rows)} raw rows; {output}', flush=True)


if __name__ == '__main__':
    main()
