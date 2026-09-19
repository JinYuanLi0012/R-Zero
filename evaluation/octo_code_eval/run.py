"""Matched Octo Base/Solver evaluation using the repository's training template."""
import argparse
import csv
import importlib.metadata
import multiprocessing
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
LEGACY = HERE.parent / "code_eval"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(LEGACY))
from common import COUNTS, VERSIONS, align, bind, codegen, digest, read, write
from evaluation.code_eval.run import worker, model_identity
from evaluation.octo_code_eval.protocol import TEMPLATE, configure, render, TokenInputModel


def generate(args):
    from transformers import AutoConfig, AutoTokenizer
    if AutoConfig.from_pretrained(args.model, revision=args.revision).model_type != "llama":
        raise ValueError("Expected the Llama architecture used by OctoThinker Hybrid Base")
    template = read(args.output / "config.json")["protocol"]["template"]
    tokenizer = configure(AutoTokenizer.from_pretrained(args.model, revision=args.revision),
                          template, base_model=args.base_model)
    bind(args.output / "tokenizer_protocol.json", {
        "template_hash": digest(template), "bos_token_id": tokenizer.bos_token_id,
        "eos_token_id": tokenizer.eos_token_id, "add_special_tokens": False,
        "input_kind": "prompt_token_ids",
    })
    selected = []
    for dataset in args.datasets:
        folder = args.output / dataset
        tasks = [render(t, tokenizer, args.max_new_tokens, args.max_model_len)
                 for t in read(folder / "tasks.json")]
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
    bind(args.output / "generation_environment.json", {
        name: importlib.metadata.version(name) for name in ["vllm", "torch", "transformers"]})
    # Ignore per-checkpoint generation_config defaults so Base/Solver use identical
    # sampling settings. EOS is explicitly supplied from the checked tokenizer.
    model = LLM(model=args.model, revision=args.revision, tokenizer_revision=args.revision,
                tensor_parallel_size=args.tp, dtype=args.dtype, max_model_len=args.max_model_len,
                gpu_memory_utilization=args.gpu_memory_utilization, seed=args.seed,
                generation_config="vllm")

    def params(task):
        return SamplingParams(n=1, temperature=0.0, top_p=1.0,
                              max_tokens=args.max_new_tokens, stop=task["stop"],
                              stop_token_ids=[tokenizer.eos_token_id], seed=args.seed)

    for folder, tasks, existing in selected:
        codegen(TokenInputModel(model, tasks), tasks, existing, params, args.batch_size,
                lambda rows, folder=folder: write(folder / "raw.json", rows))


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, help="Complete merged Solver checkpoint or original Octo Base")
    parser.add_argument("--base-model", action="store_true", help="Original Base baseline: supply the training template if absent")
    parser.add_argument("--revision", help="HF revision for an original Base model ID")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--tools", type=Path, default=os.environ.get("CODE_EVAL_TOOLS") or
                        (str(Path(os.environ["STORAGE_PATH"]) / "code_eval_tools") if os.environ.get("STORAGE_PATH") else None))
    parser.add_argument("--datasets", nargs="+", choices=list(COUNTS), default=list(COUNTS))
    parser.add_argument("--stage", choices=["all", "prepare", "generate", "score"], default="all")
    parser.add_argument("--max-new-tokens", type=int, default=4096)
    parser.add_argument("--max-model-len", type=int, default=16384)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--tp", type=int, default=1)
    parser.add_argument("--dtype", choices=["auto", "bfloat16", "float16"], default="bfloat16")
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.85)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--timeout", type=int, default=6)
    args = parser.parse_args()
    for key in ["max_new_tokens", "max_model_len", "batch_size", "tp", "workers", "timeout"]:
        if getattr(args, key) <= 0:
            parser.error(f"{key} must be positive")
    if args.max_model_len <= args.max_new_tokens or not 0 < args.gpu_memory_utilization < 1:
        parser.error("Invalid context length or GPU memory utilization")
    if not args.tools:
        parser.error("Set STORAGE_PATH or CODE_EVAL_TOOLS; run evaluation/code_eval/setup.sh first")
    args.tools = args.tools.resolve()
    args.output = args.output.resolve()
    args.datasets = list(dict.fromkeys(args.datasets))
    args.prompt_style = "chat"  # One shared protocol; never infer it from model name.
    if Path(args.model).expanduser().is_dir():
        args.model = str(Path(args.model).expanduser().resolve())
    if not (args.tools / "environment.json").is_file():
        parser.error("Run evaluation/code_eval/setup.sh first")
    return args


def main():
    args = parse_args()
    template = TEMPLATE.read_text()
    protocol = {"name": "octo-training-template-code-chat-v1", "template": template,
                "template_hash": digest(template), "input_kind": "prompt_token_ids",
                "add_special_tokens": False, "prompt_style": "chat",
                "generation_config": "vllm", "temperature": 0.0, "samples_per_task": 1}
    config = {k: getattr(args, k) for k in ["revision", "base_model", "datasets", "max_new_tokens",
              "max_model_len", "batch_size", "tp", "dtype", "gpu_memory_utilization", "seed", "workers", "timeout"]}
    config.update({"model": model_identity(args.model, args.revision), "protocol": protocol,
                   "versions": VERSIONS, "judge_environment": read(args.tools / "environment.json"),
                   "implementation": digest({str(p.relative_to(ROOT)): p.read_text() for p in
                       [*sorted(HERE.glob("*.py")), *sorted(LEGACY.glob("*.py"))]})})
    args.output.mkdir(parents=True, exist_ok=True)
    import fcntl
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
            process = multiprocessing.get_context("spawn").Process(target=generate, args=(args,))
            process.start()
            process.join()
            if process.exitcode != 0:
                raise RuntimeError(f"Generation failed (exit {process.exitcode}); rerun to resume")
        if args.stage in {"all", "score"}:
            # A prepared/copied raw file alone is insufficient to claim this protocol.
            if not (args.output / "tokenizer_protocol.json").is_file():
                raise ValueError("Missing tokenizer protocol; run the Octo generation stage first")
            for dataset in args.datasets:
                worker(args, "score", dataset)
            rows = [read(args.output / d / "summary.json") for d in args.datasets]
            write(args.output / "summary.json", {"model": args.model, "protocol": protocol, "benchmarks": rows})
            with (args.output / "summary.csv").open("w") as handle:
                writer = csv.DictWriter(handle, fieldnames=["dataset", "count", "pass@1_percent", "length_limited_count"], extrasaction="ignore")
                writer.writeheader()
                writer.writerows(rows)
            for row in rows:
                print(f"{row['dataset']}: pass@1 = {row['pass@1_percent']:.2f}%", flush=True)


if __name__ == "__main__":
    main()
