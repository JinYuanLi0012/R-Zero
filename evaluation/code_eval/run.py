"""Run with the existing R-Zero/vLLM Python; scoring uses a separate CPU venv."""
import argparse
import csv
import importlib.metadata
import os
from pathlib import Path
import subprocess
import sys

from common import HERE, COUNTS, VERSIONS, align, bind, codegen, digest, read, write


def model_identity(name, revision):
    path = Path(name).expanduser()
    if not path.is_dir():
        return {"model": name, "revision": revision}
    files = sorted(p for p in path.iterdir() if p.is_file() and
                   (p.suffix in {".json", ".safetensors", ".bin", ".model", ".jinja"}))
    return {"model": str(path.resolve()), "files": [
        [p.name, p.stat().st_size, p.stat().st_mtime_ns] for p in files]}


def generate(args):
    from transformers import AutoTokenizer
    selected = []
    tokenizer = AutoTokenizer.from_pretrained(args.model, revision=args.revision)
    for dataset in args.datasets:
        folder = args.output / dataset
        tasks = read(folder / "tasks.json")
        for task in tasks:
            if args.prompt_style == "base":
                task["rendered_prompt"] = task["prompt"]
            else:
                if not tokenizer.chat_template:
                    raise ValueError("Chat mode requires a tokenizer chat_template; use --prompt-style base")
                task["rendered_prompt"] = tokenizer.apply_chat_template(
                    task["messages"], tokenize=False, add_generation_prompt=True,
                    enable_thinking=False,
                )
            # Do not truncate a benchmark question to make it fit.
            tokens = tokenizer.encode(task["rendered_prompt"], add_special_tokens=True)
            task["prompt_tokens"] = len(tokens)
            if len(tokens) + args.max_new_tokens > args.max_model_len:
                raise ValueError(f"{dataset}/{task['task_id']} needs {len(tokens)} prompt tokens + "
                                 f"{args.max_new_tokens} output tokens; increase --max-model-len")
        bind(folder / "rendered_tasks.json", tasks)
        existing = read(folder / "raw.json") if (folder / "raw.json").exists() else []
        if len(existing) == len(tasks):
            align(tasks, existing)
            print(f"Already generated: {dataset}", flush=True)
        else:
            selected.append((folder, tasks, existing))
    if not selected:
        return
    from vllm import LLM, SamplingParams
    packages = {name: importlib.metadata.version(name) for name in ["vllm", "torch", "transformers"]}
    bind(args.output / "generation_environment.json", packages)
    model = LLM(model=args.model, revision=args.revision, tokenizer_revision=args.revision,
                tensor_parallel_size=args.tp, dtype=args.dtype,
                max_model_len=args.max_model_len, gpu_memory_utilization=args.gpu_memory_utilization,
                seed=args.seed)

    def params(task):
        return SamplingParams(n=1, temperature=0.0, top_p=1.0,
                              max_tokens=args.max_new_tokens, stop=task["stop"],
                              seed=args.seed)

    for folder, tasks, existing in selected:
        codegen(model, tasks, existing, params, args.batch_size,
                lambda rows, folder=folder: write(folder / "raw.json", rows))


def worker(args, stage, dataset):
    command = [str(args.tools / "venv/bin/python"), str(HERE / "worker.py"), stage,
               "--tools", str(args.tools), "--output", str(args.output / dataset),
               "--dataset", dataset, "--prompt-style", args.prompt_style,
               "--workers", str(args.workers), "--timeout", str(args.timeout)]
    print(f"{stage}: {dataset}", flush=True)
    # Do not expose GPUs to the CPU test runner.
    env = dict(os.environ, CUDA_VISIBLE_DEVICES="", TOKENIZERS_PARALLELISM="false")
    subprocess.run(command, check=True, env=env)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, help="Merged HF checkpoint directory or HF model ID")
    parser.add_argument("--revision", help="Optional HF model revision; pin for reproducible Base evaluations")
    parser.add_argument("--output", required=True, type=Path, help="Unique output directory per checkpoint/config")
    parser.add_argument("--tools", type=Path, default=os.environ.get("CODE_EVAL_TOOLS") or
                        (str(Path(os.environ["STORAGE_PATH"]) / "code_eval_tools") if os.environ.get("STORAGE_PATH") else None))
    parser.add_argument("--datasets", nargs="+", choices=list(COUNTS), default=list(COUNTS))
    parser.add_argument("--stage", choices=["all", "prepare", "generate", "score"], default="all")
    parser.add_argument("--prompt-style", choices=["base", "chat"], default="base")
    parser.add_argument("--max-new-tokens", type=int, default=4096)
    parser.add_argument("--max-model-len", type=int, default=16384)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--tp", type=int, default=1)
    parser.add_argument("--dtype", default="bfloat16", choices=["auto", "bfloat16", "float16"])
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.85)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--timeout", type=int, default=6, help="Official LCB per-test timeout in seconds")
    args = parser.parse_args()
    for name in ["max_new_tokens", "max_model_len", "batch_size", "tp", "workers", "timeout"]:
        if getattr(args, name) <= 0:
            parser.error(f"--{name.replace('_', '-')} must be positive")
    if not 0 < args.gpu_memory_utilization < 1:
        parser.error("--gpu-memory-utilization must be between 0 and 1")
    if args.max_model_len <= args.max_new_tokens:
        parser.error("--max-model-len must leave space for the prompt")
    if not args.tools:
        parser.error("Set STORAGE_PATH, CODE_EVAL_TOOLS, or --tools and run setup.sh first")
    args.tools = args.tools.resolve()
    args.output = args.output.resolve()
    args.datasets = list(dict.fromkeys(args.datasets))
    if Path(args.model).expanduser().is_dir():
        args.model = str(Path(args.model).expanduser().resolve())
    if not (args.tools / "environment.json").is_file():
        parser.error("CPU evaluator is not installed; run evaluation/code_eval/setup.sh first")
    config = {key: getattr(args, key) for key in
              ["revision", "datasets", "prompt_style", "max_new_tokens", "max_model_len",
               "batch_size", "tp", "dtype", "gpu_memory_utilization", "seed", "workers", "timeout"]}
    config.update({"model": model_identity(args.model, args.revision), "versions": VERSIONS,
                   "judge_environment": read(args.tools / "environment.json"),
                   "implementation": digest({p.name: p.read_text() for p in sorted(HERE.glob("*.py"))})})
    # Prevent two jobs from interleaving checkpoints in one output directory.
    import fcntl
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / ".lock").open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError(f"Another evaluation is using {args.output}") from None
        bind(args.output / "config.json", config)
        if args.stage in {"all", "prepare"}:
            for dataset in args.datasets:
                worker(args, "prepare", dataset)
        if args.stage == "generate":
            generate(args)
        elif args.stage == "all":
            # Separate process releases all vLLM GPU memory before CPU scoring.
            import multiprocessing
            process = multiprocessing.get_context("spawn").Process(target=generate, args=(args,))
            process.start()
            process.join()
            if process.exitcode != 0:
                raise RuntimeError(f"Generation failed (exit {process.exitcode}); rerun to resume")
        if args.stage in {"all", "score"}:
            for dataset in args.datasets:
                worker(args, "score", dataset)
            summaries = [read(args.output / name / "summary.json") for name in args.datasets]
            write(args.output / "summary.json", {"model": args.model, "benchmarks": summaries})
            with (args.output / "summary.csv").open("w") as handle:
                writer = csv.DictWriter(handle, fieldnames=["dataset", "count", "pass@1_percent", "length_limited_count"], extrasaction="ignore")
                writer.writeheader()
                writer.writerows(summaries)
            for result in summaries:
                print(f"{result['dataset']}: pass@1 = {result['pass@1_percent']:.2f}%", flush=True)


if __name__ == "__main__":
    main()
