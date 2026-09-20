"""Queue Octo checkpoints across GPUs and report HumanEval+/MBPP+ scores."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import csv
from datetime import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import queue
import re
import signal
import subprocess
import sys
import threading
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ENTRY = ROOT / "evaluation/octo_code_eval/run.py"
sys.path.insert(0, str(ROOT))
from scripts.validate_hf_checkpoint import validate_checkpoint

COLUMNS = ["model", "status", "humaneval_plus", "mbpp_plus", "gpu", "minutes", "output", "log", "error"]


def atomic_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_suffix(path.suffix + ".tmp")
    pending.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    pending.replace(path)


def resolve_model(value, base=False):
    path = Path(value).expanduser()
    if not path.exists():
        if base and not path.is_absolute() and not value.startswith(".") and len(value.split("/")) == 2:
            return value  # Explicit original Base HF ID.
        raise FileNotFoundError(f"Checkpoint does not exist: {value}")
    path = path.resolve()
    if (path / "config.json").is_file():
        validate_checkpoint(path)
        return str(path)
    for candidate in [path / "actor/huggingface", path / "huggingface"]:
        if (candidate / "config.json").is_file():
            validate_checkpoint(candidate)
            return str(candidate)
    steps = [p for p in path.glob("global_step_*") if p.is_dir() and re.fullmatch(r"global_step_\d+", p.name)]
    if steps:
        latest = max(steps, key=lambda p: int(p.name.rsplit("_", 1)[1]))
        # Never silently fall back to an older step when the latest is incomplete.
        return resolve_model(str(latest), base=base)
    raise ValueError(f"No merged Hugging Face checkpoint found under {path}")


def job_key(model, base):
    name = re.sub(r"[^A-Za-z0-9_.-]+", "_", model.rstrip("/").split("/")[-1])[:48] or "model"
    suffix = hashlib.sha256(json.dumps([model, base]).encode()).hexdigest()[:12]
    return name + "_" + suffix


def parse_scores(path):
    data = json.loads(path.read_text())
    rows = data["benchmarks"]
    if len(rows) != 2 or {r["dataset"] for r in rows} != {"humaneval", "mbpp"}:
        raise ValueError("Incomplete or unexpected benchmark summary")
    result = {}
    for row in rows:
        expected = {"humaneval": 164, "mbpp": 378}[row["dataset"]]
        value = float(row["pass@1_percent"])
        if row["count"] != expected or row["samples_per_task"] != 1 or not math.isfinite(value) or not 0 <= value <= 100:
            raise ValueError("Invalid score, sample count or benchmark size")
        result[row["dataset"] + "_plus"] = value
    return result


def table(rows):
    header = f"{'#':>3}  {'Status':<10} {'GPU':>4} {'HumanEval+':>11} {'MBPP+':>9} {'Min':>7}  Model"
    lines = [header, "-" * len(header)]
    for index, row in enumerate(rows, 1):
        scores = [f"{row[k]:.2f}" if row.get(k) is not None else "--" for k in ["humaneval_plus", "mbpp_plus"]]
        lines.append(f"{index:>3}  {row['status']:<10} {str(row.get('gpu', '--')):>4} {scores[0]:>11} {scores[1]:>9} "
                     f"{row.get('minutes', 0):>7.1f}  {row['model']}")
        if row.get("error"):
            lines.append(f"     {row['error']} | log: {row.get('log', '--')}")
    return "\n".join(lines)


def stop_process(process):
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        pass
    # Also clear orphaned GPU workers if the evaluator parent exited first.
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait()


def run_child(command, env, log, cancelled, timeout):
    with log.open("a") as stream:
        stream.write(f"\n=== {datetime.now().isoformat(timespec='seconds')} ===\n{json.dumps(command)}\n")
        stream.flush()
        process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT,
                                   start_new_session=True)
        started = time.monotonic()
        try:
            while True:
                if cancelled.is_set():
                    stop_process(process)
                    return 130
                if timeout and time.monotonic() - started > timeout:
                    stop_process(process)
                    return 124
                try:
                    return process.wait(timeout=0.5)
                except subprocess.TimeoutExpired:
                    pass
        finally:
            stop_process(process)


def execute(args, jobs, launch=run_child, cancelled=None):
    cancelled = cancelled or threading.Event()
    lock = threading.Lock()
    pending = queue.Queue()
    for job in jobs:
        if job["status"] == "QUEUED":
            pending.put(job)

    def save():
        atomic_json(args.output / "summary.json", {"updated": datetime.now().isoformat(), "models": jobs})
        path = args.output / "summary.csv"
        temp = path.with_suffix(".csv.tmp")
        with temp.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=COLUMNS, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(jobs)
        temp.replace(path)
        (args.output / "summary.txt").write_text(table(jobs) + "\n")

    def lane(gpu):
        cache = args.output / "cache" / re.sub(r"[^A-Za-z0-9_-]", "_", gpu)
        cache.mkdir(parents=True, exist_ok=True)
        while not cancelled.is_set():
            try:
                job = pending.get_nowait()
            except queue.Empty:
                return
            started = time.monotonic()
            with lock:
                job.update(status="RUNNING", gpu=gpu)
                save()
                print(f"[GPU {gpu}] START {job['model']}", flush=True)
            try:
                command = [sys.executable, "-u", str(ENTRY), "--model", job["model"],
                           "--output", job["output"], "--tools", str(args.tools),
                           "--datasets", "humaneval", "mbpp", "--tp", "1"]
                if job["base_model"]:
                    command.append("--base-model")
                for name in ["workers", "max_new_tokens", "max_model_len", "batch_size", "gpu_memory_utilization", "seed", "timeout"]:
                    command += ["--" + name.replace("_", "-"), str(getattr(args, name))]
                env = dict(os.environ, CUDA_VISIBLE_DEVICES=gpu, XDG_CACHE_HOME=str(cache),
                           TORCHINDUCTOR_CACHE_DIR=str(cache / "inductor"),
                           TRITON_CACHE_DIR=str(cache / "triton"), PYTHONUNBUFFERED="1")
                code = launch(command, env, Path(job["log"]), cancelled, args.job_timeout_hours * 3600)
                if code:
                    raise RuntimeError({124: "Job timeout", 130: "Interrupted"}.get(code, f"Evaluator exited with code {code}"))
                scores = parse_scores(Path(job["output"]) / "summary.json")
                result = dict(status="DONE", **scores)
            except Exception as exc:
                result = dict(status="CANCELLED" if cancelled.is_set() else "FAILED", error=str(exc))
            with lock:
                job.update(result, minutes=round((time.monotonic() - started) / 60, 2))
                save()
                print(f"[GPU {gpu}] {job['status']} {job['model']}"
                      + (f" | HumanEval+ {job['humaneval_plus']:.2f}% | MBPP+ {job['mbpp_plus']:.2f}%"
                         if job["status"] == "DONE" else f" | {job['error']}"), flush=True)
            pending.task_done()

    save()
    with ThreadPoolExecutor(max_workers=len(args.gpus)) as pool:
        futures = [pool.submit(lane, gpu) for gpu in args.gpus]
        for future in futures:
            future.result()
    for job in jobs:
        if job["status"] == "QUEUED":
            job["status"] = "CANCELLED"
    save()
    print("\n" + table(jobs), flush=True)
    print(f"\nSaved: {args.output / 'summary.csv'}", flush=True)
    return 130 if cancelled.is_set() else int(any(j["status"] != "DONE" for j in jobs))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("models", nargs="*", help="Merged checkpoints, global_step directories or Solver run directories")
    parser.add_argument("--models-file", type=Path, help="One checkpoint path per line; blank lines and # comments ignored")
    parser.add_argument("--base-model", action="append", default=[], help="Also evaluate this original Octo Base path/HF ID (repeatable)")
    parser.add_argument("--gpus", default="0,1,2,3", help="Comma-separated GPU IDs visible in the job allocation")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--tools", type=Path, default=os.environ.get("CODE_EVAL_TOOLS") or
                        (str(Path(os.environ["STORAGE_PATH"]) / "code_eval_tools") if os.environ.get("STORAGE_PATH") else None))
    parser.add_argument("--workers", type=int, default=4, help="CPU scorer workers per model")
    parser.add_argument("--max-new-tokens", type=int, default=4096)
    parser.add_argument("--max-model-len", type=int, default=16384)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.85)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--timeout", type=int, default=6)
    parser.add_argument("--job-timeout-hours", type=float, default=0, help="Per-model wall timeout; 0 means unlimited")
    args = parser.parse_args()
    args.gpus = [g.strip() for g in args.gpus.split(",")]
    if not all(re.fullmatch(r"\d+|GPU-[\w-]+|MIG-[\w./-]+", g) for g in args.gpus) or len(set(args.gpus)) != len(args.gpus):
        parser.error("--gpus must contain distinct GPU IDs")
    if any(getattr(args, k) <= 0 for k in ["workers", "max_new_tokens", "max_model_len", "batch_size", "timeout"]):
        parser.error("Token limits, batch size and workers must be positive")
    if args.max_model_len <= args.max_new_tokens or not 0 < args.gpu_memory_utilization < 1 or not math.isfinite(args.job_timeout_hours) or args.job_timeout_hours < 0:
        parser.error("Invalid context length, GPU utilization or timeout")
    values = list(args.models)
    if args.models_file:
        values += [line.strip() for line in args.models_file.read_text().splitlines() if line.strip() and not line.lstrip().startswith("#")]
    values += args.base_model
    if not values:
        parser.error("Supply checkpoint paths or --models-file")
    if not args.tools or not (args.tools / "environment.json").is_file():
        parser.error("Set STORAGE_PATH/CODE_EVAL_TOOLS and run evaluation/code_eval/setup.sh first")
    args.tools = args.tools.resolve()
    args.output = args.output.expanduser().resolve()
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "logs").mkdir(exist_ok=True)
    jobs, seen = [], set()
    base_inputs = {str(Path(v).expanduser().resolve()) if Path(v).expanduser().exists() else v for v in args.base_model}
    for value in values:
        normalized = str(Path(value).expanduser().resolve()) if Path(value).expanduser().exists() else value
        base = normalized in base_inputs
        error = None
        try:
            model = resolve_model(value, base=base)
        except (OSError, ValueError) as exc:
            model, error = normalized, str(exc)
        key = job_key(model, base)
        if key in seen:
            continue
        seen.add(key)
        jobs.append(dict(model=model, input=value, base_model=base,
                         status="FAILED" if error else "QUEUED", error=error,
                         output=str(args.output / "models" / key), log=str(args.output / "logs" / (key + ".log"))))
    import fcntl
    with (args.output / ".lock").open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            parser.error("Another batch is using this output directory")
        cancelled = threading.Event()
        def cancel(signum, frame):
            cancelled.set()
        signal.signal(signal.SIGINT, cancel)
        signal.signal(signal.SIGTERM, cancel)
        print(f"Models: {len(jobs)} | GPUs: {','.join(args.gpus)} | HumanEval+ and MBPP+ | TP=1", flush=True)
        raise SystemExit(execute(args, jobs, cancelled=cancelled))


if __name__ == "__main__":
    main()
