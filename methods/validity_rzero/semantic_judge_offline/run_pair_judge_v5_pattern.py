#!/usr/bin/env python3
"""Run the v5 exercise-pattern prompt diagnostic with the v4 direct framework."""

from __future__ import annotations

import argparse
import json
import os
import platform
import time
from dataclasses import dataclass
from pathlib import Path

from run_pair_judge import (
    atomic_json, atomic_jsonl, git_head, looks_nonbase, read_blind,
    sha256_bytes, sha256_file,
)
from run_pair_judge_v2 import ORDERS
from run_pair_judge_v3_vllm import (
    DEFAULT_MAX_TOKENS, STOP_STRINGS, load_generation_config, parse_response_v3,
    runtime_metrics, sampling_options,
)


PROMPT_VERSION = "semantic-pair-v5-exercise-pattern"
PROMPT_TEMPLATE = (
    "You are judging whether two generated math problems are repetitions of the\n"
    "same exercise pattern for diversity control.\n\n"
    "Choose SAME_TYPE when a human reviewing many generated questions would say:\n"
    '"this is basically the same kind of exercise again."\n\n'
    "The problems do NOT need to have the same constants, formulas, coefficients,\n"
    "variables, number of variables, bounds, or detailed solution steps.\n\n"
    "Focus on the overall exercise pattern:\n"
    "what kind of mathematical setup is presented, and what kind of task the\n"
    "student is being asked to perform.\n\n"
    "Local changes to the setup may still count as the same type if the overall\n"
    "exercise feels like a natural variation of the same recurring pattern.\n\n"
    "Do not choose SAME_TYPE merely because the problems share a broad subject,\n"
    "use similar mathematical vocabulary, or both ask for something generic such\n"
    "as an integer, a maximum, a count, or a remainder.\n\n"
    "If they feel like genuinely different kinds of exercises, choose DIFFERENT.\n\n"
    "If a problem is incomplete or not really a math problem, choose DIFFERENT\n"
    "unless both are clearly repetitions of the same malformed pattern.\n\n"
    "Output exactly \\boxed{SAME_TYPE} or \\boxed{DIFFERENT}. Do not explain.\n\n"
    "Question A:\n{question_a}\n\n"
    "Question B:\n{question_b}\n\n"
    "Answer:"
)


def build_prompt(question_a: str, question_b: str) -> str:
    return PROMPT_TEMPLATE.replace("{question_a}", question_a).replace(
        "{question_b}", question_b
    )


@dataclass(frozen=True)
class Condition:
    pair_id: str
    question_order: str
    prompt: str


def make_conditions(rows: list[dict[str, str]]) -> list[Condition]:
    conditions = []
    for row in rows:
        for order in ORDERS:
            question_a, question_b = (
                (row["q1"], row["q2"]) if order == "q1_q2" else (row["q2"], row["q1"])
            )
            conditions.append(Condition(
                row["pair_id"], order, build_prompt(question_a, question_b)
            ))
    return conditions


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="blind JSONL only")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model", default="Qwen/Qwen3-4B-Base")
    parser.add_argument("--revision", default=None)
    parser.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--tensor-parallel-size", type=int, default=1)
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.85)
    parser.add_argument("--expected-count", type=int, default=50)
    parser.add_argument("--local-files-only", action="store_true")
    parser.add_argument("--trust-remote-code", action="store_true")
    parser.add_argument("--allow-nonbase-model", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> None:
    total_start = time.perf_counter()
    args = arguments()
    if args.max_tokens < 1 or args.tensor_parallel_size < 1:
        raise ValueError("--max-tokens and --tensor-parallel-size must be positive")
    if not 0 < args.gpu_memory_utilization <= 1:
        raise ValueError("--gpu-memory-utilization must be in (0, 1]")
    if looks_nonbase(args.model) and not args.allow_nonbase_model:
        raise ValueError("pass the exact frozen base model, not an Instruct/trained checkpoint")
    prediction_path = args.output_dir / "predictions_v5_pattern.jsonl"
    manifest_path = args.output_dir / "run_manifest_v5_pattern.json"
    if not args.overwrite and (prediction_path.exists() or manifest_path.exists()):
        raise FileExistsError("v5 pattern output exists; use a new directory or --overwrite")

    blind = read_blind(args.input, args.expected_count)
    conditions = make_conditions(blind)
    prompts = [condition.prompt for condition in conditions]
    model_config, config_path, model_path, resolved_revision = load_generation_config(
        args.model, args.revision, args.local_files_only
    )

    import torch
    import vllm
    from vllm import LLM, SamplingParams

    options = sampling_options(args.max_tokens, args.seed)
    sampling_params = SamplingParams(**options)
    load_start = time.perf_counter()
    llm = LLM(
        model=model_path,
        tokenizer=model_path,
        dtype="bfloat16",
        tensor_parallel_size=args.tensor_parallel_size,
        gpu_memory_utilization=args.gpu_memory_utilization,
        seed=args.seed,
        trust_remote_code=args.trust_remote_code,
    )
    model_load_seconds = time.perf_counter() - load_start

    generation_start = time.perf_counter()
    outputs = llm.generate(prompts, sampling_params=sampling_params, use_tqdm=True)
    generation_seconds = time.perf_counter() - generation_start
    if len(outputs) != len(conditions):
        raise RuntimeError(f"generation coverage mismatch: {len(outputs)} vs {len(conditions)}")

    predictions = []
    prompt_counts, output_counts = [], []
    for condition, request in zip(conditions, outputs):
        if len(request.outputs) != 1:
            raise RuntimeError(f"expected one completion for {condition.pair_id}")
        completion = request.outputs[0]
        raw_response = completion.text
        prompt_count = len(request.prompt_token_ids or [])
        output_count = len(completion.token_ids or [])
        prompt_counts.append(prompt_count)
        output_counts.append(output_count)
        predictions.append({
            "pair_id": condition.pair_id,
            "question_order": condition.question_order,
            "raw_response": raw_response,
            **parse_response_v3(raw_response),
            "finish_reason": completion.finish_reason,
            "stop_reason": getattr(completion, "stop_reason", None),
            "prompt_token_count": prompt_count,
            "output_token_count": output_count,
            "model": args.model,
            "model_revision": resolved_revision,
            "prompt_version": PROMPT_VERSION,
        })

    args.output_dir.mkdir(parents=True, exist_ok=True)
    atomic_jsonl(prediction_path, predictions)
    runtime = runtime_metrics(
        model_load_seconds, generation_seconds, time.perf_counter() - total_start,
        len(blind), prompt_counts, output_counts,
    )
    manifest = {
        "experiment": "semantic_judge_offline_50_v5_exercise_pattern",
        "evaluation_status": "diagnostic_prompt_test_not_held_out_validation",
        "controlled_baseline": "v4_direct_label_ablation",
        "only_intended_variable": "SAME_TYPE definition in prompt",
        "prompt_version": PROMPT_VERSION,
        "prompt_template": PROMPT_TEMPLATE,
        "prompt_sha256": sha256_bytes(PROMPT_TEMPLATE.encode("utf-8")),
        "blind_input": str(args.input.resolve()),
        "blind_input_sha256": sha256_file(args.input),
        "blind_input_fields_visible_to_model": ["q1", "q2"],
        "question_orders": list(ORDERS),
        "model_argument": args.model,
        "resolved_model_path": model_path,
        "model_revision": resolved_revision,
        "model_generation_config_path": config_path,
        "model_generation_config": model_config,
        "interface": "vllm_plain_completion_without_chat_template",
        "sampling_params": options,
        "default_max_tokens": DEFAULT_MAX_TOKENS,
        "seed": args.seed,
        "stop_strings": list(STOP_STRINGS),
        "include_stop_str_in_output": True,
        "runtime": runtime,
        "gpu": {
            "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
            "visible_device_names": [
                torch.cuda.get_device_name(index) for index in range(torch.cuda.device_count())
            ],
            "tensor_parallel_size": args.tensor_parallel_size,
            "gpu_memory_utilization": args.gpu_memory_utilization,
        },
        "git_head": git_head(),
        "software": {
            "python": platform.python_version(), "torch": torch.__version__,
            "vllm": vllm.__version__,
        },
        "nonbase_model_override": bool(args.allow_nonbase_model),
    }
    atomic_json(manifest_path, manifest)
    print(f"wrote {len(predictions)} v5 exercise-pattern conditions to {prediction_path}")
    print(json.dumps(runtime, indent=2, sort_keys=True))
    print(f"wrote manifest to {manifest_path}")


if __name__ == "__main__":
    main()
