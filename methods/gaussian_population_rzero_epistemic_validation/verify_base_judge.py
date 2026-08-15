#!/usr/bin/env python3
"""Acceptance checks for a completed Base Judge run."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from base_judge_common import LABELS
from common import read_jsonl


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--expected-count", type=int, default=600)
    parser.add_argument("--require-analysis", action="store_true")
    args = parser.parse_args()
    blind = read_jsonl(args.output_dir / "blind_input.jsonl")
    results = read_jsonl(args.output_dir / "base_judge_results.jsonl")
    if len(blind) != args.expected_count or any(
        set(row) != {"opaque_base_judge_id", "question"} for row in blind
    ):
        raise RuntimeError("blind input coverage or fields are invalid")
    if len(results) != args.expected_count or len({r["question_id"] for r in results}) != len(results):
        raise RuntimeError("result coverage is invalid")
    for row in results:
        if row["status"] not in {"success", "final_parse_failure"}:
            raise RuntimeError("result is neither parsed nor an explicit final failure")
        if row["status"] == "success" and (
            row["label"] not in LABELS or not 0 <= float(row["probability_label_A"]) <= 1
        ):
            raise RuntimeError("successful result has invalid structured fields")
    raw = list((args.output_dir / "raw").glob("*.json"))
    if len(raw) != args.expected_count:
        raise RuntimeError(f"expected {args.expected_count} raw artifacts, found {len(raw)}")
    manifest = json.loads((args.output_dir / "base_judge_manifest.json").read_text(encoding="utf-8"))
    if manifest["question_count"] != args.expected_count:
        raise RuntimeError("manifest count mismatch")
    if args.require_analysis:
        for name in ("metrics.json", "binary_metrics.csv", "af_confusion.csv",
                     "round_valid_rates.csv", "disagreements.csv", "report.md"):
            if not (args.output_dir / "analysis" / name).is_file():
                raise RuntimeError(f"missing analysis artifact: {name}")
    print(f"Base Judge verification passed: {args.expected_count} questions")


if __name__ == "__main__":
    main()
