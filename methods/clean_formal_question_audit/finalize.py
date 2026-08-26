#!/usr/bin/env python3
"""Join Terra results to source vote metadata and produce audit statistics."""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


METHOD_DIR = Path(__file__).resolve().parent
TERRA_DIR = METHOD_DIR.parent / "validity_rl_terra_dataset"
sys.path.insert(0, str(TERRA_DIR))

from common import atomic_json, read_jsonl, write_jsonl


JUDGED_OUTCOMES = {"CORRECT", "INCORRECT", "INCOMPLETE", "NOT_RESPONSIVE"}


def missing_majority_answer(value: object) -> bool:
    return not isinstance(value, str) or value.strip().lower() in {"", "none", "null", "n/a"}


def safe_divide(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def unique_by_id(rows: list[dict[str, Any]], name: str) -> dict[str, dict[str, Any]]:
    result = {row["id"]: row for row in rows}
    if len(result) != len(rows):
        raise ValueError(f"{name} contains duplicate IDs")
    return result


def classify(annotation: dict[str, Any], source: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    failures: list[str] = []
    validity_pass = annotation.get("validity_pass") or {}
    validity_result = validity_pass.get("result") or {}
    label = validity_result.get("label") if validity_pass.get("status") == "complete" else None
    if label == "A":
        terra_validity = "VALID"
    elif label in {"B", "C", "D", "E", "F"}:
        terra_validity = "INVALID"
    else:
        terra_validity = "UNKNOWN"
        failures.append("VALIDITY_PARSE_FAILURE")

    answer_pass = annotation.get("answer_pass")
    answer_result = (answer_pass or {}).get("result") or {}
    reference_verified = bool(
        terra_validity == "VALID" and answer_pass
        and answer_pass.get("status") == "complete"
        and answer_result.get("answer_verified") is True
        and isinstance(answer_result.get("canonical_final_answer"), str)
        and answer_result["canonical_final_answer"].strip()
    )
    if terra_validity != "VALID":
        reference_status = "NOT_APPLICABLE"
    elif reference_verified:
        reference_status = "VERIFIED"
    elif answer_pass and answer_pass.get("status") == "uncertain":
        reference_status = "UNCERTAIN"
        failures.append("CANONICAL_ANSWER_UNCERTAIN")
    else:
        reference_status = "PARSE_FAILURE"
        failures.append("CANONICAL_ANSWER_PARSE_FAILURE")

    majority_pass = annotation.get("majority_pass")
    majority_result = (majority_pass or {}).get("result") or {}
    majority_missing = missing_majority_answer(source.get("majority_answer"))
    if terra_validity == "INVALID":
        majority_outcome = "NOT_APPLICABLE_INVALID"
    elif terra_validity != "VALID":
        majority_outcome = "NOT_APPLICABLE_UNKNOWN_VALIDITY"
    elif not reference_verified:
        majority_outcome = "REFERENCE_UNAVAILABLE"
    elif majority_missing:
        majority_outcome = "MISSING"
        failures.append("MISSING_MAJORITY_ANSWER")
    elif not majority_pass or majority_pass.get("status") != "complete":
        majority_outcome = (
            "JUDGE_UNCERTAIN" if majority_pass and majority_pass.get("status") == "uncertain"
            else "JUDGE_PARSE_FAILURE"
        )
        failures.append(f"MAJORITY_{majority_outcome}")
    else:
        majority_outcome = majority_result["majority_answer_status"]

    output = {
        **source,
        "terra_validity": terra_validity,
        "terra_label": label,
        "terra_confidence": validity_result.get("confidence"),
        "terra_invalid_type": validity_result.get("invalid_type"),
        "terra_reasoning_summary": validity_result.get("reasoning_summary"),
        "canonical_final_answer": (
            answer_result.get("canonical_final_answer") if reference_verified else None
        ),
        "canonical_answer_status": reference_status,
        "canonical_answer_verified": reference_verified,
        "canonical_answer_confidence": answer_result.get("confidence"),
        "majority_answer_outcome": majority_outcome,
        "majority_answer_correct": majority_outcome == "CORRECT",
        "majority_judge_confidence": majority_result.get("confidence"),
        "majority_judge_reasoning_summary": majority_result.get("reasoning_summary"),
        "majority_mathematically_equivalent": majority_result.get("mathematically_equivalent"),
    }
    return output, failures


def accuracy_block(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = list(rows)
    reference = [row for row in rows if row["canonical_answer_verified"]]
    present = [row for row in reference if row["majority_answer_outcome"] != "MISSING"]
    judged = [row for row in reference if row["majority_answer_outcome"] in JUDGED_OUTCOMES]
    correct = [row for row in reference if row["majority_answer_outcome"] == "CORRECT"]
    return {
        "sampled": len(rows),
        "terra_valid": sum(row["terra_validity"] == "VALID" for row in rows),
        "terra_invalid": sum(row["terra_validity"] == "INVALID" for row in rows),
        "terra_unknown": sum(row["terra_validity"] == "UNKNOWN" for row in rows),
        "terra_valid_rate": safe_divide(
            sum(row["terra_validity"] == "VALID" for row in rows),
            sum(row["terra_validity"] in {"VALID", "INVALID"} for row in rows),
        ),
        "verified_reference_count": len(reference),
        "majority_answer_present_count": len(present),
        "majority_judged_count": len(judged),
        "majority_correct_count": len(correct),
        "majority_strict_accuracy": safe_divide(len(correct), len(reference)),
        "majority_judged_accuracy": safe_divide(len(correct), len(judged)),
        "majority_answer_coverage": safe_divide(len(present), len(reference)),
        "majority_judge_coverage": safe_divide(len(judged), len(reference)),
    }


def bucket_score(value: Any) -> str:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return "missing"
    numerator = round(float(value) * 9)
    return f"{numerator}/9"


def grouped_accuracy(
    rows: list[dict[str, Any]], key_function,
) -> dict[str, dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(key_function(row))].append(row)
    return {key: accuracy_block(value) for key, value in sorted(groups.items())}


def percentage(value: float | None) -> str:
    return "n/a" if value is None else f"{100 * value:.2f}%"


def make_report(stats: dict[str, Any]) -> str:
    overall = stats["overall"]
    sampled_label = (
        "Sampled raw rows"
        if stats["sampling_protocol"]["sampling_unit"] == "raw_row"
        else "Sampled questions"
    )
    round_names = sorted(stats["by_round"], key=lambda value: int(value[1:]))
    round_title = "–".join(value.upper() for value in (round_names[0], round_names[-1]))
    if len(round_names) == 1:
        round_title = round_names[0].upper()
    lines = [
        f"# Clean-formal {round_title} question validity and majority-answer audit",
        "", "## Accounting", "",
        f"- Sampling unit: {stats['sampling_protocol']['sampling_unit']}",
        f"- Deduplication: {stats['sampling_protocol']['deduplication']}",
        f"- {sampled_label}: {overall['sampled']}",
        f"- Terra VALID / INVALID / UNKNOWN: {overall['terra_valid']} / "
        f"{overall['terra_invalid']} / {overall['terra_unknown']}",
        f"- Terra valid rate: {percentage(overall['terra_valid_rate'])}",
        f"- Verified canonical references: {overall['verified_reference_count']}",
        f"- Majority answers present: {overall['majority_answer_present_count']}",
        f"- Majority answers successfully judged: {overall['majority_judged_count']}",
        f"- Majority answers correct: {overall['majority_correct_count']}",
        f"- Strict majority accuracy: {percentage(overall['majority_strict_accuracy'])}",
        f"- Judged-answer accuracy: {percentage(overall['majority_judged_accuracy'])}",
        f"- Majority answer coverage: {percentage(overall['majority_answer_coverage'])}",
        f"- Majority judge coverage: {percentage(overall['majority_judge_coverage'])}",
        "", "Strict accuracy uses every Terra-VALID question with a verified canonical answer as the "
        "denominator; missing or unjudgeable majority answers are not counted as correct. Judged-answer "
        "accuracy includes only CORRECT/INCORRECT/INCOMPLETE/NOT_RESPONSIVE outcomes.",
        "", "## Per-round results", "",
        "| Round | Sampled | VALID | Invalid | Valid rate | Verified ref | Present | Judged | Correct | Strict acc. | Judged acc. |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for round_name in round_names:
        row = stats["by_round"][round_name]
        lines.append(
            f"| {round_name.upper()} | {row['sampled']} | {row['terra_valid']} | "
            f"{row['terra_invalid']} | {percentage(row['terra_valid_rate'])} | "
            f"{row['verified_reference_count']} | {row['majority_answer_present_count']} | "
            f"{row['majority_judged_count']} | {row['majority_correct_count']} | "
            f"{percentage(row['majority_strict_accuracy'])} | "
            f"{percentage(row['majority_judged_accuracy'])} |"
        )
    lines.extend([
        "", "## Source validity vote vs. Terra", "",
        f"- Agreement: {stats['source_validity_comparison']['agreement_count']} / "
        f"{stats['source_validity_comparison']['comparable_count']} "
        f"({percentage(stats['source_validity_comparison']['agreement_rate'])})",
        "", "| Source decision | Terra VALID | Terra INVALID | Terra UNKNOWN |",
        "|---|---:|---:|---:|",
    ])
    matrix = stats["source_validity_comparison"]["confusion_matrix"]
    for source in ("VALID", "INVALID"):
        lines.append(
            f"| {source} | {matrix.get(source, {}).get('VALID', 0)} | "
            f"{matrix.get(source, {}).get('INVALID', 0)} | "
            f"{matrix.get(source, {}).get('UNKNOWN', 0)} |"
        )
    lines.extend(["", "## Majority-answer outcomes", ""])
    for key, value in sorted(stats["majority_outcome_counts"].items()):
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Terra INVALID types", ""])
    for key, value in sorted(stats["invalid_type_counts"].items()):
        lines.append(f"- {key}: {value}")
    lines.extend([
        "", "## Accuracy by original solver support", "",
        "| Support | Verified ref | Judged | Correct | Strict acc. | Judged acc. |",
        "|---|---:|---:|---:|---:|---:|",
    ])
    score_order = sorted(
        stats["by_solver_score"],
        key=lambda key: (-1 if key == "missing" else int(key.split("/")[0])),
    )
    for key in score_order:
        row = stats["by_solver_score"][key]
        lines.append(
            f"| {key} | {row['verified_reference_count']} | {row['majority_judged_count']} | "
            f"{row['majority_correct_count']} | {percentage(row['majority_strict_accuracy'])} | "
            f"{percentage(row['majority_judged_accuracy'])} |"
        )
    lines.extend([
        "", "## Accuracy by original R-Zero filter", "",
        "| Passed filter | Sampled | Verified ref | Judged | Correct | Strict acc. | Judged acc. |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ])
    for key in ("true", "false"):
        row = stats["by_source_passed_rzero_filter"].get(key)
        if row is None:
            continue
        lines.append(
            f"| {key} | {row['sampled']} | {row['verified_reference_count']} | "
            f"{row['majority_judged_count']} | {row['majority_correct_count']} | "
            f"{percentage(row['majority_strict_accuracy'])} | "
            f"{percentage(row['majority_judged_accuracy'])} |"
        )
    lines.extend([
        "", "## Failures and uncertainty", "",
        f"- Rows in failed_or_uncertain.jsonl: {stats['failed_or_uncertain_count']}",
    ])
    for key, value in sorted(stats["failure_reason_counts"].items()):
        lines.append(f"- {key}: {value}")
    return "\n".join(lines) + "\n"


def finalize(output_dir: Path) -> dict[str, Any]:
    sampled = read_jsonl(output_dir / "sampled_questions.jsonl")
    raw = read_jsonl(output_dir / "terra_raw_results.jsonl")
    prepare_manifest = json.loads((output_dir / "prepare_manifest.json").read_text(encoding="utf-8"))
    sampled_by_id = unique_by_id(sampled, "sampled_questions")
    raw_by_id = unique_by_id(raw, "terra_raw_results")
    if set(sampled_by_id) != set(raw_by_id):
        raise ValueError("sampled and Terra result ID sets differ")

    annotated = []
    failures = []
    reason_counts: Counter[str] = Counter()
    for source in sampled:
        row, reasons = classify(raw_by_id[source["id"]], source)
        annotated.append(row)
        if reasons:
            reason_counts.update(reasons)
            failures.append({**row, "failure_reasons": reasons})
    write_jsonl(output_dir / "annotated_sample.jsonl", annotated)
    write_jsonl(output_dir / "failed_or_uncertain.jsonl", failures)

    matrix: dict[str, Counter[str]] = defaultdict(Counter)
    comparable = agreement = 0
    for row in annotated:
        source = row["source_validity_decision"]
        terra = row["terra_validity"]
        matrix[source][terra] += 1
        if terra in {"VALID", "INVALID"}:
            comparable += 1
            agreement += int(source == terra)
    stats = {
        "sampling_protocol": {
            "sampling_unit": prepare_manifest.get("sampling_unit", "legacy_unique_question"),
            "deduplication": prepare_manifest.get("deduplication", "legacy/unspecified"),
        },
        "overall": accuracy_block(annotated),
        "by_round": grouped_accuracy(annotated, lambda row: row["round"]),
        "by_solver_score": grouped_accuracy(annotated, lambda row: bucket_score(row["solver_score"])),
        "by_source_passed_rzero_filter": grouped_accuracy(
            annotated, lambda row: str(bool(row["source_passed_rzero_filter"])).lower()
        ),
        "source_validity_comparison": {
            "confusion_matrix": {
                source: dict(counts) for source, counts in sorted(matrix.items())
            },
            "comparable_count": comparable, "agreement_count": agreement,
            "agreement_rate": safe_divide(agreement, comparable),
        },
        "terra_label_counts": dict(Counter(row["terra_label"] or "PARSE_FAILURE" for row in annotated)),
        "invalid_type_counts": dict(Counter(
            row["terra_invalid_type"] for row in annotated if row["terra_validity"] == "INVALID"
        )),
        "canonical_answer_status_counts": dict(Counter(
            row["canonical_answer_status"] for row in annotated
        )),
        "majority_outcome_counts": dict(Counter(
            row["majority_answer_outcome"] for row in annotated
        )),
        "failed_or_uncertain_count": len(failures),
        "failure_reason_counts": dict(reason_counts),
    }
    analysis_dir = output_dir / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    atomic_json(analysis_dir / "dataset_statistics.json", stats)
    report = make_report(stats)
    temporary = analysis_dir / f"report.md.tmp-{os.getpid()}"
    temporary.write_text(report, encoding="utf-8")
    os.replace(temporary, analysis_dir / "report.md")

    annotation_manifest = json.loads(
        (output_dir / "annotation_manifest.json").read_text(encoding="utf-8")
    )
    atomic_json(output_dir / "manifest.json", {
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "sampling_unit": prepare_manifest.get("sampling_unit", "legacy_unique_question"),
        "deduplication": prepare_manifest.get("deduplication", "legacy/unspecified"),
        "prepare": prepare_manifest, "annotation": annotation_manifest,
        "statistics": stats,
    })
    print(
        f"[finalize] complete: sampled={len(annotated)} "
        f"valid={stats['overall']['terra_valid']} "
        f"strict_accuracy={percentage(stats['overall']['majority_strict_accuracy'])} "
        f"failed_or_uncertain={len(failures)}",
        flush=True,
    )
    return stats


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    finalize(args.output_dir.resolve())


if __name__ == "__main__":
    main()
