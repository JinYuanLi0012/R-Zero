#!/usr/bin/env python3
"""Run the blind generative-v2 semantic-pair diagnostic with a frozen base LM."""

from __future__ import annotations

import argparse
import json
import platform
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from .run_pair_judge import (
        atomic_json, atomic_jsonl, git_head, looks_nonbase, read_blind, resolve_dtype,
        sha256_bytes, sha256_file,
    )
except ImportError:  # Direct script execution.
    from run_pair_judge import (
        atomic_json, atomic_jsonl, git_head, looks_nonbase, read_blind, resolve_dtype,
        sha256_bytes, sha256_file,
    )


PROMPT_VERSION = "semantic-pair-generative-v2"
ORDERS = ("q1_q2", "q2_q1")
PROMPT_TEMPLATE = (
    "You are judging whether two math problems are semantic duplicates.\n\n"
    "Classify them as SAME_TYPE only if, after ignoring superficial differences\n"
    "such as wording, variable names, notation, harmless numerical substitutions,\n"
    "or story dressing, they have essentially the same mathematical structure and\n"
    "can be solved using the same high-level solution strategy.\n\n"
    "Classify them as DIFFERENT if they require a materially different key idea,\n"
    "mathematical model, theorem, or case structure. Sharing only a topic,\n"
    "keywords, or similar-looking formulas is not enough.\n\n"
    "If the match is not clear, choose DIFFERENT.\n\n"
    "Do not fully solve the problems. Give a brief justification, then end with\n"
    "exactly \\boxed{SAME_TYPE} or \\boxed{DIFFERENT}.\n\n"
    "Question A:\n{question_a}\n\n"
    "Question B:\n{question_b}\n\n"
    "Analysis: "
)
BOXED_LABEL = re.compile(r"\\boxed\{(SAME_TYPE|DIFFERENT)\}")
FINAL_BOXED_LABEL = re.compile(
    r"\\boxed\{(SAME_TYPE|DIFFERENT)\}\s*\Z"
)


def build_prompt(question_a: str, question_b: str) -> str:
    """Only the two question strings are substituted into the fixed prompt."""
    return PROMPT_TEMPLATE.replace("{question_a}", question_a).replace(
        "{question_b}", question_b
    )


def parse_response(raw_response: str) -> dict[str, str | None]:
    """Parse exactly one boxed label at the end; never infer from ordinary prose."""
    labels = BOXED_LABEL.findall(raw_response)
    if not labels:
        return {
            "predicted_label": "FORMAT_ERROR",
            "parsed_label": None,
            "format_error_reason": "missing_boxed_label",
        }
    if len(labels) > 1:
        reason = "conflicting_boxed_labels" if len(set(labels)) > 1 else "multiple_boxed_labels"
        return {
            "predicted_label": "FORMAT_ERROR",
            "parsed_label": None,
            "format_error_reason": reason,
        }
    final_match = FINAL_BOXED_LABEL.search(raw_response)
    if final_match is None:
        return {
            "predicted_label": "FORMAT_ERROR",
            "parsed_label": None,
            "format_error_reason": "boxed_label_not_final",
        }
    return {
        "predicted_label": final_match.group(1),
        "parsed_label": final_match.group(1),
        "format_error_reason": None,
    }


@dataclass(frozen=True)
class Condition:
    pair_id: str
    question_order: str
    prompt: str


def make_conditions(rows: list[dict[str, str]]) -> list[Condition]:
    conditions: list[Condition] = []
    for row in rows:
        for order in ORDERS:
            question_a, question_b = (
                (row["q1"], row["q2"]) if order == "q1_q2" else (row["q2"], row["q1"])
            )
            conditions.append(Condition(
                pair_id=row["pair_id"], question_order=order,
                prompt=build_prompt(question_a, question_b),
            ))
    return conditions


def generate_responses(
    model: Any,
    tokenizer: Any,
    torch: Any,
    conditions: list[Condition],
    device: str,
    batch_size: int,
    max_new_tokens: int,
) -> list[str]:
    responses: list[str] = []
    for start in range(0, len(conditions), batch_size):
        batch = conditions[start:start + batch_size]
        encoded = tokenizer(
            [condition.prompt for condition in batch],
            return_tensors="pt", padding=True, add_special_tokens=True,
        )
        input_ids = encoded["input_ids"].to(device)
        attention_mask = encoded["attention_mask"].to(device)
        prompt_width = input_ids.shape[1]
        generated = model.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            do_sample=False,
            num_beams=1,
            max_new_tokens=max_new_tokens,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
            use_cache=True,
        )
        for row in generated:
            continuation_ids = row[prompt_width:]
            responses.append(tokenizer.decode(continuation_ids, skip_special_tokens=True))
        del encoded, input_ids, attention_mask, generated
    return responses


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="blind JSONL only")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model", default="Qwen/Qwen3-4B-Base")
    parser.add_argument("--revision", default=None)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument(
        "--dtype", choices=("auto", "bfloat16", "float16", "float32"),
        default="bfloat16",
    )
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--max-new-tokens", type=int, default=256)
    parser.add_argument("--expected-count", type=int, default=50)
    parser.add_argument("--local-files-only", action="store_true")
    parser.add_argument("--trust-remote-code", action="store_true")
    parser.add_argument("--allow-nonbase-model", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = arguments()
    if args.batch_size < 1 or args.max_new_tokens < 1:
        raise ValueError("--batch-size and --max-new-tokens must be positive")
    if looks_nonbase(args.model) and not args.allow_nonbase_model:
        raise ValueError(
            "model path looks instruction-tuned or trained; pass the frozen base model, "
            "or explicitly acknowledge the deviation with --allow-nonbase-model"
        )
    prediction_path = args.output_dir / "predictions_v2.jsonl"
    manifest_path = args.output_dir / "run_manifest_v2.json"
    if not args.overwrite and (prediction_path.exists() or manifest_path.exists()):
        raise FileExistsError("v2 output already exists; use a new directory or --overwrite")

    blind = read_blind(args.input, args.expected_count)

    import torch
    import transformers
    from transformers import AutoModelForCausalLM, AutoTokenizer

    if args.device.startswith("cuda") and not torch.cuda.is_available():
        raise RuntimeError(f"CUDA device requested but CUDA is unavailable: {args.device}")
    dtype = resolve_dtype(torch, args.dtype, args.device)
    load_options = {
        "revision": args.revision,
        "local_files_only": args.local_files_only,
        "trust_remote_code": args.trust_remote_code,
    }
    tokenizer = AutoTokenizer.from_pretrained(args.model, **load_options)
    model = AutoModelForCausalLM.from_pretrained(
        args.model, torch_dtype=dtype, low_cpu_mem_usage=True, **load_options,
    )
    if tokenizer.eos_token_id is None:
        raise RuntimeError("tokenizer has no eos_token_id")
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left"
    model.to(args.device)
    model.eval()
    for parameter in model.parameters():
        parameter.requires_grad_(False)

    conditions = make_conditions(blind)
    with torch.inference_mode():
        raw_responses = generate_responses(
            model, tokenizer, torch, conditions, args.device,
            args.batch_size, args.max_new_tokens,
        )
    if len(raw_responses) != len(conditions):
        raise RuntimeError(
            f"generation coverage mismatch: {len(raw_responses)} vs {len(conditions)}"
        )

    predictions = []
    for condition, raw_response in zip(conditions, raw_responses):
        predictions.append({
            "pair_id": condition.pair_id,
            "question_order": condition.question_order,
            "raw_response": raw_response,
            **parse_response(raw_response),
            "model": args.model,
            "model_revision": getattr(model.config, "_commit_hash", None) or args.revision,
            "prompt_version": PROMPT_VERSION,
        })

    args.output_dir.mkdir(parents=True, exist_ok=True)
    atomic_jsonl(prediction_path, predictions)
    gpu_name = None
    if args.device.startswith("cuda"):
        gpu_name = torch.cuda.get_device_name(torch.device(args.device))
    atomic_json(manifest_path, {
        "experiment": "semantic_judge_offline_50_generative_v2",
        "evaluation_status": "diagnostic_rerun_not_held_out_validation",
        "prompt_version": PROMPT_VERSION,
        "prompt_template": PROMPT_TEMPLATE,
        "prompt_sha256": sha256_bytes(PROMPT_TEMPLATE.encode("utf-8")),
        "blind_input": str(args.input.resolve()),
        "blind_input_sha256": sha256_file(args.input),
        "blind_input_fields_visible_to_model": ["q1", "q2"],
        "pair_count": len(blind),
        "condition_count": len(predictions),
        "question_orders": list(ORDERS),
        "model_argument": args.model,
        "model_name_or_path": getattr(model, "name_or_path", None),
        "model_revision": getattr(model.config, "_commit_hash", None) or args.revision,
        "model_class": type(model).__name__,
        "tokenizer_class": type(tokenizer).__name__,
        "interface": "plain_completion_without_chat_template",
        "generation": {
            "do_sample": False,
            "num_beams": 1,
            "max_new_tokens": args.max_new_tokens,
            "padding_side": tokenizer.padding_side,
        },
        "parsing": {
            "rule": "exactly one boxed SAME_TYPE/DIFFERENT label at end of response",
            "format_error_label": "FORMAT_ERROR",
        },
        "requested_dtype": args.dtype,
        "resolved_dtype": str(dtype),
        "device": args.device,
        "gpu": gpu_name,
        "batch_size": args.batch_size,
        "git_head": git_head(),
        "software": {
            "python": platform.python_version(),
            "torch": torch.__version__,
            "transformers": transformers.__version__,
        },
        "nonbase_model_override": bool(args.allow_nonbase_model),
    })
    format_errors = sum(row["predicted_label"] == "FORMAT_ERROR" for row in predictions)
    print(f"wrote {len(predictions)} generative-v2 conditions to {prediction_path}")
    print(f"strict parser format errors: {format_errors}")
    print(f"wrote run metadata to {manifest_path}")


if __name__ == "__main__":
    main()
