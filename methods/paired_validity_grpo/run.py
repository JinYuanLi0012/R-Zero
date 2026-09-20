#!/usr/bin/env python3
"""Isolated paired GRPO: read existing labels, train two independent base replicas."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SYSTEM = r'Please reason step by step, and put your final answer within \boxed{}.'


def read_rows(path):
    with path.open() as handle:
        return [json.loads(line) for line in handle if line.strip()]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
    temporary.replace(path)


def validate_pairs(original, repaired):
    if not original or len(original) != len(repaired):
        raise ValueError('empty or unequal arms')
    seen = set()
    shared = 0
    for left, right in zip(original, repaired):
        if left['id'] != right['id'] or left['id'] in seen:
            raise ValueError('misordered or duplicate pair IDs')
        seen.add(left['id'])
        for row in (left, right):
            if not isinstance(row['problem'], str) or not row['problem'].strip():
                raise ValueError('empty question')
            if not isinstance(row['answer'], str) or row['answer'].strip().upper() in ('', 'NONE', 'INVALID'):
                raise ValueError('unusable pseudo-label')
        if left['problem'] == right['problem']:
            if left['answer'] != right['answer'] or left['label_job_id'] != right['label_job_id'] or left['score'] != right['score']:
                raise ValueError('shared question has different labels')
            shared += 1
    if not shared or shared == len(original):
        raise ValueError('expected both shared and repaired questions')
    return {'pairs': len(original), 'shared': shared, 'changed': len(original) - shared}


def clean_environment(gpus, out, seed):
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(('VALIDITY_RZERO_', 'SOLVER_', 'TERRA_', 'RAY_'))}
    env.update(CUDA_VISIBLE_DEVICES=gpus, RAY_ADDRESS='local',
               PYTHONPATH=str(ROOT), PYTHONUNBUFFERED='1', PYTHONHASHSEED=str(seed),
               VLLM_DISABLE_COMPILE_CACHE='1', WANDB_MODE='disabled',
               PYTHONDONTWRITEBYTECODE='1')
    # Each subprocess starts its own local Ray runtime; never stop other jobs.
    return env


def resume_checkpoint(directory):
    root = directory / 'checkpoints'
    tracker = root / 'latest_global_step.txt'
    if not tracker.exists():
        if list(root.glob('global_step_*')):
            raise ValueError('partial checkpoint without committed tracker; use a fresh output directory')
        return None
    step = int(tracker.read_text().strip())
    checkpoint = root / f'global_step_{step}'
    if step not in (5, 10) or not (checkpoint / 'dataloader.pt').is_file():
        raise ValueError('invalid committed resume checkpoint')
    return checkpoint


def make_config(model, out, arm, args):
    from omegaconf import OmegaConf
    config = OmegaConf.load(HERE / 'train.yaml')
    config.data.update(train_files=str(out / 'data' / f'{arm}.parquet'),
                       val_files=str(out / 'data' / 'diagnostic.parquet'),
                       max_prompt_length=2048, max_response_length=4096,
                       rollout_batch_size=512, val_batch_size=64,
                       format_prompt=str(ROOT / 'examples/format_prompt/solver.jinja'),
                       filter_overlong_prompts=False, seed=args.seed)
    config.worker.actor.model.model_path = model
    config.worker.actor.micro_batch_size_per_device_for_update = 1
    config.worker.actor.micro_batch_size_per_device_for_experience = 1
    config.worker.rollout.seed = args.seed
    config.worker.reward.reward_function = str(ROOT / 'examples/reward_function/math.py') + ':compute_score'
    config.trainer.update(total_epochs=100, max_steps=10,
                         project_name='paired_validity_grpo', experiment_name=f'{out.name}_{arm}',
                         logger=['console'], nnodes=1, n_gpus_per_node=4,
                         val_before_train=False, val_freq=5, val_generations_to_log=0,
                         save_freq=5, save_limit=2,
                         save_checkpoint_path=str(out / arm / 'checkpoints'),
                         load_checkpoint_path=None)
    return config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--labels-dir', required=True, type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    parser.add_argument('--model', default='Qwen/Qwen3-4B-Base')
    parser.add_argument('--revision', default=None)
    parser.add_argument('--gpus', default=os.environ.get('CUDA_VISIBLE_DEVICES', '0,1,2,3'))
    parser.add_argument('--seed', default=1, type=int)
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--arm', choices=['both', 'original', 'repaired'], default='both')
    parser.add_argument('--resume', action='store_true', help='resume incomplete arm from latest saved step')
    args = parser.parse_args()
    sys.dont_write_bytecode = True
    os.environ['CUDA_VISIBLE_DEVICES'] = args.gpus
    devices = args.gpus.split(',')
    if len(devices) != 4 or len(set(devices)) != 4 or any(not d.strip() or d.strip() == '-1' for d in devices):
        parser.error('exactly four allocated GPUs required')
    labels, out = args.labels_dir.resolve(), args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    with (out / '.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        original, repaired = [read_rows(labels / f'{arm}_train.jsonl') for arm in ('original', 'repaired')]
        stats = validate_pairs(original, repaired)
        if len(original) < 512:
            raise ValueError('at least 512 pairs required for unchanged R-Zero rollout batch size')
        # Resolve a Hub model once, so both arms use one immutable snapshot path.
        if Path(args.model).is_dir():
            model = str(Path(args.model).resolve())
        else:
            from huggingface_hub import snapshot_download
            model = snapshot_download(args.model, revision=args.revision)
        env = clean_environment(args.gpus, out, args.seed)
        # Match tokenizer and prompt construction used by the existing training dataset.
        for key in list(os.environ):
            if key.startswith(('VALIDITY_RZERO_', 'SOLVER_', 'TERRA_')):
                del os.environ[key]
        sys.path.insert(0, str(ROOT))
        from verl.utils.tokenizer import get_tokenizer
        tokenizer = get_tokenizer(model, trust_remote_code=False)
        maximum = 0
        for row in original + repaired:
            messages = [{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': row['problem']}]
            prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True) if tokenizer.chat_template else 'system: ' + SYSTEM + '\nuser: ' + row['problem']
            length = len(tokenizer.encode(prompt, add_special_tokens=False))
            maximum = max(maximum, length)
            if length > 2048:
                raise ValueError(f'prompt {row["id"]} exceeds 2048 tokens; abort both arms without truncation')
        from omegaconf import OmegaConf
        from verl.trainer.config import PPOConfig
        configs = {arm: make_config(model, out, arm, args) for arm in ('original', 'repaired')}
        for config in configs.values():
            checked = OmegaConf.to_object(OmegaConf.merge(OmegaConf.structured(PPOConfig()), config))
            checked.deep_post_init()
        manifest = {'protocol': 'paired-validity-grpo-v1', **stats, 'model': model,
                    'seed': args.seed, 'max_prompt_tokens': maximum,
                    'source_hashes': {arm: sha(labels / f'{arm}_train.jsonl') for arm in configs},
                    'configurations': {arm: OmegaConf.to_container(c) for arm, c in configs.items()},
                    'code_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()}
        manifest_path = out / 'manifest.json'
        if manifest_path.exists() and json.loads(manifest_path.read_text()) != manifest:
            raise ValueError('inputs/config/code changed; use a new output directory')
        write_json(manifest_path, manifest)
        data_dir = out / 'data'
        data_dir.mkdir(exist_ok=True)
        from datasets import Dataset
        for arm, data in [('original', original), ('repaired', repaired)]:
            path = data_dir / f'{arm}.parquet'
            if not path.exists():
                Dataset.from_list(data).to_parquet(str(path))
        # The trainer requires a validation loader. Shared training rows are a
        # pipeline diagnostic only, never reported as held-out benchmark accuracy.
        diagnostic = [a for a, b in zip(original, repaired) if a['problem'] == b['problem']][:64]
        path = data_dir / 'diagnostic.parquet'
        if not path.exists():
            Dataset.from_list(diagnostic).to_parquet(str(path))
        print('[prepared]', json.dumps(stats), 'max_prompt_tokens=', maximum, flush=True)
        for arm, config in configs.items():
            directory = out / arm
            directory.mkdir(exist_ok=True)
            OmegaConf.save(config, directory / 'config.yaml')
        if args.prepare_only:
            return
        import torch
        if torch.cuda.device_count() != 4:
            raise ValueError('expected four visible CUDA GPUs')
        print('[GPUs]', [torch.cuda.get_device_name(i) for i in range(4)], flush=True)
        for arm in (('original', 'repaired') if args.arm == 'both' else (args.arm,)):
            directory = out / arm
            if (directory / 'completed.json').exists():
                print('[skip completed]', arm, flush=True)
                continue
            command = [sys.executable, '-m', 'verl.trainer.main', 'config=' + str(directory / 'config.yaml')]
            checkpoint = resume_checkpoint(directory)
            if (directory / 'started.json').exists() and not args.resume:
                raise ValueError(f'{arm} previously started; use --resume or a fresh output directory')
            if checkpoint:
                if not args.resume:
                    raise ValueError('checkpoints exist; explicit --resume required')
                command += ['trainer.load_checkpoint_path=' + str(checkpoint)]
            write_json(directory / 'started.json', {'command': command})
            print('[train]', arm, 'log=', directory / 'train.log', flush=True)
            with (directory / 'train.log').open('a') as log:
                subprocess.run(command, cwd=directory, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
            for step in (5, 10):
                actor = directory / 'checkpoints' / f'global_step_{step}' / 'actor'
                if not actor.is_dir():
                    raise RuntimeError(f'missing checkpoint {actor}')
                with (directory / 'merge.log').open('a') as log:
                    subprocess.run([sys.executable, str(ROOT / 'scripts/model_merger.py'), '--local_dir', str(actor)],
                                   cwd=directory, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
            write_json(directory / 'completed.json', {'steps': 10, 'model': model, 'merged_steps': [5, 10]})
            print('[complete]', arm, flush=True)


if __name__ == '__main__':
    main()
