"""CPU data preparation and official scoring. Run in the judge venv."""
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys

from common import COUNTS, VERSIONS, align, bind, digest, file_digest, read, write


def official_imports(tools):
    for name in ("evalplus", "livecodebench"):
        root = tools / name
        revision = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
        if revision != VERSIONS[name]:
            raise ValueError(f"Wrong {name} commit; rerun setup.sh")
        if subprocess.check_output(["git", "-C", str(root), "status", "--porcelain"], text=True).strip():
            raise ValueError(f"Official checkout is modified: {root}")
        sys.path.insert(0, str(root))
    # Official LCB prompt module reads example files relative to its repo root.
    os.chdir(tools / "livecodebench")


def load_ep(dataset):
    from evalplus.data import get_human_eval_plus, get_mbpp_plus
    loader = get_human_eval_plus if dataset == "humaneval" else get_mbpp_plus
    return loader(version=VERSIONS[dataset])


def load_lcb():
    from datasets import load_dataset
    from lcb_runner.benchmarks.code_generation import CodeGenerationProblem
    # Same source/options/class as the official loader, but decode one row at a time.
    dataset = load_dataset("livecodebench/code_generation_lite", split="test",
                           version_tag=VERSIONS["livecodebench_release"], trust_remote_code=True)
    ids = dataset["question_id"]
    for index in sorted(range(len(ids)), key=lambda i: ids[i]):
        yield CodeGenerationProblem(**dataset[index])


def prepare(args):
    tasks = []
    if args.dataset == "livecodebench":
        from lcb_runner.prompts.code_generation import (
            get_base_model_question_template_answer, get_generic_question_template_answer,
            PromptConstants,
        )
        args.output.mkdir(parents=True, exist_ok=True)
        path = args.output / "judge_inputs.jsonl"
        pending = path.with_suffix(".pending.jsonl")
        with pending.open("w") as handle:
            for task in load_lcb():
                base = args.prompt_style == "base"
                tasks.append({
                    "task_id": task.question_id,
                    "prompt": get_base_model_question_template_answer(task) if base else None,
                    "messages": None if base else [
                        {"role": "system", "content": PromptConstants.SYSTEM_MESSAGE_GENERIC},
                        {"role": "user", "content": get_generic_question_template_answer(task)},
                    ],
                    "stop": ["### Question"] if base else [],
                })
                # Hidden tests are only written to the CPU judge's file.
                handle.write(json.dumps(task.get_evaluation_sample()) + "\n")
        data_hash = file_digest(pending)
        if path.exists() and file_digest(path) != data_hash:
            raise ValueError("LCB judge data changed; use a new output directory")
        pending.replace(path)
    else:
        from evalplus.provider.utility import EOS, extra_eos_for_direct_completion
        from evalplus.data import get_human_eval_plus_hash, get_mbpp_plus_hash
        dataset = load_ep(args.dataset)
        for key, task in dataset.items():
            prompt = task["prompt"].strip() + "\n"
            base = args.prompt_style == "base"
            tasks.append({
                "task_id": key, "task_prompt": prompt, "entry_point": task["entry_point"],
                "prompt": prompt if base else None,
                "messages": None if base else [{"role": "user", "content":
                    "Please provide a self-contained Python script that solves the following problem "
                    "in a markdown code block:\n```python\n" + prompt + "```"}],
                "stop": list(EOS) + extra_eos_for_direct_completion(args.dataset) if base else [],
            })
        hasher = get_human_eval_plus_hash if args.dataset == "humaneval" else get_mbpp_plus_hash
        data_hash = hasher(version=VERSIONS[args.dataset])
    if len(tasks) != COUNTS[args.dataset]:
        raise ValueError(f"Unexpected {args.dataset} count: {len(tasks)} != {COUNTS[args.dataset]}")
    if len({t['task_id'] for t in tasks}) != len(tasks):
        raise ValueError("Duplicate benchmark task IDs")
    bind(args.output / "tasks.json", tasks)
    bind(args.output / "dataset.json", {
        "dataset": args.dataset, "count": len(tasks), "prompt_style": args.prompt_style,
        "versions": VERSIONS, "data_hash": data_hash, "tasks_hash": digest(tasks),
    })
    print(f"Prepared {args.dataset}: {len(tasks)} tasks", flush=True)


def score(args):
    if sys.platform != "linux":
        raise RuntimeError("Run official code execution on Linux; Mac supports preparation only")
    tasks = read(args.output / "tasks.json")
    raw = align(tasks, read(args.output / "raw.json"))
    signature = {
        "raw_hash": digest(raw), "dataset": read(args.output / "dataset.json"),
        "workers": args.workers, "lcb_timeout": args.timeout,
    }
    bind(args.output / "score_config.json", signature)
    if (args.output / "summary.json").exists():
        print(f"Already scored: {args.output}", flush=True)
        return
    if args.dataset == "livecodebench":
        from lcb_runner.utils.extraction_utils import extract_code
        from lcb_runner.lm_styles import LMStyle
        from lcb_runner.evaluation import codegen_metrics
        style = LMStyle.GenericBase if args.prompt_style == "base" else LMStyle.OpenAIChat
        samples = [{"question_id": t["task_id"], "code_list": [extract_code(r["response"], style)]}
                   for t, r in zip(tasks, raw)]
        write(args.output / "samples.json", samples)
        judge_path = args.output / "judge_inputs.jsonl"
        if file_digest(judge_path) != signature["dataset"]["data_hash"]:
            raise ValueError("LCB judge data changed between preparation and scoring")
        with judge_path.open() as handle:
            judge_inputs = [json.loads(line) for line in handle]
        if len(judge_inputs) != len(tasks):
            raise ValueError("LCB judge inputs are incomplete")
        result = codegen_metrics(
            judge_inputs, [s["code_list"] for s in samples],
            k_list=[1], num_process_evaluate=args.workers, timeout=args.timeout,
        )
        write(args.output / "official_results.json", result)
        score_value = float(result[0]["pass@1"])
        summary = {"pass@1": score_value, "pass@1_percent": 100 * score_value}
    else:
        from evalplus.sanitize import sanitize
        from evalplus.evaluate import evaluate
        # Verify the scorer is using the exact data prepared for generation.
        from evalplus.data import get_human_eval_plus_hash, get_mbpp_plus_hash
        hasher = get_human_eval_plus_hash if args.dataset == "humaneval" else get_mbpp_plus_hash
        if hasher(version=VERSIONS[args.dataset]) != signature["dataset"]["data_hash"]:
            raise ValueError("EvalPlus dataset changed between preparation and scoring")
        samples = [{"task_id": t["task_id"], "solution": sanitize(
            t["task_prompt"] + r["response"] if args.prompt_style == "base" else r["response"],
            entrypoint=t["entry_point"],
        )} for t, r in zip(tasks, raw)]
        path = args.output / "samples.jsonl"
        path.write_text("".join(json.dumps(s) + "\n" for s in samples))
        # EvalPlus writes its output non-atomically. Never reuse an interrupted file.
        results_path = args.output / "official_results.pending.json"
        results_path.unlink(missing_ok=True)
        evaluate(dataset=args.dataset, samples=str(path), parallel=args.workers,
                 version=VERSIONS[args.dataset], output_file=str(results_path),
                 base_only=False, mini=False, noextreme=False)
        result = read(results_path)
        write(args.output / "official_results.json", result)
        results_path.unlink()
        score_value = float(result["pass_at_k"]["plus"]["pass@1"])
        summary = {"pass@1": score_value, "pass@1_percent": 100 * score_value,
                   "base_tests_pass@1_percent": 100 * result["pass_at_k"]["base"]["pass@1"]}
    summary.update({"dataset": args.dataset, "count": len(tasks), "samples_per_task": 1,
                    "length_limited_count": sum(r["finish_reason"] == "length" for r in raw)})
    write(args.output / "summary.json", summary)
    print(summary, flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["check", "prepare", "score"])
    parser.add_argument("--tools", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--dataset", choices=list(COUNTS))
    parser.add_argument("--prompt-style", choices=["base", "chat"], default="base")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--timeout", type=int, default=6)
    args = parser.parse_args()
    args.tools = args.tools.resolve()
    if args.output:
        args.output = args.output.resolve()
    official_imports(args.tools)
    if args.stage == "check":
        from evalplus.sanitize import sanitize
        from evalplus.evaluate import evaluate
        from lcb_runner.evaluation import codegen_metrics
        from lcb_runner.prompts.code_generation import get_base_model_question_template_answer
        packages = {n: importlib.metadata.version(n) for n in
                    ["datasets", "numpy", "tree-sitter", "tree-sitter-python", "psutil"]}
        write(args.tools / "environment.json", {"versions": VERSIONS, "packages": packages,
                                                "python": sys.version})
        print("Official CPU scorer imports OK")
    elif args.stage == "prepare":
        prepare(args)
    else:
        score(args)


if __name__ == "__main__":
    main()
