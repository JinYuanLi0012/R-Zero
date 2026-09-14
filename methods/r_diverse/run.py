"""Five-round, four-GPU, standalone R-Diverse baseline launcher."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

import numpy as np

from methods.r_diverse.core import read_json, replay_rows, retained, write_json
from methods.r_diverse.inference import ROOT, run_workers, sam


METHOD = Path(__file__).resolve().parent


def clean_environment():
    # Research settings from earlier shell sessions must not affect this baseline.
    for key in list(os.environ):
        if key.startswith(('VALIDITY_', 'TERRA_', 'SEMANTIC_', 'RZERO_')):
            del os.environ[key]
    os.environ['VALIDITY_RZERO_ENABLED'] = '0'
    os.environ['PYTHONPATH'] = str(ROOT) + os.pathsep + os.environ.get('PYTHONPATH', '')
    os.environ['VLLM_DISABLE_COMPILE_CACHE'] = '1'
    os.environ['VLLM_WORKER_MULTIPROC_METHOD'] = 'spawn'


def resolve_model(name, local_only):
    if Path(name).is_dir():
        return str(Path(name).resolve())
    from huggingface_hub import snapshot_download
    return snapshot_download(name, local_files_only=local_only,
                             allow_patterns=['*.json', '*.safetensors', '*.model', '*.txt',
                                             '*.jinja', 'tokenizer.*', '*.py'])


def command(args, log_path, gpu_ids=None):
    env = os.environ.copy()
    if gpu_ids is not None:
        env['CUDA_VISIBLE_DEVICES'] = ','.join(gpu_ids)
    print('[r_diverse] ' + shlex.join(map(str, args)), flush=True)
    print('[r_diverse] log:', log_path, flush=True)
    with Path(log_path).open('w') as log:
        result = subprocess.run(list(map(str, args)), cwd=ROOT, env=env,
                                stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
        tail = Path(log_path).read_text(errors='replace')[-6000:]
        raise RuntimeError(f'Command exit={result.returncode}; log={log_path}\n{tail}')


def train(role, model, dataset, config, config_path, directory, memory_path, solver_model):
    base = directory / role
    base.mkdir(exist_ok=True)
    attempt = 1
    while (base / f'attempt_{attempt}').exists():
        attempt += 1
    output = base / f'attempt_{attempt}'
    output.mkdir()
    questioner = role == 'questioner'
    gpus = config['questioner_gpus'] if questioner else config['all_gpus']
    steps = 5 if questioner else 15
    args = [sys.executable, '-m', 'methods.r_diverse.train', f'config={METHOD / "train.yaml"}',
            f'data.train_files={dataset}', f'data.val_files={dataset}',
            f'data.format_prompt={METHOD / ("questioner.jinja" if questioner else "solver.jinja")}',
            f'data.rollout_batch_size={config["rollout_batch"]}', 'data.val_batch_size=1',
            f'data.seed={config["seed"]}', f'data.max_response_length={config["response_tokens"]}',
            f'worker.actor.model.model_path={model}', f'trainer.n_gpus_per_node={len(gpus)}',
            f'trainer.save_checkpoint_path={output}', f'trainer.max_steps={steps}',
            f'trainer.save_freq={steps}', 'trainer.save_limit=1', 'trainer.total_epochs=1000',
            'trainer.val_before_train=false', 'trainer.val_freq=-1',
            f'trainer.experiment_name={config["run_name"]}_{directory.name}_{role}',
            'trainer.project_name=r_diverse', f'trainer.logger={config["logger"]}',
            f'worker.rollout.n={4 if questioner else 5}', 'worker.rollout.tensor_parallel_size=2',
            f'worker.actor.global_batch_size={config["questioner_global_batch"] if questioner else 128}',
            f'worker.actor.micro_batch_size_per_device_for_update={2 if questioner else 1}',
            f'worker.actor.micro_batch_size_per_device_for_experience={8 if questioner else 1}',
            'worker.reward.num_cpus=1']
    if questioner:
        args += [f'worker.reward.reward_function={METHOD / "reward.py"}:compute_score',
                 f'worker.reward.reward_function_kwargs.config_path={config_path}',
                 f'worker.reward.reward_function_kwargs.solver_model={solver_model}',
                 f'worker.reward.reward_function_kwargs.memory_path={memory_path}',
                 f'worker.reward.reward_function_kwargs.round_dir={directory}']
    else:
        args += [f'worker.reward.reward_function={METHOD / "solver_reward.py"}:compute_score']
    command(args, output / 'train.log', gpus)
    actor = output / f'global_step_{steps}' / 'actor'
    command([sys.executable, 'scripts/model_merger.py', '--local_dir', actor], output / 'merge.log')
    model_path = actor / 'huggingface'
    if not (model_path / 'config.json').is_file():
        raise RuntimeError(f'Merged model not found: {model_path}')
    return str(model_path)


def prepare_dataset(directory, config, current, history, history_vectors):
    from datasets import Dataset
    vectors, records = sam([r['question'] for r in current], config, config['all_gpus'], directory / 'sam')
    annotated = [dict(row, sam_key=record['key']) for row, record in zip(current, records)]
    mixed = replay_rows(annotated, history, ratio=0.3, seed=config['seed'] + int(directory.name.split('_')[-1]))
    if len(mixed) < config['rollout_batch']:
        raise RuntimeError(f'Only {len(mixed)} rows after filtering/replay; need '
                           f'{config["rollout_batch"]}. Increase --questions-per-gpu for a new run.')
    dataset = directory / 'solver.parquet'
    Dataset.from_list([{'problem': r['question'], 'answer': r['answer'],
                       'score': r['score'], 'replay': r['replay']} for r in mixed]).to_parquet(str(dataset))
    write_json(directory / 'mixed_rows.json', mixed)
    write_json(directory / 'memory_rows.json', history + annotated)
    # Append only fresh retained Phase-B rows, never replay duplicates or Phase-A rewards.
    np.save(directory / 'memory.npy', np.concatenate([history_vectors, vectors])
            if len(history_vectors) else vectors)
    write_json(directory / 'dataset_summary.json', {
        'current_rows': len(current), 'historical_rows_before': len(history),
        'replay_rows': len(mixed) - len(current), 'total_rows': len(mixed),
        'actual_replay_ratio': (len(mixed) - len(current)) / len(mixed),
        'memory_rows_after': len(history) + len(current),
        'unique_current_questions': len({r['question'] for r in current}),
        'code_tags_ok': sum(r['code_tags_ok'] for r in records),
        'code_syntax_ok': sum(r['code_syntax_ok'] for r in records),
        'code_truncated': sum(r['code_truncated'] for r in records),
    })
    return str(dataset)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-name', default='qwen3_4b_r_diverse_minimal_v1')
    parser.add_argument('--output-dir')
    parser.add_argument('--base-model', default='Qwen/Qwen3-4B-Base')
    parser.add_argument('--coder-model', default='Qwen/Qwen2.5-Coder-7B')
    parser.add_argument('--embedding-model', default='jinaai/jina-code-embeddings-1.5b')
    parser.add_argument('--rounds', type=int, default=5)
    parser.add_argument('--gpu-ids', default='0,1,2,3')
    parser.add_argument('--questions-per-gpu', type=int, default=int(os.getenv('SOLVER_GENERATE_SAMPLES', '1000')))
    parser.add_argument('--rollout-batch', type=int, default=int(os.getenv('QUESTIONER_ROLLOUT_BATCH_SIZE', '512')))
    parser.add_argument('--questioner-global-batch', type=int, default=int(os.getenv('QUESTIONER_GLOBAL_BATCH_SIZE', '4')))
    parser.add_argument('--response-tokens', type=int, default=4096)
    parser.add_argument('--code-tokens', type=int, default=2048)
    parser.add_argument('--embedding-tokens', type=int, default=4096)
    parser.add_argument('--inference-context', type=int, default=8192)
    parser.add_argument('--inference-memory', type=float, default=0.8)
    parser.add_argument('--inference-batch', type=int, default=64)
    parser.add_argument('--embedding-batch', type=int, default=8)
    parser.add_argument('--seed', type=int, default=1)
    parser.add_argument('--logger', default='["console","wandb"]')
    parser.add_argument('--local-files-only', action='store_true')
    parser.add_argument('--resume', action='store_true', help='Skip completed stages; restart an incomplete training stage')
    args = parser.parse_args()
    config = vars(args).copy()
    config.pop('resume')
    gpu_ids = [g.strip() for g in args.gpu_ids.split(',')]
    if len(gpu_ids) != 4 or len(set(gpu_ids)) != 4 or any(not g.isdigit() for g in gpu_ids):
        parser.error('--gpu-ids must contain four distinct physical GPU indices')
    for field in ['rounds', 'questions_per_gpu', 'rollout_batch', 'questioner_global_batch',
                  'response_tokens', 'code_tokens', 'embedding_tokens', 'inference_batch', 'embedding_batch']:
        if config[field] <= 0:
            parser.error(f'{field} must be positive')
    if args.rollout_batch * 4 % args.questioner_global_batch or args.questioner_global_batch % 2:
        parser.error('Q global batch must be even and divide rollout_batch * 4')
    if args.rollout_batch * 5 % 128:
        parser.error('rollout_batch * 5 must be divisible by Solver global batch 128')
    if not 0 < args.inference_memory < 1:
        parser.error('--inference-memory must be in (0, 1)')
    storage = os.environ.get('STORAGE_PATH')
    if not args.output_dir and not storage:
        parser.error('Source env_rzero.sh or provide --output-dir')
    run_root = Path(args.output_dir or str(Path(storage) / 'rzero_runs' / args.run_name)).resolve()
    config.update(run_root=str(run_root), all_gpus=gpu_ids,
                  questioner_gpus=gpu_ids[:2], feedback_gpus=gpu_ids[2:])
    config['method_hash'] = hashlib.sha256(b''.join(p.name.encode() + p.read_bytes() for p in sorted(METHOD.iterdir())
                         if p.suffix in {'.py', '.yaml', '.jinja', '.txt', '.sh'})).hexdigest()
    config_path = run_root / 'config.json'
    request_path = run_root / 'requested_config.json'
    clean_environment()
    if request_path.exists():
        if not args.resume:
            parser.error(f'Run already exists: {run_root}. Use --resume or a different --run-name')
        if read_json(request_path) != config:
            parser.error('Resume configuration/code differs from requested_config.json; use a new run name')
        if config_path.exists():
            config = read_json(config_path)
    else:
        run_root.mkdir(parents=True, exist_ok=True)
        write_json(request_path, config)
    if not config_path.exists():
        # Freeze HF snapshots once. Resume reuses these local resolved paths.
        for key in ['base_model', 'coder_model', 'embedding_model']:
            config[key] = resolve_model(config[key], args.local_files_only)
        write_json(config_path, config)
        write_json(run_root / 'provenance.json', {
            'upstream': 'Chengsong-Huang/R-Zero@5699329',
            'implementation_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
            'paper': 'arXiv:2602.13103v2', 'sam_python': os.getenv('RDIVERSE_SAM_PYTHON', sys.executable),
        })
    from datasets import Dataset
    dummy = run_root / 'questioner.parquet'
    if not dummy.exists():
        # Original fixed prompt ignores these placeholder fields; no seed question data.
        Dataset.from_list([{'problem': '', 'answer': ''} for _ in range(config['rollout_batch'])]).to_parquet(str(dummy))
    empty_memory = run_root / 'empty_memory.npy'
    if not empty_memory.exists():
        np.save(empty_memory, np.empty((0, 1536), dtype=np.float32))
    questioner = solver = config['base_model']
    memory_path = empty_memory
    history = []
    for number in range(1, args.rounds + 1):
        directory = run_root / f'round_{number}'
        directory.mkdir(exist_ok=True)
        state_path = directory / 'state.json'
        state = read_json(state_path) if state_path.exists() else {}
        print(f'[r_diverse] round {number}/{args.rounds}; completed stages={list(state)}', flush=True)
        if 'questioner' not in state:
            state['questioner'] = train('questioner', questioner, dummy, config, config_path,
                                         directory, memory_path, solver)
            write_json(state_path, state)
        questioner = state['questioner']
        if 'generated' not in state:
            rows = run_workers('generate', [{} for _ in range(config['questions_per_gpu'] * 4)],
                               questioner, gpu_ids, config, directory / 'generate', seed=args.seed + number * 100)
            path = directory / 'generated.json'
            write_json(path, rows)
            state['generated'] = str(path)
            write_json(state_path, state)
        if 'labeled' not in state:
            generated = read_json(state['generated'])
            usable = [dict(row, source_round=number, source_id=f"r{number}-{row['id']}")
                      for row in generated if row['question'] and row['answer']]
            rows = run_workers('solve', usable, solver, gpu_ids, config, directory / 'label',
                               phase='label', seed=args.seed + number * 100)
            path = directory / 'labeled.json'
            write_json(path, rows)
            state['labeled'] = str(path)
            write_json(state_path, state)
        if 'dataset' not in state:
            current = [r for r in read_json(state['labeled']) if retained(r)]
            if not current:
                raise RuntimeError('No retained current questions after original R-Zero filtering')
            state['dataset'] = prepare_dataset(directory, config, current, history,
                                                np.load(memory_path, allow_pickle=False))
            write_json(state_path, state)
        if 'solver' not in state:
            state['solver'] = train('solver', solver, state['dataset'], config, config_path,
                                     directory, memory_path, solver)
            write_json(state_path, state)
        solver = state['solver']
        memory_path = directory / 'memory.npy'
        history = read_json(directory / 'memory_rows.json')
        write_json(run_root / 'latest.json', {'round': number, 'questioner': questioner,
                                            'solver': solver, 'memory': str(memory_path)})
        print(f'[r_diverse] completed round {number}: solver={solver}', flush=True)
    print(f'[r_diverse] finished; checkpoints and datasets: {run_root}', flush=True)


if __name__ == '__main__':
    main()
