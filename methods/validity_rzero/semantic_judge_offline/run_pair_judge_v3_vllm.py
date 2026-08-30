#!/usr/bin/env python3
"""Run the blind generative-v3 semantic-pair diagnostic with batched vLLM."""

from __future__ import annotations

import argparse
import json
import math
import os
import platform
import re
import time
from pathlib import Path
from typing import Any

from run_pair_judge import (
    atomic_json, atomic_jsonl, git_head, looks_nonbase, read_blind,
    sha256_bytes, sha256_file,
)
from run_pair_judge_v2 import ORDERS, PROMPT_TEMPLATE, make_conditions


PROMPT_VERSION = "semantic-pair-generative-v3-vllm"
STOP_STRINGS = (r"\boxed{SAME_TYPE}", r"\boxed{DIFFERENT}")
SEMANTIC_BOX = re.compile(
    r"\\boxed\s*\{\s*(?:"
    r"(?P<plain>SAME(?:\\)?_TYPE|DIFFERENT)"
    r"|\\text\s*\{\s*(?P<text>SAME(?:\\)?_TYPE|DIFFERENT)\s*\}"
    r")\s*\}"
)


def parse_response_v3(raw_response: str) -> dict[str, str | None]:
    """Accept boxed LaTeX variants, but never infer a label from ordinary prose."""
    labels = []
    for match in SEMANTIC_BOX.finditer(raw_response):
        label = (match.group("plain") or match.group("text")).replace(r"\_", "_")
        labels.append(label)
    unique = set(labels)
    if not unique:
        return {
            "predicted_label": "FORMAT_ERROR",
            "parsed_label": None,
            "format_status": "error",
            "format_error_reason": "missing_boxed_label",
        }
    if len(unique) > 1:
        return {
            "predicted_label": "FORMAT_ERROR",
            "parsed_label": None,
            "format_status": "error",
            "format_error_reason": "conflicting_boxed_labels",
        }
    label = next(iter(unique))
    return {
        "predicted_label": label,
        "parsed_label": label,
        "format_status": "ok",
        "format_error_reason": None,
    }


def sampling_options(max_tokens: int, seed: int) -> dict[str, Any]:
    """Qwen3 official anti-repetition sampling plus task-specific stop strings."""
    return {
        "n": 1,
        "max_tokens": max_tokens,
        "temperature": 0.6,
        "top_p": 0.95,
        "top_k": 20,
        "min_p": 0.0,
        "presence_penalty": 1.5,
        "frequency_penalty": 0.0,
        "repetition_penalty": 1.0,
        "seed": seed,
        "stop": list(STOP_STRINGS),
        "include_stop_str_in_output": True,
        "skip_special_tokens": True,
    }


def percentile(values: list[int], probability: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(ordered[lower])
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def token_statistics(values: list[int]) -> dict[str, float | int | None]:
    return {
        "total": sum(values),
        "mean": sum(values) / len(values) if values else None,
        "p50": percentile(values, 0.50),
        "p95": percentile(values, 0.95),
        "max": max(values) if values else None,
    }


def runtime_metrics(
    model_load_seconds: float,
    generation_seconds: float,
    total_seconds: float,
    pair_count: int,
    prompt_token_counts: list[int],
    output_token_counts: list[int],
) -> dict[str, Any]:
    condition_count = len(prompt_token_counts)
    if len(output_token_counts) != condition_count:
        raise ValueError("prompt/output token count coverage differs")
    if generation_seconds <= 0:
        raise ValueError("generation wall time must be positive")
    return {
        "timing_seconds": {
            "model_load_init": model_load_seconds,
            "generation_wall": generation_seconds,
            "total_wall": total_seconds,
        },
        "counts": {"pairs": pair_count, "prompts": condition_count, "conditions": condition_count},
        "tokens": {
            "prompt": token_statistics(prompt_token_counts),
            "generated": token_statistics(output_token_counts),
            "percentile_method": "linear interpolation at (n-1)*p",
        },
        "throughput": {
            "conditions_per_second": condition_count / generation_seconds,
            "pairs_per_second": pair_count / generation_seconds,
            "output_tokens_per_second": sum(output_token_counts) / generation_seconds,
        },
    }


def load_generation_config(
    model: str, revision: str | None, local_files_only: bool,
) -> tuple[dict[str, Any], str, str, str | None]:
    model_path = Path(model)
    if model_path.is_dir():
        config_path = model_path / "generation_config.json"
    else:
        from huggingface_hub import hf_hub_download
        config_path = Path(hf_hub_download(
            repo_id=model,
            filename="generation_config.json",
            revision=revision,
            local_files_only=local_files_only,
        ))
    if not config_path.is_file():
        raise FileNotFoundError(f"generation_config.json not found: {config_path}")
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    resolved_revision = revision
    parts = config_path.parts
    if "snapshots" in parts:
        snapshot_index = parts.index("snapshots")
        if snapshot_index + 1 < len(parts):
            resolved_revision = parts[snapshot_index + 1]
    return (
        payload,
        str(config_path.resolve()),
        str(config_path.parent.resolve()),
        resolved_revision,
    )


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="blind JSONL only")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model", default="Qwen/Qwen3-4B-Base")
    parser.add_argument("--revision", default=None)
    parser.add_argument("--max-tokens", type=int, default=256)
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
        raise ValueError(
            "model path looks instruction-tuned or trained; pass the frozen base model, "
            "or explicitly acknowledge the deviation with --allow-nonbase-model"
        )
    prediction_path = args.output_dir / "predictions_v3_vllm.jsonl"
    manifest_path = args.output_dir / "run_manifest_v3_vllm.json"
    if not args.overwrite and (prediction_path.exists() or manifest_path.exists()):
        raise FileExistsError("v3 output already exists; use a new directory or --overwrite")

    blind = read_blind(args.input, args.expected_count)
    conditions = make_conditions(blind)
    prompts = [condition.prompt for condition in conditions]
    model_generation_config, generation_config_path, resolved_model_path, resolved_revision = (
        load_generation_config(args.model, args.revision, args.local_files_only)
    )

    import torch
    import vllm
    from vllm import LLM, SamplingParams

    options = sampling_options(args.max_tokens, args.seed)
    sampling_params = SamplingParams(**options)
    llm_options = {
        "model": resolved_model_path,
        "tokenizer": resolved_model_path,
        "dtype": "bfloat16",
        "tensor_parallel_size": args.tensor_parallel_size,
        "gpu_memory_utilization": args.gpu_memory_utilization,
        "seed": args.seed,
        "trust_remote_code": args.trust_remote_code,
    }
    load_start = time.perf_counter()
    llm = LLM(**llm_options)
    model_load_seconds = time.perf_counter() - load_start

    generation_start = time.perf_counter()
    outputs = llm.generate(prompts, sampling_params=sampling_params, use_tqdm=True)
    generation_seconds = time.perf_counter() - generation_start
    if len(outputs) != len(conditions):
        raise RuntimeError(f"generation coverage mismatch: {len(outputs)} vs {len(conditions)}")

    predictions = []
    prompt_token_counts = []
    output_token_counts = []
    for condition, request_output in zip(conditions, outputs):
        if len(request_output.outputs) != 1:
            raise RuntimeError(
                f"expected one completion for {condition.pair_id}, got {len(request_output.outputs)}"
            )
        completion = request_output.outputs[0]
        raw_response = completion.text
        prompt_tokens = len(request_output.prompt_token_ids or [])
        output_tokens = len(completion.token_ids or [])
        prompt_token_counts.append(prompt_tokens)
        output_token_counts.append(output_tokens)
        predictions.append({
            "pair_id": condition.pair_id,
            "question_order": condition.question_order,
            "raw_response": raw_response,
            **parse_response_v3(raw_response),
            "finish_reason": completion.finish_reason,
            "stop_reason": getattr(completion, "stop_reason", None),
            "prompt_token_count": prompt_tokens,
            "output_token_count": output_tokens,
            "model": args.model,
            "model_revision": resolved_revision,
            "prompt_version": PROMPT_VERSION,
        })

    args.output_dir.mkdir(parents=True, exist_ok=True)
    atomic_jsonl(prediction_path, predictions)
    total_seconds = time.perf_counter() - total_start
    runtime = runtime_metrics(
        model_load_seconds, generation_seconds, total_seconds, len(blind),
        prompt_token_counts, output_token_counts,
    )
    cuda_devices = [
        torch.cuda.get_device_name(index) for index in range(torch.cuda.device_count())
    ]
    manifest = {
        "experiment": "semantic_judge_offline_50_generative_v3_vllm",
        "evaluation_status": "diagnostic_rerun_not_held_out_validation",
        "prompt_version": PROMPT_VERSION,
        "prompt_template": PROMPT_TEMPLATE,
        "prompt_sha256": sha256_bytes(PROMPT_TEMPLATE.encode("utf-8")),
        "blind_input": str(args.input.resolve()),
        "blind_input_sha256": sha256_file(args.input),
        "blind_input_fields_visible_to_model": ["q1", "q2"],
        "question_orders": list(ORDERS),
        "model_argument": args.model,
        "resolved_model_path": resolved_model_path,
        "model_revision": resolved_revision,
        "model_generation_config_path": generation_config_path,
        "model_generation_config": model_generation_config,
        "interface": "vllm_plain_completion_without_chat_template",
        "sampling_parameter_source": {
            "selected": (
                "Qwen3 official thinking-mode preset plus its documented "
                "presence_penalty=1.5 mitigation for observed endless repetition"
            ),
            "qwen3_official": "temperature=0.6, top_p=0.95, top_k=20, min_p=0",
            "qwen3_repetition_mitigation": "presence_penalty=1.5",
            "base_generation_config_inspected_but_rejected": model_generation_config,
            "repository_questioner_reference": "temperature=1.0, top_p=0.95",
            "repository_solver_reference": "temperature=1.0, top_p=1.0, top_k=40",
            "sources": {
                "base_generation_config": (
                    "https://huggingface.co/Qwen/Qwen3-4B-Base/blob/main/"
                    "generation_config.json"
                ),
                "qwen3_best_practices": "https://huggingface.co/Qwen/Qwen3-4B#best-practices",
                "repository_questioner": "question_generate/question_generate.py",
                "repository_solver": "vllm_service_init/start_vllm_server.py",
            },
        },
        "sampling_params": options,
        "seed": args.seed,
        "stop_strings": list(STOP_STRINGS),
        "include_stop_str_in_output": True,
        "runtime": runtime,
        "gpu": {
            "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
            "visible_device_names": cuda_devices,
            "tensor_parallel_size": args.tensor_parallel_size,
            "gpu_memory_utilization": args.gpu_memory_utilization,
        },
        "git_head": git_head(),
        "software": {
            "python": platform.python_version(),
            "torch": torch.__version__,
            "vllm": vllm.__version__,
        },
        "nonbase_model_override": bool(args.allow_nonbase_model),
    }
    atomic_json(manifest_path, manifest)
    format_errors = sum(row["predicted_label"] == "FORMAT_ERROR" for row in predictions)
    print(f"wrote {len(predictions)} v3/vLLM conditions to {prediction_path}")
    print(f"format errors: {format_errors}")
    print(json.dumps(runtime, indent=2, sort_keys=True))
    print(f"wrote manifest to {manifest_path}")


if __name__ == "__main__":
    main()
