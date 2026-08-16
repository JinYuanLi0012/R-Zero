#!/usr/bin/env python3
"""Acceptance checks for the binary few-shot logprob Judge."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from binary_logprob_common import EXPERIMENT_VERSION, VARIANTS
from common import read_jsonl


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--expected-count", type=int, default=600)
    parser.add_argument("--require-analysis", action="store_true")
    args = parser.parse_args()
    blind = read_jsonl(args.output_dir / "blind_input.jsonl")
    results = read_jsonl(args.output_dir / "binary_logprob_results.jsonl")
    if len(blind) != args.expected_count or any(
        set(row) != {"opaque_binary_judge_id", "question"} for row in blind
    ):
        raise RuntimeError("blind input coverage or fields are invalid")
    expected_results = args.expected_count * len(VARIANTS)
    keys = {(row["question_id"], row["variant"]) for row in results}
    if len(results) != expected_results or len(keys) != expected_results:
        raise RuntimeError("result question/variant coverage is invalid")
    for row in results:
        if row.get("status") != "success" or row.get("experiment_version") != EXPERIMENT_VERSION:
            raise RuntimeError("result is incomplete or from a different experiment version")
        if row["verdict"] not in {"VALID", "INVALID"}:
            raise RuntimeError("invalid binary verdict")
        probability = float(row["valid_score"])
        if not math.isfinite(probability) or not 0 <= probability <= 1:
            raise RuntimeError("invalid paired probability")
        for field in ("valid_logprob", "invalid_logprob", "logprob_margin_valid_minus_invalid"):
            if not math.isfinite(float(row[field])):
                raise RuntimeError(f"non-finite {field}")
        if not row["valid_candidate_token_ids"] or not row["invalid_candidate_token_ids"]:
            raise RuntimeError("candidate token IDs were not saved")
    raw_count = sum(len(list((args.output_dir / "raw" / variant).glob("*.json"))) for variant in VARIANTS)
    if raw_count != expected_results:
        raise RuntimeError(f"expected {expected_results} raw artifacts, found {raw_count}")
    manifest = json.loads((args.output_dir / "binary_logprob_manifest.json").read_text(encoding="utf-8"))
    if manifest["question_count"] != args.expected_count or manifest["result_count"] != expected_results:
        raise RuntimeError("manifest count mismatch")
    if args.require_analysis:
        for name in ("metrics.json", "binary_metrics.csv", "confusion_matrices.csv",
                     "round_valid_rates.csv", "prompt_disagreements.csv",
                     "generation_diagnostics.csv", "report.md"):
            if not (args.output_dir / "analysis" / name).is_file():
                raise RuntimeError(f"missing analysis artifact: {name}")
    print(f"Binary logprob Judge verification passed: {args.expected_count} questions x {len(VARIANTS)} variants")


if __name__ == "__main__":
    main()
