"""Summarize the actual verl Questioner rollout dump without changing training."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any

from qwen35.rzero.generate_candidates import atomic_json
from qwen35.rzero.rewards.common import parse_questioner_response


def _stats(values: list[float | int]) -> dict[str, float]:
    if not values:
        return {"mean": 0.0, "median": 0.0, "min": 0.0, "max": 0.0}
    return {
        "mean": float(statistics.fmean(values)),
        "median": float(statistics.median(values)),
        "min": float(min(values)),
        "max": float(max(values)),
    }


def analyze(rows: list[dict[str, Any]], tokenizer: Any, max_tokens: int) -> dict[str, Any]:
    outputs = [str(row["output"]) for row in rows]
    token_counts = [len(tokenizer.encode(text, add_special_tokens=False)) for text in outputs]
    parsed = [parse_questioner_response(text) for text in outputs]
    parse_valid = [bool(item["question"] and item["answer"]) for item in parsed]
    formats = [float(row["format"]) for row in rows]
    difficulties = [float(row["solver_difficulty"]) for row in rows]
    penalties = [float(row["diversity_penalty"]) for row in rows]
    rewards = [float(row["score"]) for row in rows]
    return {
        "total": len(rows),
        "response_tokens_reencoded": _stats(token_counts),
        "hit_max_tokens_reencoded": sum(count >= max_tokens for count in token_counts),
        "parse_valid": sum(parse_valid),
        "reward_format_valid": sum(value > 0.5 for value in formats),
        "literal_final_answer": sum(item["answer"].strip().lower() == "final_answer" for item in parsed),
        "solver_difficulty": _stats(difficulties),
        "solver_difficulty_valid_only": _stats(
            [value for value, valid in zip(difficulties, parse_valid) if valid]
        ),
        "diversity_penalty": _stats(penalties),
        "total_reward": _stats(rewards),
        "notes": {
            "token_counts": "Re-encoded from verl's decoded rollout output; trainer log remains authoritative for exact padded response-length metrics.",
            "raw_rollouts": "The input JSONL is the authoritative per-trajectory record from trainer.rollout_data_dir.",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-rows", type=int, required=True)
    parser.add_argument("--max-tokens", type=int, default=4096)
    args = parser.parse_args()

    rows = [json.loads(line) for line in args.input.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(rows) != args.expected_rows:
        raise RuntimeError(f"rollout dump has {len(rows)} rows, expected {args.expected_rows}")
    required = {"output", "score", "format", "solver_difficulty", "diversity_penalty"}
    for index, row in enumerate(rows):
        missing = required - row.keys()
        if missing:
            raise RuntimeError(f"rollout row {index} is missing reward fields: {sorted(missing)}")

    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(args.model)
    atomic_json(args.output, analyze(rows, tokenizer, args.max_tokens))
    print(f"summary_output={args.output}")


if __name__ == "__main__":
    main()
