#!/usr/bin/env python3
"""Import blind human labels and report agreement with GPT reference judgments."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from sklearn.metrics import cohen_kappa_score

from common import atomic_json, read_jsonl


def read_human_results(path: Path) -> list[dict]:
    if path.suffix.lower() == ".csv":
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))
    return read_jsonl(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--human-results", type=Path, required=True)
    parser.add_argument("--private-key", type=Path, required=True)
    parser.add_argument("--judge-results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    human = {row["human_review_id"]: row for row in read_human_results(args.human_results)}
    keys = read_jsonl(args.private_key)
    judge = {row["question_id"]: row for row in read_jsonl(args.judge_results)}
    pairs = []
    for key in keys:
        label = str(human.get(key["human_review_id"], {}).get("human_label", "")).strip().upper()
        if label:
            if label not in {"A", "B", "C", "D", "E", "F"}:
                raise ValueError(f"invalid human label {label!r}")
            pairs.append((label, judge[key["question_id"]]["label"]))
    if not pairs:
        raise RuntimeError("no completed human labels found")
    atomic_json(
        args.output,
        {
            "labeled_count": len(pairs),
            "exact_agreement": sum(left == right for left, right in pairs) / len(pairs),
            "cohen_kappa": float(cohen_kappa_score([x[0] for x in pairs], [x[1] for x in pairs])),
            "validity_agreement": sum((x[0] == "A") == (x[1] == "A") for x in pairs) / len(pairs),
        },
    )


if __name__ == "__main__":
    main()
