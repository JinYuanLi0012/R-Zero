#!/usr/bin/env python3
"""Score generative-v2 semantic-pair outputs as a diagnostic rerun."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from run_pair_judge import atomic_json, atomic_jsonl
from run_pair_judge_v2 import parse_response
from score_pair_judge import read_jsonl, safe_rate


ORDERS = ("q1_q2", "q2_q1")
SEMANTIC_LABELS = ("SAME_TYPE", "DIFFERENT")
PREDICTION_LABELS = (*SEMANTIC_LABELS, "FORMAT_ERROR")


def key(row: dict[str, Any]) -> tuple[str, str]:
    return str(row["pair_id"]), str(row["question_order"])


def validate_and_join(
    blind_rows: list[dict[str, Any]],
    gold_rows: list[dict[str, Any]],
    prediction_rows: list[dict[str, Any]],
    expected_count: int,
) -> list[dict[str, Any]]:
    if len(blind_rows) != expected_count or len(gold_rows) != expected_count:
        raise ValueError(
            f"expected {expected_count} blind/gold rows, found "
            f"{len(blind_rows)}/{len(gold_rows)}"
        )
    blind = {str(row["pair_id"]): row for row in blind_rows}
    gold = {str(row["pair_id"]): row for row in gold_rows}
    if len(blind) != expected_count or len(gold) != expected_count:
        raise ValueError("blind or gold pair_id values are not unique")
    if set(blind) != set(gold):
        raise ValueError("blind and gold pair_id sets differ")
    expected_keys = {(pair_id, order) for pair_id in blind for order in ORDERS}
    actual_keys = [key(row) for row in prediction_rows]
    if len(actual_keys) != len(set(actual_keys)):
        raise ValueError("prediction keys are not unique")
    if set(actual_keys) != expected_keys:
        missing = sorted(expected_keys - set(actual_keys))[:5]
        extra = sorted(set(actual_keys) - expected_keys)[:5]
        raise ValueError(f"prediction coverage mismatch; missing={missing}, extra={extra}")
    joined = []
    for prediction in prediction_rows:
        pair_id = str(prediction["pair_id"])
        predicted = str(prediction["predicted_label"])
        gold_label = str(gold[pair_id]["gold"])
        if predicted not in PREDICTION_LABELS or gold_label not in SEMANTIC_LABELS:
            raise ValueError(
                f"invalid label for {pair_id}: prediction={predicted}, gold={gold_label}"
            )
        reparsed = parse_response(str(prediction["raw_response"]))
        for field in ("predicted_label", "parsed_label", "format_error_reason"):
            if prediction.get(field) != reparsed[field]:
                raise ValueError(
                    f"saved parse disagrees with strict v2 parser for {pair_id} "
                    f"{prediction['question_order']}: field={field}"
                )
        joined.append({
            **prediction,
            "gold": gold_label,
            "stratum": str(gold[pair_id]["stratum"]),
            "risk": str(gold[pair_id]["risk"]),
            "gold_reason": str(gold[pair_id].get("reason", "")),
            "q1": str(blind[pair_id]["q1"]),
            "q2": str(blind[pair_id]["q2"]),
            "correct": predicted == gold_label,
        })
    return joined


def classification_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter((row["gold"], row["predicted_label"]) for row in rows)
    correct = sum(row["correct"] for row in rows)
    same_total = sum(row["gold"] == "SAME_TYPE" for row in rows)
    different_total = sum(row["gold"] == "DIFFERENT" for row in rows)
    false_negatives = counts[("SAME_TYPE", "DIFFERENT")]
    false_positives = counts[("DIFFERENT", "SAME_TYPE")]
    format_errors = sum(row["predicted_label"] == "FORMAT_ERROR" for row in rows)
    return {
        "count": len(rows),
        "correct": correct,
        "accuracy": safe_rate(correct, len(rows)),
        "confusion_matrix": {
            f"gold_{gold}": {
                f"pred_{predicted}": counts[(gold, predicted)]
                for predicted in PREDICTION_LABELS
            }
            for gold in SEMANTIC_LABELS
        },
        "false_negatives": false_negatives,
        "false_negative_rate": safe_rate(false_negatives, same_total),
        "false_positives": false_positives,
        "false_positive_rate": safe_rate(false_positives, different_total),
        "format_errors": format_errors,
        "format_error_rate": safe_rate(format_errors, len(rows)),
        "format_errors_on_same_type": counts[("SAME_TYPE", "FORMAT_ERROR")],
        "format_errors_on_different": counts[("DIFFERENT", "FORMAT_ERROR")],
    }


def analyze(
    joined: list[dict[str, Any]], pair_ids: list[str],
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    index = {key(row): row for row in joined}
    conditions: dict[str, Any] = {}
    for order in ORDERS:
        rows = [row for row in joined if row["question_order"] == order]
        strata = {
            stratum: classification_metrics([row for row in rows if row["stratum"] == stratum])
            for stratum in sorted({row["stratum"] for row in rows})
        }
        conditions[order] = {**classification_metrics(rows), "strata": strata}

    disagreements = []
    both_parseable = 0
    semantic_agreements = 0
    exact_agreements = 0
    any_format_error_ids = []
    for pair_id in pair_ids:
        first = index[(pair_id, "q1_q2")]
        second = index[(pair_id, "q2_q1")]
        first_label = first["predicted_label"]
        second_label = second["predicted_label"]
        if first_label == second_label:
            exact_agreements += 1
        else:
            disagreements.append({
                "pair_id": pair_id,
                "q1_q2_label": first_label,
                "q2_q1_label": second_label,
                "q1_q2_raw_response": first["raw_response"],
                "q2_q1_raw_response": second["raw_response"],
                "gold": first["gold"],
                "q1": first["q1"],
                "q2": first["q2"],
            })
        if "FORMAT_ERROR" in (first_label, second_label):
            any_format_error_ids.append(pair_id)
        else:
            both_parseable += 1
            semantic_agreements += int(first_label == second_label)

    errors = [row for row in joined if not row["correct"]]
    metrics = {
        "evaluation_status": "diagnostic_rerun_not_held_out_validation",
        "conditions": conditions,
        "order_stability": {
            "pair_count": len(pair_ids),
            "exact_agreements_including_format_error": exact_agreements,
            "exact_agreement_rate_including_format_error": safe_rate(
                exact_agreements, len(pair_ids)
            ),
            "disagreements": len(disagreements),
            "disagreement_pair_ids": [row["pair_id"] for row in disagreements],
            "both_orders_parseable": both_parseable,
            "semantic_agreements_when_both_parseable": semantic_agreements,
            "semantic_agreement_rate_when_both_parseable": safe_rate(
                semantic_agreements, both_parseable
            ),
            "pairs_with_any_format_error": len(any_format_error_ids),
            "format_error_pair_ids": any_format_error_ids,
        },
        "error_condition_count": len(errors),
        "pairs_with_any_error": sorted({row["pair_id"] for row in errors}),
        "interpretation": (
            "Diagnostic rerun on the same 50 pairs; not a new held-out validation and "
            "not sufficient by itself to authorize R-Zero integration."
        ),
    }
    return metrics, errors, disagreements


def make_report(
    metrics: dict[str, Any], errors: list[dict[str, Any]], disagreements: list[dict[str, Any]],
) -> str:
    lines = [
        "# Generative-v2 semantic judge: diagnostic rerun", "",
        "This is a diagnostic rerun on the same 50 pairs, not a new held-out validation.", "",
        "## Metrics by question order", "",
        "| Order | Accuracy | FN | FP | Format errors |", "|---|---:|---:|---:|---:|",
    ]
    for order in ORDERS:
        row = metrics["conditions"][order]
        lines.append(
            f"| `{order}` | {row['correct']}/{row['count']} ({row['accuracy']:.1%}) | "
            f"{row['false_negatives']} | {row['false_positives']} | "
            f"{row['format_errors']} |"
        )
    stability = metrics["order_stability"]
    lines.extend([
        "", "## Order stability", "",
        f"- Disagreements: {stability['disagreements']}/{stability['pair_count']}",
        f"- Both orders parseable: {stability['both_orders_parseable']}/{stability['pair_count']}",
        "- Semantic agreement when both parseable: "
        f"{stability['semantic_agreements_when_both_parseable']}/"
        f"{stability['both_orders_parseable']}",
        f"- Pairs with any format error: {stability['pairs_with_any_format_error']}",
        "", "## Order disagreements", "",
    ])
    if disagreements:
        for row in disagreements:
            lines.append(
                f"- `{row['pair_id']}`: q1_q2=`{row['q1_q2_label']}`, "
                f"q2_q1=`{row['q2_q1_label']}`, gold=`{row['gold']}`"
            )
    else:
        lines.append("None.")
    lines.extend(["", "## Every incorrect or format-error condition", ""])
    if not errors:
        lines.append("None.")
    for number, row in enumerate(errors, 1):
        lines.extend([
            f"### {number}. {row['pair_id']} — {row['question_order']}", "",
            f"Gold: `{row['gold']}`; prediction: `{row['predicted_label']}`; "
            f"format error: `{row.get('format_error_reason')}`.", "",
            f"Stratum: `{row['stratum']}`. Gold rationale: {row['gold_reason']}", "",
            "Question 1:", "", str(row["q1"]).strip(), "", "Question 2:", "",
            str(row["q2"]).strip(), "", "Raw response:", "",
            "```text", str(row["raw_response"]).rstrip(), "```", "",
        ])
    return "\n".join(lines).rstrip() + "\n"


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--blind", type=Path, required=True)
    parser.add_argument("--gold", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--expected-count", type=int, default=50)
    return parser.parse_args()


def main() -> None:
    args = arguments()
    blind = read_jsonl(args.blind)
    gold = read_jsonl(args.gold)
    predictions = read_jsonl(args.predictions)
    joined = validate_and_join(blind, gold, predictions, args.expected_count)
    metrics, errors, disagreements = analyze(
        joined, [str(row["pair_id"]) for row in blind]
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    atomic_json(args.output_dir / "metrics_v2.json", metrics)
    atomic_jsonl(args.output_dir / "errors_v2.jsonl", errors)
    atomic_jsonl(args.output_dir / "order_disagreements_v2.jsonl", disagreements)
    (args.output_dir / "report_v2.md").write_text(
        make_report(metrics, errors, disagreements), encoding="utf-8",
    )
    print(json.dumps(metrics, indent=2, sort_keys=True))
    print(f"wrote generative-v2 diagnostic report to {args.output_dir}")


if __name__ == "__main__":
    main()
