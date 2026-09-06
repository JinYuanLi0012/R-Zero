"""Own a Qwen3 vLLM server for one recheck run, then release its GPUs.

Runs only after solver generation. No OpenAI credentials are loaded or required.
"""

import argparse
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
import uuid

import requests

try:
    from evaluation.local_judge import DEFAULT_MODEL
except ModuleNotFoundError:
    from local_judge import DEFAULT_MODEL

ROOT = Path(__file__).resolve().parents[1]
DATASETS = "math,gsm8k,amc,minerva,olympiad,aime2024,aime2025"


def stop_owned_process(process):
    """Only signal the private process group we created, including vLLM workers."""
    if process is None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=15)
    except subprocess.TimeoutExpired:
        pass
    # The group leader may have exited while a worker is still alive.
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait()


def wait_ready(process, base, key, alias, timeout):
    deadline = time.monotonic() + timeout
    with requests.Session() as session:
        session.trust_env = False
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError("Local vLLM exited during startup; inspect the server log")
            try:
                response = session.get(base + "/models", headers={"Authorization": "Bearer " + key},
                                       timeout=2, allow_redirects=False)
                if response.status_code == 200:
                    if any(item.get("id") == alias for item in response.json().get("data", [])):
                        return
            except (requests.RequestException, ValueError, TypeError, AttributeError):
                pass
            time.sleep(1)
    raise TimeoutError("Local vLLM startup timed out; inspect the server log")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--model_name", help="Solver path used by evaluation/generate.py")
    group.add_argument("--models_file", help="One solver path per line; reuse saved base results")
    parser.add_argument("--output_file", default=os.getenv("FINAL_RESULTS_FILE", "final_results_local_qwen3.jsonl"))
    parser.add_argument("--datasets", default=os.getenv("EVAL_TASKS", DATASETS))
    parser.add_argument("--dry_run", action="store_true", help="Validate inputs and print plan without starting GPU processes")
    args = parser.parse_args()
    storage = os.getenv("STORAGE_PATH")
    if not storage:
        parser.error("STORAGE_PATH is required")
    datasets = args.datasets.split(",")
    if any(dataset not in DATASETS.split(",") for dataset in datasets):
        parser.error("--datasets must contain supported math evaluation names")
    models = [args.model_name] if args.model_name else [
        line.strip() for line in Path(args.models_file).read_text().splitlines() if line.strip()
    ]
    if not models:
        parser.error("No solver models specified")
    for model in models:
        for dataset in datasets:
            result = Path(storage) / "evaluation" / model.replace("/", "_") / f"results_{dataset}.json"
            if not result.is_file():
                raise FileNotFoundError(f"Generate base results first: {result}")
            rows = json.loads(result.read_text())
            if not isinstance(rows, list) or len(rows) < 2:
                raise ValueError(f"Expected nonempty base results plus summary: {result}")

    env = os.environ.copy()
    # Discard stale API judge settings; only the explicitly named LOCAL settings
    # can choose a model/server in this workflow.
    env["RECHECK_BACKEND"] = "local"
    env["RECHECK_LOCAL_MODEL"] = os.getenv("RECHECK_LOCAL_MODEL", DEFAULT_MODEL)
    env.setdefault("RECHECK_CONCURRENCY", "8")
    env.setdefault("RECHECK_MAX_COMPLETION_TOKENS", "32")
    env["FINAL_RESULTS_FILE"] = str(Path(args.output_file).resolve())
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    gpu_ids = os.getenv("RECHECK_GPU_IDS") or os.getenv("CUDA_VISIBLE_DEVICES") or os.getenv("EVAL_GPU_IDS") or "0,1,2,3"
    tp = int(os.getenv("RECHECK_TENSOR_PARALLEL_SIZE", str(len(gpu_ids.split(",")))))
    if tp < 1 or tp > len(gpu_ids.split(",")):
        parser.error("RECHECK_TENSOR_PARALLEL_SIZE must fit RECHECK_GPU_IDS")
    env["CUDA_VISIBLE_DEVICES"] = gpu_ids
    # Model-specific metadata remains stable across per-run aliases/ports.
    env["RECHECK_LOCAL_SERVED_MODEL"] = "rzero-recheck-" + uuid.uuid4().hex
    env["RECHECK_LOCAL_API_KEY"] = uuid.uuid4().hex
    env.pop("OPENAI_API_KEY", None)
    env.pop("OPENAI_BASE_URL", None)
    env.pop("VLLM_PORT", None)  # Avoid inheriting a training worker's internal port.
    if args.model_name:
        client = [sys.executable, str(ROOT / "evaluation/results_recheck.py"),
                  "--model_name", args.model_name, "--datasets", args.datasets]
    else:
        client = [sys.executable, str(ROOT / "evaluation/recheck_resume.py"),
                  "--models_file", str(Path(args.models_file).resolve()),
                  "--output_file", env["FINAL_RESULTS_FILE"], "--datasets", args.datasets]
    print(f"Local judge: {env['RECHECK_LOCAL_MODEL']}; BF16; GPUs={gpu_ids}; TP={tp}; thinking=False", flush=True)
    print(f"Solvers={len(models)}; datasets={args.datasets}; output={env['FINAL_RESULTS_FILE']}", flush=True)
    if args.dry_run:
        print("Dry run: no server, GPU inference, or API requests started.")
        return

    Path(env["FINAL_RESULTS_FILE"]).parent.mkdir(parents=True, exist_ok=True)
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    env["RECHECK_LOCAL_BASE_URL"] = f"http://127.0.0.1:{port}/v1"
    server_command = [os.getenv("RECHECK_LOCAL_PYTHON", sys.executable),
                      "-m", "vllm.entrypoints.openai.api_server",
                      "--model", env["RECHECK_LOCAL_MODEL"],
                      "--served-model-name", env["RECHECK_LOCAL_SERVED_MODEL"],
                      "--host", "127.0.0.1", "--port", str(port),
                      "--api-key", env["RECHECK_LOCAL_API_KEY"],
                      "--dtype", "bfloat16", "--tensor-parallel-size", str(tp),
                      "--distributed-executor-backend", "mp",
                      "--max-model-len", os.getenv("RECHECK_MAX_MODEL_LEN", "8192"),
                      "--gpu-memory-utilization", os.getenv("RECHECK_GPU_MEMORY_UTILIZATION", "0.85"),
                      "--max-num-seqs", os.getenv("RECHECK_MAX_NUM_SEQS", "16"),
                      "--generation-config", "vllm"]
    if env.get("RECHECK_LOCAL_REVISION"):
        server_command += ["--revision", env["RECHECK_LOCAL_REVISION"]]
    log_dir = Path(os.getenv("EVAL_LOG_DIR", "logs"))
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"local_judge_{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.log"
    print(f"Local vLLM log: {log_path.resolve()}", flush=True)
    server = worker = None
    previous_handler = signal.getsignal(signal.SIGTERM)

    def interrupted(signum, frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, interrupted)
    try:
        with log_path.open("x") as log:
            server = subprocess.Popen(server_command, env=env, stdout=log, stderr=subprocess.STDOUT,
                                      start_new_session=True)
            wait_ready(server, env["RECHECK_LOCAL_BASE_URL"], env["RECHECK_LOCAL_API_KEY"],
                       env["RECHECK_LOCAL_SERVED_MODEL"], float(os.getenv("RECHECK_STARTUP_TIMEOUT", "900")))
            worker = subprocess.Popen(client, env=env, start_new_session=True)
            code = worker.wait()
            if code:
                raise subprocess.CalledProcessError(code, client)
    finally:
        # Do not let a repeated Ctrl-C/TERM interrupt GPU cleanup.
        old_int = signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        try:
            stop_owned_process(worker)
            stop_owned_process(server)
        finally:
            signal.signal(signal.SIGINT, old_int)
            signal.signal(signal.SIGTERM, previous_handler)


if __name__ == "__main__":
    main()
