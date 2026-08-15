#!/usr/bin/env python3
"""One-GPU worker for deterministic frozen-Qwen question judging."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

os.environ.setdefault("VLLM_USE_V1", "0")

from base_judge_common import BASE_JUDGE_SCHEMA, build_prompt, parse_judgment  # noqa: E402
from common import atomic_json, read_jsonl  # noqa: E402


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--shard-index", type=int, required=True)
    parser.add_argument("--num-shards", type=int, required=True)
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.8)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def sampling_params(vllm_module, args: argparse.Namespace, guided: bool):
    options = dict(max_tokens=args.max_tokens, temperature=0.0, top_p=1.0, n=1, seed=args.seed)
    if guided:
        try:
            from vllm.sampling_params import GuidedDecodingParams

            options["guided_decoding"] = GuidedDecodingParams(json=BASE_JUDGE_SCHEMA)
        except (ImportError, TypeError):
            return None
    try:
        return vllm_module.SamplingParams(**options)
    except TypeError:
        return None if guided else vllm_module.SamplingParams(**{k: v for k, v in options.items() if k != "seed"})


def generate(llm, vllm_module, prompts: list[str], args: argparse.Namespace, guided: bool) -> list[str]:
    params = sampling_params(vllm_module, args, guided)
    if params is None:
        raise RuntimeError("guided decoding is unsupported")
    outputs = llm.generate(prompts, sampling_params=params, use_tqdm=True)
    if len(outputs) != len(prompts):
        raise RuntimeError("vLLM returned an unexpected output count")
    return [output.outputs[0].text for output in outputs]


def completed(path: Path, model: str) -> bool:
    if not path.is_file():
        return False
    try:
        artifact = json.loads(path.read_text(encoding="utf-8"))
        return artifact.get("model") == model and artifact.get("status") in {
            "success", "final_parse_failure"
        }
    except (OSError, json.JSONDecodeError):
        return False


def main() -> None:
    args = arguments()
    if args.num_shards < 1 or not 0 <= args.shard_index < args.num_shards:
        raise ValueError("invalid shard assignment")
    if args.batch_size < 1:
        raise ValueError("batch size must be positive")
    all_items = read_jsonl(args.input)
    if any(set(item) != {"opaque_base_judge_id", "question"} for item in all_items):
        raise ValueError("worker input is not blind")
    items = [item for index, item in enumerate(all_items) if index % args.num_shards == args.shard_index]
    pending = [
        item for item in items
        if not (
            args.resume
            and completed(args.output_dir / f"{item['opaque_base_judge_id']}.json", args.model)
        )
    ]
    if not pending:
        return

    import vllm

    llm = vllm.LLM(
        model=args.model, tokenizer=args.model, tensor_parallel_size=1,
        gpu_memory_utilization=args.gpu_memory_utilization, enable_prefix_caching=False,
    )
    for start in range(0, len(pending), args.batch_size):
        batch = pending[start : start + args.batch_size]
        prompts = [build_prompt(item["question"]) for item in batch]
        guided_used = True
        try:
            raw_outputs = generate(llm, vllm, prompts, args, guided=True)
        except Exception:
            guided_used = False
            raw_outputs = generate(llm, vllm, prompts, args, guided=False)
        for item, raw in zip(batch, raw_outputs):
            attempts = [{"raw_completion": raw, "guided_json": guided_used}]
            try:
                judgment = parse_judgment(raw)
                artifact = {"status": "success", "judgment": judgment}
            except ValueError as first_error:
                retry_raw = generate(
                    llm, vllm, [build_prompt(item["question"], retry=True)], args, guided=False
                )[0]
                attempts.append({"raw_completion": retry_raw, "guided_json": False})
                try:
                    judgment = parse_judgment(retry_raw)
                    artifact = {"status": "success", "judgment": judgment}
                except ValueError as retry_error:
                    artifact = {
                        "status": "final_parse_failure", "judgment": None,
                        "failure_reason": str(retry_error), "first_failure_reason": str(first_error),
                    }
            atomic_json(
                args.output_dir / f"{item['opaque_base_judge_id']}.json",
                {
                    "opaque_base_judge_id": item["opaque_base_judge_id"],
                    "model": args.model, "temperature": 0.0, "top_p": 1.0,
                    "max_tokens": args.max_tokens, "attempts": attempts, **artifact,
                },
            )


if __name__ == "__main__":
    main()
