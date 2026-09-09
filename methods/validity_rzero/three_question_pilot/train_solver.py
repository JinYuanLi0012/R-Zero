"""Train S3 on the existing three-question Phase B data using production settings."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

from methods.validity_rzero.prepare_solver_dataset import (
    build_mixed_rows, passes_rzero_filter, require_full_training_batch,
    _atomic_json, _write_jsonl,
)
from methods.validity_rzero.three_question_pilot.core import resolve_model

REPO = Path(__file__).resolve().parents[3]
STORAGE = Path('/engrfs/project/jiaxinh/jinyuan/R-zero-storage')
NAME = 'novelty_k8_q4_s3_three_questions_v1_solver_v4'
TERRA = 'jinyuan222/rzero-validity-rl-terra-v1-clean-v1'


def training_env(parent, storage, artifact):
    # Match scripts/main.sh's formal Solver overrides, not solver_train.sh defaults.
    env = {k: v for k, v in parent.items() if not k.startswith(
        ('SOLVER_', 'VALIDITY_RZERO_', 'TERRA_REPLAY_'))}
    env.update({
        'STORAGE_PATH': str(storage), 'QUESTION_GPU_IDS': '0,1,2,3',
        'VALIDITY_RZERO_ENABLED': '1', 'VALIDITY_RZERO_ARTIFACT_DIR': str(artifact),
        'SOLVER_DATASET_READY': '1', 'SOLVER_PREPARE_ONLY': '0',
        'SOLVER_MAX_STEPS': '15', 'SOLVER_MERGE_STEP': '15',
        'SOLVER_SAVE_FREQ': '1', 'SOLVER_SAVE_LIMIT': '1',
        'SOLVER_KEEP_LATEST_RESUME_STATE_ONLY': 'false',
        'SOLVER_MAX_RESPONSE_LENGTH': '4096', 'SOLVER_TOTAL_EPOCHS': '100',
        'SOLVER_ROLLOUT_BATCH_SIZE': '512', 'SOLVER_VAL_FREQ': '4',
        'SOLVER_SKIP_MERGE': '0', 'SOLVER_SKIP_FINAL_EVAL': '1',
    })
    return env


def read_retained(directory):
    phase = [json.loads(line) for line in
             (directory / 'round_4_phase_b.jsonl').read_text().splitlines() if line.strip()]
    retained = json.loads((directory / 'round_4.json').read_text())
    selected = [row for row in phase if passes_rzero_filter(row, .3, .8)]
    def keyed(rows):
        result = {row['sample_id']: (row['question'], row['answer'], row['score']) for row in rows}
        if len(result) != len(rows):
            raise ValueError('Duplicate sample IDs')
        return result
    if keyed(selected) != keyed(retained):
        raise ValueError('Retained data disagrees with the production Phase B filter')
    require_full_training_batch(len(retained), 512)
    return retained


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=STORAGE / 'rzero_runs/novelty_k8_q4_s3_three_questions_v1/datasets')
    parser.add_argument('--storage-path', type=Path, default=STORAGE)
    parser.add_argument('--solver', type=Path, default=STORAGE / 'models/qwen3_4b_validity_rzero_semantic_novelty_gate_k8_4gpu_v1_solver_v3')
    parser.add_argument('--experiment-name', default=NAME)
    parser.add_argument('--dry-run', action='store_true', help='Check local input and print settings; no upload or GPU use')
    parser.add_argument('--prepare-only', action='store_true', help='Mix and upload data without starting training')
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]+', args.experiment_name):
        parser.error('experiment-name must contain only letters, digits, underscores or hyphens')
    name = args.experiment_name
    rows = read_retained(args.data_dir)
    artifact = args.storage_path / 'rzero_runs' / name
    output = args.storage_path / 'models' / name
    env = training_env(os.environ, args.storage_path, artifact)
    namespace = env.get('HUGGINGFACENAME', 'jinyuan222')
    env['HUGGINGFACENAME'] = namespace
    identity = {
        'dataset_id': f'{namespace}/{name}', 'config_name': name,
        'input_sha256': {f: hashlib.sha256((args.data_dir / f).read_bytes()).hexdigest()
                         for f in ('round_4.json', 'round_4_phase_b.jsonl')},
        'terra_dataset': TERRA, 'terra_config': 'default', 'replay_seed': 1,
        'requested_replay_ratio': .1,
    }
    print(json.dumps({'rzero_rows': len(rows), 'solver': str(args.solver),
                      'model_output': str(output), **identity,
                      'training_overrides': {k: v for k, v in env.items()
                                             if k.startswith('SOLVER_')}}, indent=2), flush=True)
    if args.dry_run:
        return
    solver, model_info = resolve_model(args.solver, 15)
    if output.exists():
        raise FileExistsError(f'{output} already exists; refusing to overwrite or restart training')
    artifact.mkdir(parents=True, exist_ok=True)
    # Serialize launch/preparation on Linux, including the full training subprocess.
    import fcntl
    with (artifact / 'train.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        receipt = artifact / 'dataset_receipt.json'
        if receipt.exists():
            old = json.loads(receipt.read_text())
            if any(old.get(k) != v for k, v in identity.items()):
                raise ValueError('Existing dataset receipt differs; use a new experiment name')
        else:
            from datasets import Dataset, DatasetDict, load_dataset
            from huggingface_hub import login
            token = env.get('HF_TOKEN') or env.get('HUGGING_FACE_HUB_TOKEN')
            if not token and (REPO / 'tokens.json').is_file():
                token = json.loads((REPO / 'tokens.json').read_text()).get('huggingface')
            if token:
                login(token=token)
            terra = load_dataset(TERRA, 'default', split='train')
            mixed, stats = build_mixed_rows(rows, terra, .3, .8, .1, 1)
            require_full_training_batch(len(mixed), 512)
            _write_jsonl(artifact / 'solver_train_mixed.jsonl', mixed)
            DatasetDict({'train': Dataset.from_list(mixed)}).push_to_hub(
                identity['dataset_id'], private=True, config_name=name)
            _atomic_json(receipt, {**identity, **stats})
            print(json.dumps(stats, indent=2), flush=True)
        if args.prepare_only:
            return
        if output.exists():
            raise FileExistsError(output)
        _atomic_json(artifact / 'training_launch.json', {
            'solver': solver, 'model_info': model_info, **identity,
            'training_overrides': {k: v for k, v in env.items() if k.startswith('SOLVER_')},
            'git_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip(),
        })
        subprocess.run(['bash', 'scripts/solver_train.sh', solver, 'unused-dataset-ready', name],
                       cwd=REPO, env=env, check=True)


if __name__ == '__main__':
    main()
