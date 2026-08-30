#!/usr/bin/env python3
"""Run one single-GPU shard of frozen-base semantic-pair inference."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import time
from typing import Callable

from .semantic_judge_offline.run_pair_judge import atomic_json, atomic_jsonl
from .semantic_judge_offline.run_pair_judge_v3_vllm import parse_response_v3, sampling_options


def read_tasks(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--metrics", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--max-tokens", type=int, default=1024)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.85)
    parser.add_argument("--batch-size", type=int, default=512)
    return parser.parse_args()


def generate_with_one_retry(
    tasks: list[dict],
    generate: Callable[[list[str]], list[str]],
    parse: Callable[[str], dict],
) -> dict[str, dict]:
    """Generate all tasks and retry only first-pass strict parse failures once."""
    first_responses = generate([item["prompt"] for item in tasks])
    if len(first_responses) != len(tasks):
        raise RuntimeError("semantic generator returned the wrong number of responses")
    results: dict[str, dict] = {}
    retry: list[dict] = []
    for item, raw_response in zip(tasks, first_responses):
        parsed = parse(raw_response)
        results[item["cache_key"]] = {**parsed, "attempts": 1}
        if parsed["parsed_label"] is None:
            retry.append(item)
    if retry:
        retry_responses = generate([item["prompt"] for item in retry])
        if len(retry_responses) != len(retry):
            raise RuntimeError("semantic retry returned the wrong number of responses")
        for item, raw_response in zip(retry, retry_responses):
            results[item["cache_key"]] = {**parse(raw_response), "attempts": 2}
    return results


def main() -> None:
    args = arguments()
    tasks = read_tasks(args.input)
    if not tasks:
        atomic_jsonl(args.output, [])
        atomic_json(args.metrics, {"task_count": 0, "model_load_seconds": 0.0, "generation_seconds": 0.0})
        return

    from vllm import LLM, SamplingParams

    sampling = SamplingParams(**sampling_options(args.max_tokens, args.seed))
    load_start = time.perf_counter()
    model = LLM(
        model=args.model,
        tokenizer=args.model,
        dtype="bfloat16",
        tensor_parallel_size=1,
        gpu_memory_utilization=args.gpu_memory_utilization,
        seed=args.seed,
    )
    model_load_seconds = time.perf_counter() - load_start
    results: dict[str, dict] = {}
    generation_seconds = 0.0
    for start in range(0, len(tasks), args.batch_size):
        batch = tasks[start:start + args.batch_size]
        def generate(prompts: list[str]) -> list[str]:
            nonlocal generation_seconds
            generation_start = time.perf_counter()
            generated = model.generate(prompts, sampling_params=sampling, use_tqdm=True)
            generation_seconds += time.perf_counter() - generation_start
            return [output.outputs[0].text for output in generated]

        results.update(generate_with_one_retry(batch, generate, parse_response_v3))
    rows = [{"cache_key": item["cache_key"], **results[item["cache_key"]]} for item in tasks]
    atomic_jsonl(args.output, rows)
    atomic_json(args.metrics, {
        "task_count": len(tasks),
        "model_load_seconds": model_load_seconds,
        "generation_seconds": generation_seconds,
        "final_parse_success_count": sum(row["parsed_label"] is not None for row in rows),
        "final_parse_failure_count": sum(row["parsed_label"] is None for row in rows),
    })


if __name__ == "__main__":
    main()
