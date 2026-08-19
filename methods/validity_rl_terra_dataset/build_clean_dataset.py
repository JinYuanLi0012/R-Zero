#!/usr/bin/env python3
"""Build a conservative clean dataset from consistency and deep-review decisions."""
from __future__ import annotations

import argparse
import hashlib
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from common import atomic_json, read_jsonl, write_jsonl


PRODUCTION_COUNTS = {
    "base_total": 2290, "base_valid": 973, "base_invalid": 1317,
    "audit_pass": 870, "audit_suspect": 113, "deep_keep": 46,
    "clean_total": 2233, "clean_valid": 916, "excluded_valid": 67,
}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.tmp-{os.getpid()}")
    temporary.write_text(value, encoding="utf-8")
    os.replace(temporary, path)


def unique_by_id(rows: list[dict[str, Any]], label: str) -> dict[str, dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for row in rows:
        item_id = row.get("id")
        if not isinstance(item_id, str) or not item_id:
            raise ValueError(f"{label} contains a row without a valid id")
        if item_id in by_id:
            raise ValueError(f"{label} contains duplicate id {item_id}")
        by_id[item_id] = row
    return by_id


def validate_expected(actual: dict[str, int], expected: dict[str, int] | None) -> None:
    if expected is None:
        return
    mismatches = [
        f"{key}: expected {value}, found {actual.get(key)}"
        for key, value in expected.items() if actual.get(key) != value
    ]
    if mismatches:
        raise ValueError("production accounting mismatch: " + "; ".join(mismatches))


def build_clean_rows(
    base_train: list[dict[str, Any]], base_validation: list[dict[str, Any]],
    passed: list[dict[str, Any]], suspects: list[dict[str, Any]],
    deep_results: list[dict[str, Any]],
    expected: dict[str, int] | None = PRODUCTION_COUNTS,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    base_rows = base_train + base_validation
    unique_by_id(base_rows, "base train/validation")
    passed_by_id = unique_by_id(passed, "consistency passed")
    suspect_by_id = unique_by_id(suspects, "consistency suspects")
    deep_by_id = unique_by_id(deep_results, "deep-review results")

    if set(passed_by_id) & set(suspect_by_id):
        raise ValueError("consistency passed and suspect ID sets overlap")
    if set(deep_by_id) != set(suspect_by_id):
        missing = set(suspect_by_id) - set(deep_by_id)
        extra = set(deep_by_id) - set(suspect_by_id)
        raise ValueError(
            f"deep-review/suspect ID mismatch: missing={len(missing)}, extra={len(extra)}"
        )
    if any(row.get("disposition") != "PASS" for row in passed):
        raise ValueError("passed.jsonl contains a non-PASS row")
    if any(row.get("disposition") != "SUSPECT" for row in suspects):
        raise ValueError("suspect.jsonl contains a non-SUSPECT row")
    allowed_actions = {
        "KEEP_CANONICAL", "REPLACEMENT_CANDIDATE", "EXCLUDE", "HUMAN_REVIEW",
    }
    if any(row.get("final_action") not in allowed_actions for row in deep_results):
        raise ValueError("deep-review results contain an unknown or missing final_action")

    for row in base_rows:
        if row.get("split") not in {"train", "validation"}:
            raise ValueError(f"base row {row['id']} has invalid split")
        validity = row.get("terra_validity")
        if validity not in {"VALID", "INVALID"}:
            raise ValueError(f"base row {row['id']} has invalid terra_validity")
        if validity == "VALID":
            if row["id"] not in passed_by_id and row["id"] not in suspect_by_id:
                raise ValueError(f"base VALID row {row['id']} is absent from consistency audit")
        elif row.get("validity_rl_target") != "INVALID":
            raise ValueError(f"base INVALID row {row['id']} has a non-INVALID target")

    base_valid_ids = {row["id"] for row in base_rows if row["terra_validity"] == "VALID"}
    if not set(passed_by_id) <= base_valid_ids:
        raise ValueError("a consistency PASS row is absent from the base VALID dataset")
    keep_review_ids = {
        item_id for item_id, row in deep_by_id.items()
        if row["final_action"] == "KEEP_CANONICAL"
    }
    if not keep_review_ids <= base_valid_ids:
        raise ValueError("a deep-review KEEP row is absent from the base VALID dataset")
    keep_valid_ids = set(passed_by_id) | keep_review_ids
    kept = [
        row for row in base_rows
        if row["terra_validity"] == "INVALID" or row["id"] in keep_valid_ids
    ]
    clean_train = sorted(
        (row for row in kept if row["split"] == "train"), key=lambda row: row["id"]
    )
    clean_validation = sorted(
        (row for row in kept if row["split"] == "validation"), key=lambda row: row["id"]
    )

    excluded = []
    for item_id in sorted(set(suspect_by_id) - keep_review_ids):
        deep, source = deep_by_id[item_id], suspect_by_id[item_id]
        excluded.append({
            "id": item_id, "round": source.get("round"), "split": source.get("split"),
            "question": source.get("question"), "terra_validity": "VALID",
            "canonical_final_answer": source.get("canonical_final_answer"),
            "deep_review_action": deep["final_action"],
            "decision_reasons": deep.get("decision_reasons", []),
            "exclusion_reason": "VALID_NOT_APPROVED_FOR_CLEAN_DATASET",
        })

    validity_counts = Counter(row["terra_validity"] for row in kept)
    split_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for row in kept:
        split_counts[row["split"]][row["terra_validity"]] += 1
    action_counts = Counter(row["final_action"] for row in deep_results)
    actual = {
        "base_total": len(base_rows),
        "base_valid": sum(row["terra_validity"] == "VALID" for row in base_rows),
        "base_invalid": sum(row["terra_validity"] == "INVALID" for row in base_rows),
        "audit_pass": len(passed), "audit_suspect": len(suspects),
        "deep_keep": action_counts["KEEP_CANONICAL"], "clean_total": len(kept),
        "clean_valid": validity_counts["VALID"], "excluded_valid": len(excluded),
    }
    validate_expected(actual, expected)
    stats = {
        **actual, "clean_invalid": validity_counts["INVALID"],
        "clean_train": len(clean_train), "clean_validation": len(clean_validation),
        "clean_by_split": {
            split: dict(sorted(counts.items())) for split, counts in sorted(split_counts.items())
        },
        "deep_review_action_counts": dict(sorted(action_counts.items())),
        "policy": {
            "invalid": "KEEP", "consistency_pass": "KEEP_CANONICAL",
            "deep_review_keep": "KEEP_CANONICAL", "all_other_suspects": "EXCLUDE",
            "replacement_candidates_applied": False,
        },
        "accounting_check": (
            len(clean_train) + len(clean_validation) == len(kept)
            and validity_counts["VALID"] == len(passed) + len(keep_review_ids)
            and len(excluded) + len(keep_review_ids) == len(suspects)
        ),
    }
    return clean_train, clean_validation, excluded, stats


def render_report(stats: dict[str, Any]) -> str:
    return "\n".join([
        "# R-Zero Validity-RL Terra clean dataset v1", "", "## Final accounting", "",
        f"- Clean total: {stats['clean_total']}",
        f"- Train / validation: {stats['clean_train']} / {stats['clean_validation']}",
        f"- VALID retained: {stats['clean_valid']}",
        f"- INVALID retained: {stats['clean_invalid']}",
        f"- VALID excluded: {stats['excluded_valid']}", "",
        "| VALID decision source | Kept |", "|---|---:|",
        f"| Consistency PASS | {stats['audit_pass']} |",
        f"| Sol KEEP_CANONICAL | {stats['deep_keep']} |",
        f"| Total VALID kept | {stats['clean_valid']} |", "", "## Policy", "",
        "All INVALID examples are retained. A VALID example is retained only when it passed the",
        "consistency audit or received the deterministic Sol action KEEP_CANONICAL. Every other",
        "suspect is excluded, including replacement candidates; no canonical answer is replaced.", "",
        "The original train/validation assignment and training-row schema are unchanged. This",
        "builder only writes a new output directory and does not modify the source dataset, upload",
        "to Hugging Face, or start training.", "",
    ])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_dir", type=Path)
    parser.add_argument("audit_dir", type=Path)
    parser.add_argument("deep_review_dir", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--allow-nonstandard-counts", action="store_true")
    args = parser.parse_args()
    resolved = [path.resolve() for path in (
        args.source_dir, args.audit_dir, args.deep_review_dir, args.output_dir,
    )]
    if resolved[3] in resolved[:3]:
        raise ValueError("output directory must differ from every input directory")

    input_paths = {
        "source_train": args.source_dir / "train.jsonl",
        "source_validation": args.source_dir / "validation.jsonl",
        "audit_passed": args.audit_dir / "passed.jsonl",
        "audit_suspect": args.audit_dir / "suspect.jsonl",
        "deep_review_results": args.deep_review_dir / "deep_review_results.jsonl",
    }
    train, validation, excluded, stats = build_clean_rows(
        read_jsonl(input_paths["source_train"]),
        read_jsonl(input_paths["source_validation"]),
        read_jsonl(input_paths["audit_passed"]),
        read_jsonl(input_paths["audit_suspect"]),
        read_jsonl(input_paths["deep_review_results"]),
        None if args.allow_nonstandard_counts else PRODUCTION_COUNTS,
    )
    write_jsonl(args.output_dir / "train.jsonl", train)
    write_jsonl(args.output_dir / "validation.jsonl", validation)
    write_jsonl(args.output_dir / "excluded_valid.jsonl", excluded)
    atomic_json(args.output_dir / "analysis" / "statistics.json", stats)
    report_path = args.output_dir / "analysis" / "report.md"
    atomic_text(report_path, render_report(stats))
    output_paths = {
        "clean_train": args.output_dir / "train.jsonl",
        "clean_validation": args.output_dir / "validation.jsonl",
        "excluded_valid": args.output_dir / "excluded_valid.jsonl",
        "statistics": args.output_dir / "analysis" / "statistics.json",
        "report": report_path,
    }
    atomic_json(args.output_dir / "manifest.json", {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "builder": "build_clean_dataset.py",
        "source_dirs": {
            "dataset": str(args.source_dir.resolve()),
            "consistency_audit": str(args.audit_dir.resolve()),
            "deep_review": str(args.deep_review_dir.resolve()),
        },
        "input_sha256": {name: file_sha256(path) for name, path in input_paths.items()},
        "output_sha256": {name: file_sha256(path) for name, path in output_paths.items()},
        "statistics": stats,
    })
    print(
        f"[clean-dataset] total={stats['clean_total']} train={len(train)} "
        f"validation={len(validation)} valid={stats['clean_valid']} "
        f"invalid={stats['clean_invalid']} excluded_valid={len(excluded)} "
        f"report={report_path}", flush=True,
    )


if __name__ == "__main__":
    main()
