#!/usr/bin/env python3
"""Minimal frozen-Base-vs-Terra reference analysis, rebuildable from two JSONLs."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from base_judge_common import LABELS, binary_metrics, roc_auc
from common import atomic_json, read_jsonl


def terra_label(row: dict[str, Any]) -> str:
    candidates = [
        row.get("first_pass_label"), row.get("label"),
        (row.get("first_pass") or {}).get("label"),
        (row.get("judgment") or {}).get("label"),
    ]
    label = next((value for value in candidates if value in LABELS), None)
    if label is None:
        raise ValueError(f"cannot find Terra first-pass A-F label for {row.get('question_id')}")
    return label


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def scope_metrics(rows: list[dict[str, Any]], model_name: str) -> dict[str, Any]:
    truth = [row["terra_label"] == "A" for row in rows]
    if model_name == "always_valid":
        predicted = [True] * len(rows)
        scores = [1.0] * len(rows)
    else:
        predicted = [row["qwen_label"] == "A" for row in rows]
        scores = [float(row["probability_label_A"]) for row in rows]
    result = binary_metrics(truth, predicted)
    result["roc_auc"] = roc_auc(truth, scores)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qwen-results", type=Path, required=True)
    parser.add_argument("--terra-results", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--expected-count", type=int, default=600)
    args = parser.parse_args()

    qwen_rows = read_jsonl(args.qwen_results)
    terra_rows = read_jsonl(args.terra_results)
    terra_by_id = {row["question_id"]: row for row in terra_rows}
    if len(qwen_rows) != args.expected_count or len({r["question_id"] for r in qwen_rows}) != len(qwen_rows):
        raise RuntimeError("Qwen results do not have the expected unique question coverage")
    if set(row["question_id"] for row in qwen_rows) - set(terra_by_id):
        raise RuntimeError("Terra reference is missing Qwen question IDs")

    joined, all_joined, failed = [], [], []
    for qwen in qwen_rows:
        reference = terra_by_id[qwen["question_id"]]
        base = {
            "question_id": qwen["question_id"], "round": int(qwen["round"]),
            "question": qwen["question"], "terra_label": terra_label(reference),
            "qwen_label": qwen.get("label"),
            "probability_label_A": qwen.get("probability_label_A"),
            "qwen_reasoning_summary": (qwen.get("judgment") or {}).get("reasoning_summary"),
        }
        all_joined.append(base)
        if qwen.get("status") == "success" and qwen.get("label") in LABELS:
            joined.append(base)
        else:
            failed.append({**base, "failure_reason": qwen.get("failure_reason")})

    metric_rows, metrics_json = [], {"coverage": {}, "scopes": {}}
    for scope in ["overall", "v1", "v2", "v3"]:
        scope_rows = joined if scope == "overall" else [r for r in joined if r["round"] == int(scope[1:])]
        all_scope = all_joined if scope == "overall" else [r for r in all_joined if r["round"] == int(scope[1:])]
        metrics_json["coverage"][scope] = {"total": len(all_scope), "parsed": len(scope_rows)}
        metrics_json["scopes"][scope] = {}
        for model in ("qwen_base", "always_valid"):
            values = scope_metrics(scope_rows if model == "qwen_base" else all_scope, model)
            metrics_json["scopes"][scope][model] = values
            metric_rows.append({"scope": scope, "model": model, **values})

    confusion_rows = []
    for scope in ["overall", "v1", "v2", "v3"]:
        values = joined if scope == "overall" else [r for r in joined if r["round"] == int(scope[1:])]
        for terra in LABELS:
            confusion_rows.append(
                {"scope": scope, "terra_label": terra,
                 **{f"qwen_{qwen}": sum(r["terra_label"] == terra and r["qwen_label"] == qwen for r in values)
                    for qwen in LABELS},
                 "qwen_PARSE_FAILURE": sum(
                     r["terra_label"] == terra and r["qwen_label"] not in LABELS
                     for r in (all_joined if scope == "overall" else [
                         item for item in all_joined if item["round"] == int(scope[1:])
                     ])
                 )}
            )

    rate_rows = []
    for round_index in (1, 2, 3):
        values = [row for row in joined if row["round"] == round_index]
        all_values = [row for row in all_joined if row["round"] == round_index]
        rate_rows.append(
            {
                "round": round_index, "n_total": len(all_values), "n_parsed": len(values),
                "qwen_valid_rate": (
                    sum(r["qwen_label"] == "A" for r in values) / len(values) if values else None
                ),
                "terra_valid_rate": sum(r["terra_label"] == "A" for r in all_values) / len(all_values),
            }
        )
    disagreements = [row for row in joined if row["qwen_label"] != row["terra_label"]]

    args.output_dir.mkdir(parents=True, exist_ok=True)
    atomic_json(args.output_dir / "metrics.json", {**metrics_json, "parse_failures": failed})
    write_csv(
        args.output_dir / "binary_metrics.csv", metric_rows,
        ["scope", "model", "n", "tp", "tn", "fp", "fn", "accuracy", "balanced_accuracy",
         "valid_precision", "valid_recall", "valid_f1", "invalid_recall", "mcc", "cohens_kappa", "roc_auc"],
    )
    write_csv(
        args.output_dir / "af_confusion.csv", confusion_rows,
        ["scope", "terra_label"] + [f"qwen_{label}" for label in LABELS] + ["qwen_PARSE_FAILURE"],
    )
    write_csv(
        args.output_dir / "round_valid_rates.csv", rate_rows,
        ["round", "n_total", "n_parsed", "qwen_valid_rate", "terra_valid_rate"],
    )
    write_csv(
        args.output_dir / "disagreements.csv", disagreements,
        ["question_id", "round", "question", "terra_label", "qwen_label",
         "probability_label_A", "qwen_reasoning_summary"],
    )
    overall = metrics_json["scopes"]["overall"]
    lines = [
        "# Frozen Qwen3-4B-Base Judge comparison", "",
        "Terra is used only as a reference judgment, not as absolute ground truth.", "",
        f"Parsed coverage: **{len(joined)}/{len(qwen_rows)}**; final parse failures: **{len(failed)}**.", "",
        "## Overall binary comparison", "",
        "| Judge | Accuracy | Balanced accuracy | Valid P/R/F1 | Invalid recall | MCC | Kappa | AUC |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for model, title in (("qwen_base", "Qwen3-4B-Base"), ("always_valid", "Always valid")):
        value = overall[model]
        auc = "NA" if value["roc_auc"] is None else f"{value['roc_auc']:.3f}"
        lines.append(
            f"| {title} | {value['accuracy']:.3f} | {value['balanced_accuracy']:.3f} | "
            f"{value['valid_precision']:.3f}/{value['valid_recall']:.3f}/{value['valid_f1']:.3f} | "
            f"{value['invalid_recall']:.3f} | {value['mcc']:.3f} | {value['cohens_kappa']:.3f} | {auc} |"
        )
    lines.extend(["", "## Valid-rate trend", "", "| Round | Qwen | Terra reference |", "|---:|---:|---:|"])
    for row in rate_rows:
        qwen_rate = "NA" if row["qwen_valid_rate"] is None else f"{row['qwen_valid_rate']:.1%}"
        lines.append(f"| V{row['round']} | {qwen_rate} | {row['terra_valid_rate']:.1%} |")
    lines.extend([
        "", "The always-valid baseline is mandatory because the reference class distribution is imbalanced. ",
        "Interpret balanced accuracy, invalid recall, MCC, kappa, and AUC alongside ordinary accuracy.", "",
        "Detailed per-round metrics, A-F confusion matrices, and disagreements are in the companion CSV files.",
    ])
    (args.output_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
