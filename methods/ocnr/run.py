"""Four-GPU, isolated OCNR orchestration. All large artifacts stay in STORAGE_PATH."""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

from methods.ocnr.core import curate_and_split, write_json

ROOT = Path(__file__).resolve().parents[2]
PYTHON = sys.executable


def stop(process):
    if process is None:
        return
    # The child owns a new process group, including its vLLM/Ray descendants.
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=15)
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait()


def launch(command, env, log):
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a") as handle:
        handle.write("\nCOMMAND " + repr(command) + "\n")
        handle.flush()
        return subprocess.Popen(command, cwd=ROOT, env=env, stdout=handle,
                                stderr=subprocess.STDOUT, start_new_session=True)


def execute(command, env, log):
    print(f"[OCNR] {log}: {command[0:4]}", flush=True)
    process = launch(command, env, log)
    try:
        code = process.wait()
        if code:
            raise RuntimeError(f"command failed ({code}); inspect {log}")
    finally:
        stop(process)


def parallel(commands, env, log_dir, name, gpus):
    children = []
    try:
        for i, (command, gpu) in enumerate(zip(commands, gpus)):
            log = log_dir / f"{name}-{i}.log"
            children.append((launch(command, {**env, "CUDA_VISIBLE_DEVICES": str(gpu)}, log), log))
        while children:
            for process, log in list(children):
                code = process.poll()
                if code is not None:
                    if code:
                        raise RuntimeError(f"worker failed ({code}); inspect {log}")
                    stop(process)
                    children.remove((process, log))
            if children:
                time.sleep(1)
    finally:
        for process, _ in children:
            stop(process)


def port_free(port):
    with socket.socket() as sock:
        if sock.connect_ex(("127.0.0.1", port)) == 0:
            raise RuntimeError(f"port {port} is occupied; choose another port_base in config")


def merged_model_ready(hf):
    """Trainer saves HF config/tokenizer BEFORE model_merger writes weights."""
    if not (hf / "config.json").is_file():
        return False
    for name in ["model.safetensors.index.json", "pytorch_model.bin.index.json"]:
        index = hf / name
        if index.exists():
            shards = set(json.loads(index.read_text())["weight_map"].values())
            return bool(shards) and all((hf / shard).is_file() and (hf / shard).stat().st_size > 0 for shard in shards)
    return any((hf / name).is_file() and (hf / name).stat().st_size > 0
               for name in ["model.safetensors", "pytorch_model.bin"])


@contextlib.contextmanager
def questioner_services(solver, previous_sd, config, env, directory):
    import urllib.request
    gpus = config["gpu_ids"]
    port = config["port_base"]
    run_id = f"ocnr-{os.getpid()}-{time.time_ns()}"
    # First round can use both feedback replicas; subsequent rounds dedicate
    # GPU3 to HF hidden states and GPU2 to the same Solver's vLLM generation.
    feedback_gpus = gpus[2:3] if previous_sd else gpus[2:]
    services = []
    try:
        for i, gpu in enumerate(feedback_gpus):
            port_free(port + i)
            command = [PYTHON, "vllm_service_init/start_vllm_server.py", "--model_path", solver,
                       "--port", str(port + i), "--run_id", run_id]
            process = launch(command, {**env, "CUDA_VISIBLE_DEVICES": str(gpu)}, directory / f"feedback-{i}.log")
            services.append((process, port + i))
        if previous_sd:
            port_free(port + 2)
            command = [PYTHON, "-m", "methods.ocnr.detector", "serve", "--model", solver,
                       "--config", str(directory.parent.parent / "config.json"), "--state", str(previous_sd),
                       "--port", str(port + 2), "--run-id", run_id]
            process = launch(command, {**env, "CUDA_VISIBLE_DEVICES": str(gpus[3])}, directory / "novelty-service.log")
            services.append((process, port + 2))
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        for process, service_port in services:
            deadline = time.monotonic() + 900
            while True:
                if process.poll() is not None:
                    raise RuntimeError(f"service {service_port} exited; inspect {directory}")
                try:
                    with opener.open(f"http://127.0.0.1:{service_port}/health", timeout=2) as response:
                        health = json.load(response)
                    if health.get("run_id") == run_id and health.get("pid") == process.pid:
                        break
                except (OSError, ValueError):
                    pass
                if time.monotonic() >= deadline:
                    raise RuntimeError(f"service startup timeout on port {service_port}")
                time.sleep(2)
        yield len(feedback_gpus)
    finally:
        for process, _ in services:
            stop(process)


def train(role, model, output, data, config, env, log, resume, services=0, novelty=False):
    from scripts.find_resume_checkpoint import find_complete_checkpoint
    questioner = role == "questioner"
    gpus = config["gpu_ids"][:2] if questioner else config["gpu_ids"]
    steps = config[f"{role}_steps"]
    hf = output / f"global_step_{steps}" / "actor" / "huggingface"
    if (output / "TRAIN_DONE.json").exists():
        if not merged_model_ready(hf):
            raise RuntimeError(f"completed training is missing merged model: {hf}")
        return str(hf)
    output.mkdir(parents=True, exist_ok=True)
    checkpoint = find_complete_checkpoint(output, len(gpus)) if resume else None
    if checkpoint is None or int(checkpoint.name.split("_")[-1]) < steps:
        command = [PYTHON, "-m", "verl.trainer.main", "config=examples/config.yaml",
                   f"worker.actor.model.model_path={model}", f"trainer.experiment_name={output.name}",
                   f"trainer.save_checkpoint_path={output}", f"trainer.logger={json.dumps(config['logger'])}",
                   "trainer.total_epochs=1000", f"trainer.max_steps={steps}",
                   f"trainer.n_gpus_per_node={len(gpus)}", "trainer.save_freq=5", "trainer.save_limit=3",
                   "trainer.val_before_train=false", "trainer.val_freq=-1",
                   f"data.train_files={data}", f"data.val_files={data}",
                   f"data.rollout_batch_size={config['rollout_batch_size']}", "data.val_batch_size=32",
                   f"data.seed={config['seed']}", "data.max_prompt_length=2048",
                   # Keep every declared seen row in the training dataset. Long
                   # prompts use the inherited right truncation, not post-split deletion.
                   "data.filter_overlong_prompts=false",
                   f"data.max_response_length={config['max_response_length']}",
                   f"data.format_prompt=./examples/format_prompt/{role}.jinja",
                   f"worker.actor.global_batch_size={config[f'{role}_global_batch_size']}",
                   f"worker.rollout.n={config[f'{role}_rollouts']}",
                   f"worker.actor.optim.lr={config['learning_rate']}",
                   f"worker.actor.optim.weight_decay={config['weight_decay']}",
                   f"algorithm.kl_coef={config['kl_coefficient']}",
                   f"worker.actor.micro_batch_size_per_device_for_update={2 if questioner else 1}",
                   f"worker.actor.micro_batch_size_per_device_for_experience={8 if questioner else 1}"]
        if questioner:
            command.extend([
                "worker.reward.reward_function=./methods/ocnr/reward.py:compute_score",
                f"worker.reward.reward_function_kwargs.num_services={services}",
                f"worker.reward.reward_function_kwargs.port_base={config['port_base']}",
                f"worker.reward.reward_function_kwargs.novelty_port={config['port_base'] + 2}",
                f"worker.reward.reward_function_kwargs.novelty_coefficient={config['novelty_coefficient'] if novelty else 0.0}",
                f"worker.reward.reward_function_kwargs.uncertainty_scale={config['uncertainty_scale']}"])
        if checkpoint:
            command.append(f"trainer.load_checkpoint_path={checkpoint}")
        execute(command, {**env, "CUDA_VISIBLE_DEVICES": ",".join(map(str, gpus))}, log)
    # Without our completion marker, always merge again, including after an
    # interrupted merge. A config-only HF directory is NOT a merged checkpoint.
    execute([PYTHON, "scripts/model_merger.py", "--local_dir", str(hf.parent)], env, log)
    if not merged_model_ready(hf):
        raise RuntimeError(f"model merger did not produce {hf}")
    write_json(output / "TRAIN_DONE.json", {"model": str(hf), "steps": steps})
    return str(hf)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "methods/ocnr/config.json")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    if len(config["gpu_ids"]) != 4 or len(set(config["gpu_ids"])) != 4:
        raise ValueError("this minimal runner needs exactly four distinct GPUs")
    if config["votes"] != 10 or config["overgeneration_factor"] != 2:
        raise ValueError("this baseline implements paper K=10 and 2x over-generation")
    if config["max_response_length"] != 4096:
        raise ValueError("the shared baseline generators use the paper's 4096-token response limit")
    if not 0 < config["tau"] or not 0 < config["ema_rate"] <= 1:
        raise ValueError("positive tau and EMA rate in (0,1] are required")
    for key in ["rounds", "sd_steps", "questioner_steps", "solver_steps", "rollout_batch_size",
                "embedding_batch_size", "embedding_max_length"]:
        if not isinstance(config[key], int) or config[key] < 1:
            raise ValueError(f"{key} must be a positive integer")
    total = config["baseline_candidates"] * config["overgeneration_factor"]
    if total % 4 or total < 4:
        raise ValueError("candidate count must be positive and divisible by four")
    if not config["run_name"] or config["run_name"] in {".", ".."} or Path(config["run_name"]).name != config["run_name"]:
        raise ValueError("run_name must be a single directory name")
    if "STORAGE_PATH" not in os.environ:
        raise ValueError("source env_rzero.sh first (STORAGE_PATH is required)")
    storage = Path(os.environ["STORAGE_PATH"]).resolve()
    root = storage / "rzero_runs" / config["run_name"]
    if root.exists() and not args.resume:
        raise FileExistsError(f"{root} exists; use --resume or a new config run_name")
    root.mkdir(parents=True, exist_ok=True)
    config_file = root / "config.json"
    if config_file.exists() and json.loads(config_file.read_text()) != config:
        raise ValueError("resume config differs from saved config; use a new run_name")
    write_json(config_file, config)
    env = {key: value for key, value in os.environ.items()
           if not key.startswith(("VALIDITY_RZERO_", "TERRA_REPLAY_", "OCNR_"))}
    env.update(VALIDITY_RZERO_ENABLED="0", RZERO_QUESTION_BOX_FILTER="legacy",
               VLLM_SERVER_N="10", VLLM_SERVER_MAX_TOKENS=str(config["max_response_length"]),
               VLLM_DISABLE_COMPILE_CACHE="1", PYTHONPATH=str(ROOT) + os.pathsep + env.get("PYTHONPATH", ""),
               PYTHONUNBUFFERED="1", QUESTION_GPU_IDS=",".join(map(str, config["gpu_ids"])),
               QUESTION_NUM_SHARDS="4")
    for name in ["generated_question", "temp_results", "models"]:
        (storage / name).mkdir(parents=True, exist_ok=True)
    # Constant Questioner prompts do not consume math12k question/answer content.
    from datasets import Dataset
    dummy = root / "questioner_inputs.parquet"
    if not dummy.exists():
        Dataset.from_list([{"problem": "Generate one new question.", "answer": ""}
                           for _ in range(config["rollout_batch_size"])]).to_parquet(str(dummy))
    from huggingface_hub import snapshot_download
    base = config["base_model"]
    if not Path(base).is_dir():
        base = snapshot_download(base)
    base = str(Path(base).resolve())
    manifest_path = root / "manifest.json"
    if manifest_path.exists():
        if json.loads(manifest_path.read_text())["resolved_base_model"] != base:
            raise ValueError("base snapshot changed since this run started")
    else:
        sources = list((ROOT / "methods/ocnr").glob("*.py")) + [ROOT / name for name in [
            "examples/config.yaml", "verl/utils/dataset.py", "verl/trainer/core_algos.py",
            "examples/reward_function/math.py", "question_generate/question_generate.py",
            "question_evaluate/evaluate.py", "vllm_service_init/start_vllm_server.py"]]
        hashes = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in sources}
        write_json(manifest_path, {"resolved_base_model": base, "method": "OCNR minimal paper reproduction",
                                  "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                                  "source_sha256": hashes, "actual_candidates_per_round": total})
    solver = questioner = base
    previous_sd = None
    for iteration in range(1, config["rounds"] + 1):
        directory = root / f"round_{iteration}"
        directory.mkdir(exist_ok=True)
        print(f"[OCNR] ROUND {iteration}: S={solver}; SD={previous_sd}", flush=True)
        name = f"{config['run_name']}_solver_v{iteration}"
        q_output = storage / "models" / f"{config['run_name']}_questioner_v{iteration}"
        q_env = {**env, "OCNR_REWARD_DIR": str(directory / "rewards")}
        if not (q_output / "TRAIN_DONE.json").exists():
            with questioner_services(solver, previous_sd, config, q_env, directory / "logs") as count:
                questioner = train("questioner", questioner, q_output, dummy, config, q_env,
                                   directory / "logs/questioner.log", args.resume, count, iteration > 1)
        else:
            questioner = train("questioner", questioner, q_output, dummy, config, q_env,
                               directory / "logs/questioner.log", args.resume)
        curated_path = directory / "curated.json"
        split_done = directory / "SPLIT_DONE.json"
        if not split_done.exists():
            # Regenerate unfinished data stages. Completed raw generation is saved
            # independently because the stock labeler deletes its temporary input.
            if not (directory / "GENERATION_DONE.json").exists():
                commands = [[PYTHON, "question_generate/question_generate.py", "--model", questioner,
                             "--num_samples", str(total // 4), "--suffix", str(i), "--save_name", name]
                            for i in range(4)]
                parallel(commands, env, directory / "logs", "generate", config["gpu_ids"])
                for i in range(4):
                    source = storage / "generated_question" / f"{name}_{i}.json"
                    rows = json.loads(source.read_text())
                    if len(rows) != total // 4:
                        raise ValueError("candidate shard size mismatch")
                    write_json(directory / f"generated-{i}.json", rows)
                write_json(directory / "GENERATION_DONE.json", {"count": total})
            for i in range(4):
                source = directory / f"generated-{i}.json"
                (storage / "generated_question" / f"{name}_{i}.json").write_bytes(source.read_bytes())
            commands = [[PYTHON, "question_evaluate/evaluate.py", "--model", solver,
                         "--num_samples", "10", "--suffix", str(i), "--save_name", name] for i in range(4)]
            parallel(commands, env, directory / "logs", "label", config["gpu_ids"])
            rows = []
            for i in range(4):
                source = storage / "generated_question" / f"{name}_{i}_results.json"
                rows.extend(json.loads(source.read_text()))
            write_json(directory / "labeled.json", rows)
            seen, unseen, metrics = curate_and_split(rows, votes=config["votes"],
                min_count=config["min_majority_count"], max_count=config["max_majority_count"],
                seed=config["seed"] + iteration)
            if len(seen) < config["rollout_batch_size"]:
                raise ValueError(f"only {len(seen)} seen rows; need {config['rollout_batch_size']} for a training batch")
            write_json(curated_path, seen + unseen)
            write_json(directory / "seen.json", seen)
            write_json(directory / "unseen.json", unseen)
            Dataset.from_list([{"problem": row["question"], "answer": row["answer"], "score": row["score"]}
                               for row in seen]).to_parquet(str(directory / "seen.parquet"))
            write_json(split_done, metrics)
        solver = train("solver", solver, storage / "models" / name, directory / "seen.parquet",
                       config, env, directory / "logs/solver.log", args.resume)
        sd = directory / "sd.json"
        if not sd.exists():
            command = [PYTHON, "-m", "methods.ocnr.detector", "fit", "--model", solver,
                       "--config", str(config_file), "--data", str(curated_path),
                       "--output", str(sd), "--round", str(iteration)]
            if previous_sd:
                command.extend(["--state", str(previous_sd)])
            execute(command, {**env, "CUDA_VISIBLE_DEVICES": str(config["gpu_ids"][3])}, directory / "logs/sd-fit.log")
        previous_sd = sd
        write_json(directory / "ROUND_DONE.json", {"questioner": questioner, "solver": solver, "sd": str(sd)})
        if config["evaluate_each_round"] and not (directory / "EVAL_DONE.json").exists():
            evaluation = directory / "evaluation"
            eval_env = {**env, "EVAL_GPU_IDS": env["QUESTION_GPU_IDS"], "EVAL_ARTIFACT_DIR": str(evaluation),
                        "EVAL_LOG_DIR": str(evaluation / "logs"), "EVAL_RUN_ID": name,
                        "FINAL_RESULTS_FILE": str(evaluation / "final_results.jsonl")}
            execute(["bash", "evaluation/evaluate.bash", solver], eval_env, directory / "logs/evaluation.log")
            write_json(directory / "EVAL_DONE.json", {"model": solver})
    write_json(root / "DONE.json", {"questioner": questioner, "solver": solver, "sd": str(previous_sd)})
    print(f"[OCNR] Finished. Final Solver: {solver}\nArtifacts: {root}", flush=True)


if __name__ == "__main__":
    # Turn scheduler cancellation into cleanup of subprocess groups.
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    main()
