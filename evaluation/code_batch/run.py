"""Explicit Qwen/Octo routing for a shared multi-GPU code-evaluation queue."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import csv
from datetime import datetime
import json
import math
import os
from pathlib import Path
import queue
import re
import signal
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from evaluation.octo_code_batch.run import atomic_json, job_key, parse_scores, resolve_model, run_child

ENTRIES = {"qwen": ROOT / "evaluation/code_eval/run.py", "octo": ROOT / "evaluation/octo_code_eval/run.py"}
COLUMNS = ["label", "family", "protocol", "status", "humaneval_plus", "mbpp_plus", "gpu", "minutes", "model", "output", "log", "error"]


def read_records(args):
    records = []
    if args.manifest:
        records = json.loads(args.manifest.read_text())
        if not isinstance(records, list):
            raise ValueError("Manifest must be a JSON list")
        for record in records:
            if not isinstance(record, dict) or record.get("family") not in ENTRIES:
                raise ValueError("Each manifest row requires family=qwen or octo")
            if not isinstance(record.get("model"), str) or not record["model"].strip():
                raise ValueError("Each manifest row requires a nonempty model path/ID")
            if not isinstance(record.get("base_model", False), bool):
                raise ValueError("base_model must be a JSON boolean")
        if args.family:
            records = [r for r in records if r["family"] == args.family]
    paths = list(args.models)
    if args.models_file:
        paths += [s.strip() for s in args.models_file.read_text().splitlines() if s.strip() and not s.lstrip().startswith("#")]
    paths += args.base_model
    if paths and not args.family:
        raise ValueError("Use --family qwen|octo for plain checkpoint paths or --models-file")
    records += [{"family": args.family, "model": p, "base_model": p in args.base_model} for p in paths]
    if not records:
        raise ValueError("No models selected")
    return records


def plan(records, output, qwen_style, validate=True, protocol_mode="legacy"):
    jobs, seen = [], set()
    for record in records:
        value = record["model"].strip()
        # Accept pasted Markdown-escaped underscores and a single weight shard path.
        value = value.replace("\\_", "_")
        if value.endswith((".safetensors", ".bin")):
            value = str(Path(value).parent)
        base = record.get("base_model", False)
        error = None
        try:
            model = resolve_model(value, base=base) if validate else value
        except (OSError, ValueError) as exc:
            model, error = value, str(exc)
        family = record["family"]
        protocol = "octo-training-chat" if family == "octo" else "qwen-" + qwen_style
        if protocol_mode == "matched":
            protocol = family + "-matched-code-v1"
        if protocol_mode == "final":
            protocol = "code-eval-final-v1"
        key = job_key(family + ":" + protocol + ":" + model, base)
        if key in seen:
            continue
        seen.add(key)
        label = record.get("label") or Path(model).name
        jobs.append(dict(label=label, family=family, protocol=protocol, model=model,
                         base_model=base, status="FAILED" if error else "QUEUED", error=error,
                         output=str(output / "models" / key), log=str(output / "logs" / (key + ".log"))))
    return jobs


def command_for(args, job):
    final = job["protocol"] == "code-eval-final-v1"
    matched = job["protocol"].endswith("-matched-code-v1")
    entry = ROOT / "evaluation/matched_code_eval/run.py" if matched else ENTRIES[job["family"]]
    if final:
        entry = ROOT / "evaluation/final_code_eval/run.py"
    command = [sys.executable, "-u", str(entry), "--model", job["model"],
               "--output", job["output"], "--tools", str(args.tools),
               "--datasets", "humaneval", "mbpp", "--tp", "1"]
    if final:
        command += ["--family", job["family"]]
    elif matched:
        command += ["--family", job["family"]]
        if job["base_model"]:
            command.append("--base-model")
    elif job["family"] == "octo":
        if job["base_model"]:
            command.append("--base-model")
    else:
        command += ["--prompt-style", args.qwen_prompt_style]
    for key in ["workers", "max_new_tokens", "max_model_len", "batch_size", "gpu_memory_utilization", "seed", "timeout"]:
        command += ["--" + key.replace("_", "-"), str(getattr(args, key))]
    return command


def table(jobs):
    lines = [f"{'#':>3} {'Status':<10} {'Family/protocol':<21} {'GPU':>4} {'HumanEval+':>11} {'MBPP+':>9} {'Min':>7}  Model",
             "-" * 108]
    for i, job in enumerate(jobs, 1):
        scores = [f"{job[k]:.2f}" if job.get(k) is not None else "--" for k in ["humaneval_plus", "mbpp_plus"]]
        lines.append(f"{i:>3} {job['status']:<10} {job['protocol']:<21} {str(job.get('gpu', '--')):>4} "
                     f"{scores[0]:>11} {scores[1]:>9} {job.get('minutes', 0):>7.1f}  {job['label']}")
        if job.get("error"):
            lines.append(f"    {job['error']} | log: {job['log']}")
    return "\n".join(lines)


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
            start = time.monotonic()
            with lock:
                job.update(status="RUNNING", gpu=gpu)
                save()
                print(f"[GPU {gpu}] START {job['label']} ({job['protocol']})", flush=True)
            try:
                env = dict(os.environ, CUDA_VISIBLE_DEVICES=gpu, XDG_CACHE_HOME=str(cache),
                           TORCHINDUCTOR_CACHE_DIR=str(cache / "inductor"),
                           TRITON_CACHE_DIR=str(cache / "triton"), PYTHONUNBUFFERED="1")
                code = launch(command_for(args, job), env, Path(job["log"]), cancelled, args.job_timeout_hours * 3600)
                if code:
                    raise RuntimeError({124: "Job timeout", 130: "Interrupted"}.get(code, f"Evaluator exited with code {code}"))
                result = dict(status="DONE", **parse_scores(Path(job["output"]) / "summary.json"))
            except Exception as exc:
                result = dict(status="CANCELLED" if cancelled.is_set() else "FAILED", error=str(exc))
            with lock:
                job.update(result, minutes=round((time.monotonic() - start) / 60, 2))
                save()
                print(f"[GPU {gpu}] {job['status']} {job['label']}"
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
    print("\n" + table(jobs) + f"\n\nSaved: {args.output / 'summary.csv'}", flush=True)
    return 130 if cancelled.is_set() else int(any(j["status"] != "DONE" for j in jobs))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("models", nargs="*")
    parser.add_argument("--family", choices=list(ENTRIES), help="Required for plain paths; filters a mixed manifest")
    parser.add_argument("--manifest", type=Path, help="JSON list of {family, model, label, base_model}")
    parser.add_argument("--models-file", type=Path)
    parser.add_argument("--base-model", action="append", default=[])
    parser.add_argument("--protocol", choices=["legacy", "matched", "final"], default="final")
    parser.add_argument("--qwen-prompt-style", choices=["base", "chat"], default=None)
    parser.add_argument("--gpus", default="0,1,2,3")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--tools", type=Path, default=os.environ.get("CODE_EVAL_TOOLS") or
                        (str(Path(os.environ["STORAGE_PATH"]) / "code_eval_tools") if os.environ.get("STORAGE_PATH") else None))
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--max-new-tokens", type=int, default=4096)
    parser.add_argument("--max-model-len", type=int, default=16384)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.85)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--timeout", type=int, default=6)
    parser.add_argument("--job-timeout-hours", type=float, default=0)
    parser.add_argument("--dry-run", action="store_true", help="Show family/protocol/input paths without loading models or checking remote filesystem")
    args = parser.parse_args()
    if args.protocol != "legacy" and args.qwen_prompt_style is not None:
        parser.error("--qwen-prompt-style applies only to --protocol legacy")
    args.qwen_prompt_style = args.qwen_prompt_style or "base"
    args.output = args.output.expanduser().resolve()
    args.gpus = [g.strip() for g in args.gpus.split(",")]
    if not all(re.fullmatch(r"\d+|GPU-[\w-]+|MIG-[\w./-]+", g) for g in args.gpus) or len(set(args.gpus)) != len(args.gpus):
        parser.error("--gpus must contain distinct GPU IDs")
    if any(getattr(args, k) <= 0 for k in ["workers", "max_new_tokens", "max_model_len", "batch_size", "timeout"]):
        parser.error("Token limits, batch size and workers must be positive")
    if args.max_model_len <= args.max_new_tokens or not 0 < args.gpu_memory_utilization < 1 or not math.isfinite(args.job_timeout_hours) or args.job_timeout_hours < 0:
        parser.error("Invalid context length, GPU utilization or timeout")
    try:
        jobs = plan(read_records(args), args.output, args.qwen_prompt_style, validate=not args.dry_run, protocol_mode=args.protocol)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    if args.dry_run:
        print(table(jobs))
        for j in jobs:
            print(f"{j['label']}: {j['model']}")
        print(f"Total {len(jobs)}; qwen={sum(j['family'] == 'qwen' for j in jobs)}, octo={sum(j['family'] == 'octo' for j in jobs)}. Paths not validated.")
        return
    if not args.tools or not (args.tools / "environment.json").is_file():
        parser.error("Set STORAGE_PATH/CODE_EVAL_TOOLS and run evaluation/code_eval/setup.sh first")
    args.tools = args.tools.resolve()
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "logs").mkdir(exist_ok=True)
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
