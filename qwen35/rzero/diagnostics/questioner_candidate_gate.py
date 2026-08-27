"""Adapt step-1 raw Questioner records and summarize the official n=9 gate."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from qwen35.rzero.curate_dataset import filter_candidates
from qwen35.rzero.generate_candidates import atomic_json


def prepare_candidates(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Recreate the unchanged generate_candidates output schema from raw diagnostics."""

    candidates = []
    for record in records:
        question = str(record.get("parsed_question") or "")
        answer = str(record.get("parsed_answer") or "")
        raw_response = str(record.get("raw_response") or "")
        valid = bool(question and answer)
        candidates.append(
            {
                "question": question or raw_response,
                "answer": answer,
                "score": 0 if valid else -1,
            }
        )
    return candidates


def summarize_gate(
    candidates: list[dict[str, Any]],
    scored: list[dict[str, Any]],
    minimum: float = 0.3,
    maximum: float = 0.8,
) -> dict[str, Any]:
    parseable = sum(item.get("score") == 0 for item in candidates)
    majority_none = sum(item.get("answer") == "None" for item in scored)
    accepted, accepted_before_deduplication, _ = filter_candidates(
        scored,
        minimum,
        maximum,
        deduplicate_questions=False,
    )
    score_histogram = Counter(round(float(item["score"]), 6) for item in scored)
    result_lengths = Counter(len(item.get("results") or []) for item in scored)
    return {
        "total_candidates": len(candidates),
        "parseable_candidates": parseable,
        "scored_candidates": len(scored),
        "dropped_during_evaluation": parseable - len(scored),
        "majority_none": majority_none,
        "difficulty_min": minimum,
        "difficulty_max": maximum,
        "accepted_0.3_to_0.8": accepted_before_deduplication,
        "accepted_fraction_of_scored": (
            accepted_before_deduplication / len(scored) if scored else 0.0
        ),
        "accepted_fraction_of_total": (
            accepted_before_deduplication / len(candidates) if candidates else 0.0
        ),
        "accepted_questions": [item["question"] for item in accepted],
        "score_histogram": {str(key): value for key, value in sorted(score_histogram.items())},
        "result_lengths": {str(key): value for key, value in sorted(result_lengths.items())},
        "semantics": {
            "solver_samples": 9,
            "deduplication": False,
            "repeat_to_minimum": False,
            "fallback": False,
            "note": "This is a data-viability gate only; it does not create a Solver training Parquet.",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare = subparsers.add_parser("prepare")
    prepare.add_argument("--raw", type=Path, required=True)
    prepare.add_argument("--output", type=Path, required=True)
    summary = subparsers.add_parser("summarize")
    summary.add_argument("--candidates", type=Path, required=True)
    summary.add_argument("--scored", type=Path, required=True)
    summary.add_argument("--output", type=Path, required=True)
    summary.add_argument("--min-score", type=float, default=0.3)
    summary.add_argument("--max-score", type=float, default=0.8)
    args = parser.parse_args()

    if args.command == "prepare":
        records = json.loads(args.raw.read_text(encoding="utf-8"))
        atomic_json(args.output, prepare_candidates(records))
        print(f"candidate_output={args.output}")
        return

    candidates = json.loads(args.candidates.read_text(encoding="utf-8"))
    scored = json.loads(args.scored.read_text(encoding="utf-8"))
    atomic_json(args.output, summarize_gate(candidates, scored, args.min_score, args.max_score))
    print(f"summary_output={args.output}")


if __name__ == "__main__":
    main()
