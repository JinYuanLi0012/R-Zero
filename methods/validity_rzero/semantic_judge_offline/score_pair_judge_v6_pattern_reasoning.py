#!/usr/bin/env python3
"""Score the v6 exercise-pattern brief-reasoning diagnostic."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from run_pair_judge import atomic_json, atomic_jsonl
from score_pair_judge import read_jsonl
from score_pair_judge_v3 import analyze, make_report, validate_and_join


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--blind", type=Path, required=True)
    parser.add_argument("--gold", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--expected-count", type=int, default=50)
    args = parser.parse_args()
    blind = read_jsonl(args.blind)
    joined = validate_and_join(
        blind, read_jsonl(args.gold), read_jsonl(args.predictions), args.expected_count
    )
    metrics, errors, disagreements = analyze(
        joined, [str(row["pair_id"]) for row in blind]
    )
    metrics["evaluation_status"] = "diagnostic_v6_pattern_reasoning_not_held_out"
    args.output_dir.mkdir(parents=True, exist_ok=True)
    atomic_json(args.output_dir / "metrics_v6_pattern_reasoning.json", metrics)
    atomic_jsonl(args.output_dir / "errors_v6_pattern_reasoning.jsonl", errors)
    atomic_jsonl(
        args.output_dir / "order_disagreements_v6_pattern_reasoning.jsonl",
        disagreements,
    )
    report = make_report(metrics, errors, disagreements).replace(
        "Generative-v3/vLLM semantic judge",
        "V6 exercise-pattern brief-reasoning semantic judge",
    )
    (args.output_dir / "report_v6_pattern_reasoning.md").write_text(
        report, encoding="utf-8"
    )
    print(json.dumps(metrics, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
