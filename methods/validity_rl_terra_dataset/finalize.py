#!/usr/bin/env python3
"""Join blind annotations to private metadata and produce RL-ready files and reports."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from common import atomic_json, read_jsonl, write_jsonl


def increment_nested(counter: dict[str, Counter], key: str, value: str) -> None:
    counter[key][value] += 1


def finalize(sampled: list[dict[str, Any]], raw: list[dict[str, Any]]) -> tuple[
    list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]
]:
    raw_by_id = {row["id"]: row for row in raw}
    if len(raw_by_id) != len(raw):
        raise ValueError("terra_raw_results contains duplicate IDs")
    expected_ids = {row["id"] for row in sampled}
    if set(raw_by_id) != expected_ids:
        missing, extra = expected_ids - set(raw_by_id), set(raw_by_id) - expected_ids
        raise ValueError(f"annotation/sample ID mismatch: missing={len(missing)}, extra={len(extra)}")

    eligible: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []
    validity = Counter()
    validity_by_split: dict[str, Counter] = defaultdict(Counter)
    validity_by_round: dict[str, Counter] = defaultdict(Counter)
    invalid_types = Counter()
    answer_outcomes = Counter()
    parse_failures = 0

    for source in sampled:
        annotation = raw_by_id[source["id"]]
        validity_pass = annotation["validity_pass"]
        if validity_pass["status"] != "complete" or validity_pass["result"] is None:
            parse_failures += 1
            failed.append({**source, "failure_stage": "validity", "terra_raw": annotation})
            continue
        judgment = validity_pass["result"]
        is_valid = judgment["label"] == "A"
        validity_label = "VALID" if is_valid else "INVALID"
        validity[validity_label] += 1
        increment_nested(validity_by_split, source["split"], validity_label)
        increment_nested(validity_by_round, source["round"], validity_label)

        if not is_valid:
            invalid_types[judgment["invalid_type"]] += 1
            eligible.append({
                "id": source["id"], "round": source["round"], "question": source["question"],
                "terra_validity": "INVALID", "canonical_final_answer": None,
                "answer_verified": None, "invalid_type": judgment["invalid_type"],
                "split": source["split"], "terra_label": judgment["label"],
                "validity_rl_target": "INVALID",
            })
            continue

        answer_pass = annotation["answer_pass"]
        if answer_pass is None or answer_pass["status"] != "complete" or answer_pass["result"] is None:
            outcome = "parse_failure" if answer_pass is None or answer_pass["status"] == "failed" else "uncertain"
            answer_outcomes[outcome] += 1
            if outcome == "parse_failure":
                parse_failures += 1
            failed.append({**source, "failure_stage": "answer", "failure_type": outcome,
                           "terra_validity": "VALID", "terra_raw": annotation})
            continue
        answer = answer_pass["result"]
        answer_outcomes["verified"] += 1
        eligible.append({
            "id": source["id"], "round": source["round"], "question": source["question"],
            "terra_validity": "VALID", "canonical_final_answer": answer["canonical_final_answer"],
            "answer_verified": True, "answer_confidence": answer["confidence"],
            "invalid_type": None, "split": source["split"], "terra_label": "A",
            "validity_rl_target": answer["canonical_final_answer"],
        })

    train = sorted((row for row in eligible if row["split"] == "train"), key=lambda row: row["id"])
    validation = sorted((row for row in eligible if row["split"] == "validation"), key=lambda row: row["id"])
    sampled_splits = Counter(row["split"] for row in sampled)
    sampled_rounds = Counter(row["round"] for row in sampled)
    stats = {
        "total_terra_annotation_questions": len(sampled),
        "sampled_split_counts": dict(sorted(sampled_splits.items())),
        "sampled_round_counts": dict(sorted(sampled_rounds.items())),
        "terra_validity_counts": dict(validity),
        "terra_validity_rates": {
            key: value / sum(validity.values()) if validity else None for key, value in validity.items()
        },
        "validity_by_split": {key: dict(value) for key, value in sorted(validity_by_split.items())},
        "validity_by_round": {key: dict(value) for key, value in sorted(validity_by_round.items())},
        "valid_rate_by_round": {
            key: value["VALID"] / sum(value.values()) if value else None
            for key, value in sorted(validity_by_round.items())
        },
        "valid_answer_outcomes": dict(answer_outcomes),
        "terra_parse_failures": parse_failures,
        "invalid_type_counts": dict(invalid_types),
        "rl_eligible_train": len(train),
        "rl_eligible_validation": len(validation),
        "failed_or_uncertain": len(failed),
    }
    return train, validation, failed, stats


def render_report(stats: dict[str, Any]) -> str:
    counts = stats["terra_validity_counts"]
    judged = sum(counts.values())
    valid = counts.get("VALID", 0)
    invalid = counts.get("INVALID", 0)
    lines = [
        "# R-Zero Validity-RL Terra dataset report", "",
        "## Dataset accounting", "",
        f"- Total Terra annotation questions: {stats['total_terra_annotation_questions']}",
        f"- Sampled train / validation: {stats['sampled_split_counts'].get('train', 0)} / "
        f"{stats['sampled_split_counts'].get('validation', 0)}",
        f"- RL-eligible train / validation: {stats['rl_eligible_train']} / {stats['rl_eligible_validation']}",
        f"- VALID: {valid} ({valid / judged:.2%})" if judged else "- VALID: 0",
        f"- INVALID: {invalid} ({invalid / judged:.2%})" if judged else "- INVALID: 0",
        f"- Failed or uncertain: {stats['failed_or_uncertain']}",
        f"- Terra parse failures: {stats['terra_parse_failures']}", "",
        "The sampled split remains fixed before annotation. RL-eligible counts can be smaller because an A-label",
        "question is excluded when its canonical answer cannot be verified reliably.", "",
        "## Per-round validity", "",
        "| Round | Sampled | VALID | INVALID | Valid rate |", "|---|---:|---:|---:|---:|",
    ]
    for round_name, sampled_count in stats["sampled_round_counts"].items():
        row = stats["validity_by_round"].get(round_name, {})
        rate = stats["valid_rate_by_round"].get(round_name)
        lines.append(
            f"| {round_name.upper()} | {sampled_count} | {row.get('VALID', 0)} | "
            f"{row.get('INVALID', 0)} | {rate:.2%} |" if rate is not None else
            f"| {round_name.upper()} | {sampled_count} | 0 | 0 | n/a |"
        )
    lines.extend(["", "## Split validity", "", "| Split | VALID | INVALID |", "|---|---:|---:|"])
    for split, row in stats["validity_by_split"].items():
        lines.append(f"| {split} | {row.get('VALID', 0)} | {row.get('INVALID', 0)} |")
    lines.extend(["", "## VALID answer verification", ""])
    for key in ("verified", "uncertain", "parse_failure"):
        lines.append(f"- {key}: {stats['valid_answer_outcomes'].get(key, 0)}")
    lines.extend(["", "## INVALID types", ""])
    for key, value in sorted(stats["invalid_type_counts"].items()):
        lines.append(f"- {key}: {value}")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    print(f"[finalize] reading annotations from {args.output_dir}", flush=True)
    sampled = read_jsonl(args.output_dir / "sampled_questions.jsonl")
    raw = read_jsonl(args.output_dir / "terra_raw_results.jsonl")
    train, validation, failed, stats = finalize(sampled, raw)
    write_jsonl(args.output_dir / "train.jsonl", train)
    write_jsonl(args.output_dir / "validation.jsonl", validation)
    write_jsonl(args.output_dir / "failed_or_uncertain.jsonl", failed)
    analysis_dir = args.output_dir / "analysis"
    atomic_json(analysis_dir / "dataset_statistics.json", stats)
    analysis_dir.mkdir(parents=True, exist_ok=True)
    (analysis_dir / "report.md").write_text(render_report(stats), encoding="utf-8")

    prepare_manifest = __import__("json").loads(
        (args.output_dir / "prepare_manifest.json").read_text(encoding="utf-8")
    )
    annotation_manifest = __import__("json").loads(
        (args.output_dir / "annotation_manifest.json").read_text(encoding="utf-8")
    )
    atomic_json(args.output_dir / "manifest.json", {
        "source_datasets": prepare_manifest["source_datasets"],
        "sampling_seed": prepare_manifest["sampling_seed"],
        "sampled_count": prepare_manifest["sampled_count"],
        "per_round": prepare_manifest["per_round"],
        "train_per_round": prepare_manifest["train_per_round"],
        "validation_per_round": prepare_manifest["validation_per_round"],
        "terra": annotation_manifest,
        "annotation_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "statistics": stats,
    })
    print(
        f"[finalize] complete: eligible_train={len(train)} "
        f"eligible_validation={len(validation)} failed_or_uncertain={len(failed)}",
        flush=True,
    )


if __name__ == "__main__":
    main()
