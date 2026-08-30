#!/usr/bin/env python3
"""Score four-condition semantic-pair predictions against the private gold key."""

from __future__ import annotations

import argparse
import json
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


LABELS = ("SAME_TYPE", "DIFFERENT")
ORDERS = ("q1_q2", "q2_q1")
MAPPINGS = ("A_same", "A_different")
PRIMARY = ("q1_q2", "A_same")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as error:
                    raise ValueError(f"invalid JSON at {path}:{line_number}: {error}") from error
    return rows


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False,
    ) as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    temporary.replace(path)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False,
    ) as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        temporary = Path(handle.name)
    temporary.replace(path)


def safe_rate(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def classification_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter((row["gold"], row["predicted_label"]) for row in rows)
    same_total = sum(row["gold"] == "SAME_TYPE" for row in rows)
    different_total = sum(row["gold"] == "DIFFERENT" for row in rows)
    false_negatives = counts[("SAME_TYPE", "DIFFERENT")]
    false_positives = counts[("DIFFERENT", "SAME_TYPE")]
    correct = sum(row["gold"] == row["predicted_label"] for row in rows)
    return {
        "count": len(rows),
        "correct": correct,
        "accuracy": safe_rate(correct, len(rows)),
        "confusion_matrix": {
            "gold_SAME_TYPE": {
                "pred_SAME_TYPE": counts[("SAME_TYPE", "SAME_TYPE")],
                "pred_DIFFERENT": false_negatives,
            },
            "gold_DIFFERENT": {
                "pred_SAME_TYPE": false_positives,
                "pred_DIFFERENT": counts[("DIFFERENT", "DIFFERENT")],
            },
        },
        "false_negatives": false_negatives,
        "false_negative_rate": safe_rate(false_negatives, same_total),
        "false_positives": false_positives,
        "false_positive_rate": safe_rate(false_positives, different_total),
    }


def condition_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return str(row["pair_id"]), str(row["question_order"]), str(row["mapping"])


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
    expected_keys = {
        (pair_id, order, mapping)
        for pair_id in blind for order in ORDERS for mapping in MAPPINGS
    }
    actual_keys = [condition_key(row) for row in prediction_rows]
    if len(actual_keys) != len(set(actual_keys)):
        raise ValueError("prediction condition keys are not unique")
    if set(actual_keys) != expected_keys:
        missing = sorted(expected_keys - set(actual_keys))[:5]
        extra = sorted(set(actual_keys) - expected_keys)[:5]
        raise ValueError(f"prediction coverage mismatch; missing={missing}, extra={extra}")
    joined = []
    for prediction in prediction_rows:
        pair_id = str(prediction["pair_id"])
        label = str(prediction["predicted_label"])
        gold_label = str(gold[pair_id]["gold"])
        if label not in LABELS or gold_label not in LABELS:
            raise ValueError(f"invalid label for {pair_id}: prediction={label}, gold={gold_label}")
        joined.append({
            **prediction,
            "gold": gold_label,
            "stratum": str(gold[pair_id]["stratum"]),
            "risk": str(gold[pair_id]["risk"]),
            "gold_reason": str(gold[pair_id].get("reason", "")),
            "q1": str(blind[pair_id]["q1"]),
            "q2": str(blind[pair_id]["q2"]),
            "correct": label == gold_label,
        })
    return joined


def disagreement_summary(
    index: dict[tuple[str, str, str], dict[str, Any]],
    pair_ids: list[str],
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    order: dict[str, Any] = {}
    mapping: dict[str, Any] = {}
    details: list[dict[str, Any]] = []
    for answer_mapping in MAPPINGS:
        ids = [
            pair_id for pair_id in pair_ids
            if index[(pair_id, "q1_q2", answer_mapping)]["predicted_label"]
            != index[(pair_id, "q2_q1", answer_mapping)]["predicted_label"]
        ]
        order[answer_mapping] = {
            "compared": len(pair_ids), "disagreements": len(ids),
            "agreement_rate": safe_rate(len(pair_ids) - len(ids), len(pair_ids)),
            "pair_ids": ids,
        }
        for pair_id in ids:
            details.append({
                "kind": "question_order", "fixed_condition": answer_mapping,
                "pair_id": pair_id,
                "first_label": index[(pair_id, "q1_q2", answer_mapping)]["predicted_label"],
                "second_label": index[(pair_id, "q2_q1", answer_mapping)]["predicted_label"],
            })
    for question_order in ORDERS:
        ids = [
            pair_id for pair_id in pair_ids
            if index[(pair_id, question_order, "A_same")]["predicted_label"]
            != index[(pair_id, question_order, "A_different")]["predicted_label"]
        ]
        mapping[question_order] = {
            "compared": len(pair_ids), "disagreements": len(ids),
            "agreement_rate": safe_rate(len(pair_ids) - len(ids), len(pair_ids)),
            "pair_ids": ids,
        }
        for pair_id in ids:
            details.append({
                "kind": "answer_mapping", "fixed_condition": question_order,
                "pair_id": pair_id,
                "first_label": index[(pair_id, question_order, "A_same")]["predicted_label"],
                "second_label": index[(pair_id, question_order, "A_different")]["predicted_label"],
            })
    return order, mapping, details


def analyze(joined: list[dict[str, Any]], pair_ids: list[str]) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    by_condition: dict[str, Any] = {}
    for order in ORDERS:
        for mapping in MAPPINGS:
            rows = [
                row for row in joined
                if row["question_order"] == order and row["mapping"] == mapping
            ]
            strata: dict[str, Any] = {}
            for stratum in sorted({row["stratum"] for row in rows}):
                strata[stratum] = classification_metrics(
                    [row for row in rows if row["stratum"] == stratum]
                )
            by_condition[f"{order}__{mapping}"] = {
                **classification_metrics(rows), "strata": strata,
            }

    index = {condition_key(row): row for row in joined}
    order, mapping, disagreement_details = disagreement_summary(index, pair_ids)
    primary_rows = [
        row for row in joined
        if (row["question_order"], row["mapping"]) == PRIMARY
    ]
    primary = classification_metrics(primary_rows)
    same_template = [row for row in primary_rows if row["stratum"] == "same_template"]
    same_template_errors = sum(not row["correct"] for row in same_template)
    gate_checks = {
        "primary_accuracy_at_least_0_90": bool(primary["accuracy"] >= 0.90),
        "primary_false_negatives_at_most_2": primary["false_negatives"] <= 2,
        "primary_false_positives_at_most_2": primary["false_positives"] <= 2,
        "all_order_disagreements_at_most_2": all(
            order[answer_mapping]["disagreements"] <= 2
            for answer_mapping in MAPPINGS
        ),
        "all_mapping_disagreements_at_most_2": all(
            mapping[question_order]["disagreements"] <= 2
            for question_order in ORDERS
        ),
        "same_template_errors_at_most_2": same_template_errors <= 2,
    }
    semantic_checks = (
        "primary_accuracy_at_least_0_90",
        "primary_false_negatives_at_most_2",
        "primary_false_positives_at_most_2",
        "same_template_errors_at_most_2",
    )
    stability_checks = (
        "all_order_disagreements_at_most_2",
        "all_mapping_disagreements_at_most_2",
    )
    if all(gate_checks.values()):
        conclusion = "promising_enough_for_larger_300_pair_validation"
    elif all(gate_checks[key] for key in semantic_checks) and not all(
        gate_checks[key] for key in stability_checks
    ):
        conclusion = "unstable"
    else:
        conclusion = "falsified"
    errors = [row for row in joined if not row["correct"]]
    metrics = {
        "primary_condition": {"question_order": PRIMARY[0], "mapping": PRIMARY[1]},
        "primary": primary,
        "conditions": by_condition,
        "stability": {
            "question_order": order,
            "answer_mapping": mapping,
        },
        "same_template": {
            "count": len(same_template),
            "errors": same_template_errors,
            "accuracy": safe_rate(len(same_template) - same_template_errors, len(same_template)),
        },
        "predeclared_gate": {
            "checks": gate_checks,
            "passed": all(gate_checks.values()),
            "conclusion": conclusion,
            "note": (
                "The operational no-collapse check is at most two primary-condition "
                "errors among the eight same_template pairs."
            ),
        },
        "error_condition_count": len(errors),
        "pairs_with_any_error": sorted({row["pair_id"] for row in errors}),
    }
    return metrics, errors, disagreement_details


def markdown_text(value: Any) -> str:
    return str(value).replace("\r", "").strip()


def make_report(
    metrics: dict[str, Any], errors: list[dict[str, Any]], disagreements: list[dict[str, Any]],
) -> str:
    primary = metrics["primary"]
    gate = metrics["predeclared_gate"]
    lines = [
        "# Frozen 4B semantic-pair judge: offline 50-pair result", "",
        f"Conclusion: `{gate['conclusion']}`", "",
        "## Primary condition", "",
        "Primary is `q1_q2` with `A = SAME_TYPE`.", "",
        f"- Accuracy: {primary['correct']}/{primary['count']} ({primary['accuracy']:.1%})",
        f"- False negatives: {primary['false_negatives']}/25 ({primary['false_negative_rate']:.1%})",
        f"- False positives: {primary['false_positives']}/25 ({primary['false_positive_rate']:.1%})",
        "- Question-order disagreements: "
        + ", ".join(
            f"{name}={value['disagreements']}/50"
            for name, value in metrics["stability"]["question_order"].items()
        ),
        "- A/B-mapping disagreements: "
        + ", ".join(
            f"{name}={value['disagreements']}/50"
            for name, value in metrics["stability"]["answer_mapping"].items()
        ),
        f"- same_template errors: {metrics['same_template']['errors']}/{metrics['same_template']['count']}",
        "", "## Gate checks", "",
    ]
    for name, passed in gate["checks"].items():
        lines.append(f"- [{'x' if passed else ' '}] `{name}`")
    lines.extend(["", "## Condition metrics", "",
                  "| Condition | Accuracy | FN | FP |", "|---|---:|---:|---:|"])
    for name, condition in metrics["conditions"].items():
        lines.append(
            f"| `{name}` | {condition['correct']}/{condition['count']} "
            f"({condition['accuracy']:.1%}) | {condition['false_negatives']} | "
            f"{condition['false_positives']} |"
        )
    lines.extend(["", "## Stability disagreements", ""])
    if disagreements:
        for item in disagreements:
            lines.append(
                f"- `{item['pair_id']}` {item['kind']} ({item['fixed_condition']}): "
                f"`{item['first_label']}` vs `{item['second_label']}`"
            )
    else:
        lines.append("None.")
    lines.extend(["", "## Every incorrect condition", ""])
    if not errors:
        lines.append("None.")
    for number, row in enumerate(errors, 1):
        lines.extend([
            f"### {number}. {row['pair_id']} — {row['question_order']} / {row['mapping']}", "",
            f"Gold: `{row['gold']}`; prediction: `{row['predicted_label']}`; "
            f"A score: `{row['score_a']:.8f}`; B score: `{row['score_b']:.8f}`.", "",
            f"Stratum: `{row['stratum']}`. Gold rationale: {markdown_text(row['gold_reason'])}", "",
            "Problem 1:", "", markdown_text(row["q1"]), "", "Problem 2:", "",
            markdown_text(row["q2"]), "",
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
    pair_ids = [str(row["pair_id"]) for row in blind]
    metrics, errors, disagreements = analyze(joined, pair_ids)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.output_dir / "metrics.json", metrics)
    write_jsonl(args.output_dir / "errors.jsonl", errors)
    write_jsonl(args.output_dir / "stability_disagreements.jsonl", disagreements)
    (args.output_dir / "report.md").write_text(
        make_report(metrics, errors, disagreements), encoding="utf-8",
    )
    print(json.dumps(metrics["predeclared_gate"], indent=2, sort_keys=True))
    print(f"wrote metrics and error report to {args.output_dir}")


if __name__ == "__main__":
    main()
