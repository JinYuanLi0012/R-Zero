#!/usr/bin/env python3
"""Run the three audit passes through concurrent, synchronous Responses calls."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


METHOD_DIR = Path(__file__).resolve().parent
TERRA_DIR = METHOD_DIR.parent / "validity_rl_terra_dataset"
sys.path.insert(0, str(TERRA_DIR))

from annotate import (
    ANSWER_PROMPT_VERSION,
    ANSWER_SYSTEM_PROMPT,
    VALIDITY_PROMPT_VERSION,
    VALIDITY_SYSTEM_PROMPT,
    run_many,
)
from common import atomic_json, prompt_hash, read_jsonl, write_jsonl

from majority_judge import (
    PROMPT_VERSION as MAJORITY_PROMPT_VERSION,
    SYSTEM_PROMPT as MAJORITY_SYSTEM_PROMPT,
    run_majority_pass_sync,
)


def missing_majority_answer(value: object) -> bool:
    return not isinstance(value, str) or value.strip().lower() in {"", "none", "null", "n/a"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--sampled", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model", default="gpt-5.6-terra")
    parser.add_argument(
        "--reasoning-effort", choices=("low", "medium", "high", "xhigh", "max"),
        default="high",
    )
    parser.add_argument("--max-output-tokens", type=int, default=16384)
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--min-confidence", type=float, default=0.8)
    parser.add_argument("--concurrency", type=int, default=64)
    args = parser.parse_args()
    args.input = args.input.resolve()
    args.sampled = args.sampled.resolve()
    args.output_dir = args.output_dir.resolve()

    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is required")
    if not 0 <= args.min_confidence <= 1:
        raise ValueError("min-confidence must be in [0, 1]")
    if args.max_attempts < 1:
        raise ValueError("max-attempts must be positive")
    if args.concurrency < 1:
        raise ValueError("concurrency must be positive")

    blind = read_jsonl(args.input)
    sampled = read_jsonl(args.sampled)
    if any(set(item) != {"id", "question"} for item in blind):
        raise ValueError("Terra blind rows must contain exactly id and question")
    blind_by_id = {item["id"]: item for item in blind}
    sampled_by_id = {item["id"]: item for item in sampled}
    if len(blind_by_id) != len(blind) or len(sampled_by_id) != len(sampled):
        raise ValueError("duplicate IDs in inputs")
    if set(blind_by_id) != set(sampled_by_id):
        raise ValueError("blind and sampled ID sets differ")
    if any(
        blind_by_id[item_id]["question"] != row["question"]
        for item_id, row in sampled_by_id.items()
    ):
        raise ValueError("blind and sampled question text differs")

    validity = run_many(
        blind, "validity", args.output_dir / "artifacts" / "validity", args.model,
        args.concurrency, args.max_attempts, args.min_confidence,
        args.reasoning_effort, args.max_output_tokens, None,
    )
    valid_items = [
        blind_by_id[row["id"]]
        for row in validity
        if row["status"] == "complete" and row["result"]["label"] == "A"
    ]
    answers = run_many(
        valid_items, "answer", args.output_dir / "artifacts" / "answer", args.model,
        args.concurrency, args.max_attempts, args.min_confidence,
        args.reasoning_effort, args.max_output_tokens, None,
    )
    answer_by_id = {row["id"]: row for row in answers}

    majority_inputs = []
    for row in answers:
        result = row.get("result") or {}
        majority = sampled_by_id[row["id"]]["majority_answer"]
        if (
            row["status"] == "complete"
            and result.get("answer_verified") is True
            and isinstance(result.get("canonical_final_answer"), str)
            and result["canonical_final_answer"].strip()
            and not missing_majority_answer(majority)
        ):
            majority_inputs.append({
                "id": row["id"],
                "question": blind_by_id[row["id"]]["question"],
                "canonical_final_answer": result["canonical_final_answer"],
                "majority_answer": majority,
            })
    majority_inputs.sort(key=lambda row: row["id"])
    write_jsonl(args.output_dir / "majority_blind_input.jsonl", majority_inputs)
    majority_results = run_majority_pass_sync(
        majority_inputs, args.output_dir, args.model, args.reasoning_effort,
        args.max_output_tokens, args.max_attempts, args.min_confidence, args.concurrency,
    )
    majority_by_id = {row["id"]: row for row in majority_results}

    combined = [{
        "id": row["id"],
        "validity_pass": row,
        "answer_pass": answer_by_id.get(row["id"]),
        "majority_pass": majority_by_id.get(row["id"]),
    } for row in validity]
    write_jsonl(args.output_dir / "terra_raw_results.jsonl", combined)
    atomic_json(args.output_dir / "annotation_manifest.json", {
        "annotation_mode": "responses_api_sync",
        "endpoint": "/v1/responses",
        "model": args.model,
        "concurrency": args.concurrency,
        "reasoning_effort": args.reasoning_effort,
        "max_output_tokens": args.max_output_tokens,
        "max_attempts": args.max_attempts,
        "min_confidence": args.min_confidence,
        "input_count": len(blind),
        "answer_pass_input_count": len(valid_items),
        "majority_pass_input_count": len(majority_inputs),
        "validity_prompt_version": VALIDITY_PROMPT_VERSION,
        "validity_prompt_sha256": prompt_hash(VALIDITY_SYSTEM_PROMPT),
        "validity_system_prompt": VALIDITY_SYSTEM_PROMPT,
        "answer_prompt_version": ANSWER_PROMPT_VERSION,
        "answer_prompt_sha256": prompt_hash(ANSWER_SYSTEM_PROMPT),
        "answer_system_prompt": ANSWER_SYSTEM_PROMPT,
        "majority_prompt_version": MAJORITY_PROMPT_VERSION,
        "majority_prompt_sha256": prompt_hash(MAJORITY_SYSTEM_PROMPT),
        "majority_system_prompt": MAJORITY_SYSTEM_PROMPT,
    })
    print(
        f"[annotate:sync] complete: validity={len(validity)} answer={len(answers)} "
        f"majority_judged={len(majority_results)}",
        flush=True,
    )


if __name__ == "__main__":
    main()
