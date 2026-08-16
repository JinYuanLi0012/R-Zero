#!/usr/bin/env python3
"""Analyze binary few-shot logprob judgments against Terra first-pass labels."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from base_judge_analyze import terra_label, write_csv
from base_judge_common import binary_metrics, roc_auc
from binary_logprob_common import VARIANTS
from common import atomic_json, read_jsonl


def metric_values(rows: list[dict[str, Any]], baseline: bool = False) -> dict[str, Any]:
    truth = [row["terra_valid"] for row in rows]
    predicted = [True] * len(rows) if baseline else [row["verdict"] == "VALID" for row in rows]
    scores = [1.0] * len(rows) if baseline else [float(row["valid_score"]) for row in rows]
    result = binary_metrics(truth, predicted)
    result["roc_auc"] = roc_auc(truth, scores)
    return result


def scope_rows(rows: list[dict[str, Any]], scope: str) -> list[dict[str, Any]]:
    return rows if scope == "overall" else [row for row in rows if row["round"] == int(scope[1:])]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--terra-results", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--expected-count", type=int, default=600)
    args = parser.parse_args()

    results = read_jsonl(args.results)
    terra = read_jsonl(args.terra_results)
    terra_by_id = {row["question_id"]: row for row in terra}
    expected_results = args.expected_count * len(VARIANTS)
    if len(results) != expected_results:
        raise RuntimeError(f"expected {expected_results} results, found {len(results)}")
    keys = {(row["question_id"], row["variant"]) for row in results}
    if len(keys) != expected_results:
        raise RuntimeError("result question/variant keys are not unique")
    if {row["question_id"] for row in results} - set(terra_by_id):
        raise RuntimeError("Terra reference is missing result question IDs")

    joined = []
    for row in results:
        label = terra_label(terra_by_id[row["question_id"]])
        joined.append({**row, "terra_label": label, "terra_valid": label == "A"})
    failures = [row for row in joined if row.get("status") != "success"]
    evaluable = [row for row in joined if row.get("status") == "success"]

    scopes = ("overall", "v1", "v2", "v3")
    metric_rows, metrics = [], {"coverage": {}, "scopes": {}, "failures": failures}
    for scope in scopes:
        metrics["scopes"][scope] = {}
        for variant in VARIANTS:
            values = scope_rows([r for r in evaluable if r["variant"] == variant], scope)
            metrics["coverage"][f"{scope}:{variant}"] = {
                "expected": args.expected_count if scope == "overall" else args.expected_count // 3,
                "evaluable": len(values),
            }
            computed = metric_values(values)
            metrics["scopes"][scope][variant] = computed
            metric_rows.append({"scope": scope, "model": variant, **computed})
        baseline_source = scope_rows(
            [
                {"round": int(row["round"]), "terra_valid": terra_label(row) == "A"}
                for row in terra
            ],
            scope,
        )
        baseline = metric_values(baseline_source, baseline=True)
        metrics["scopes"][scope]["always_valid"] = baseline
        metric_rows.append({"scope": scope, "model": "always_valid", **baseline})

    confusion_rows = []
    for scope in scopes:
        for variant in VARIANTS:
            values = scope_rows([r for r in evaluable if r["variant"] == variant], scope)
            counts = metric_values(values)
            confusion_rows.append(
                {"scope": scope, "variant": variant,
                 **{key: counts[key] for key in ("tp", "tn", "fp", "fn")}}
            )

    rate_rows = []
    for round_index in (1, 2, 3):
        reference = [row for row in terra if int(row["round"]) == round_index]
        for variant in VARIANTS:
            values = [
                row for row in evaluable
                if row["round"] == round_index and row["variant"] == variant
            ]
            rate_rows.append(
                {
                    "round": round_index, "variant": variant, "n": len(values),
                    "predicted_valid_rate": sum(r["verdict"] == "VALID" for r in values) / len(values),
                    "terra_valid_rate": sum(terra_label(r) == "A" for r in reference) / len(reference),
                }
            )

    by_key = {(row["question_id"], row["variant"]): row for row in evaluable}
    paired_rows = []
    for question_id in sorted({row["question_id"] for row in evaluable}):
        direct = by_key.get((question_id, "direct"))
        solver = by_key.get((question_id, "solver_first"))
        if direct and solver:
            paired_rows.append(
                {
                    "question_id": question_id, "round": direct["round"],
                    "terra_label": direct["terra_label"], "question": direct["question"],
                    "direct_verdict": direct["verdict"],
                    "direct_valid_score": direct["valid_score"],
                    "direct_analysis": direct["analysis"],
                    "solver_first_verdict": solver["verdict"],
                    "solver_first_valid_score": solver["valid_score"],
                    "solver_first_analysis": solver["analysis"],
                }
            )
    disagreements = [
        row for row in paired_rows
        if row["direct_verdict"] != ("VALID" if row["terra_label"] == "A" else "INVALID")
        or row["solver_first_verdict"] != ("VALID" if row["terra_label"] == "A" else "INVALID")
    ]
    comparison = {
        "paired_count": len(paired_rows),
        "same_verdict": sum(r["direct_verdict"] == r["solver_first_verdict"] for r in paired_rows),
        "direct_only_correct": sum(
            r["direct_verdict"] == ("VALID" if r["terra_label"] == "A" else "INVALID")
            and r["solver_first_verdict"] != ("VALID" if r["terra_label"] == "A" else "INVALID")
            for r in paired_rows
        ),
        "solver_first_only_correct": sum(
            r["solver_first_verdict"] == ("VALID" if r["terra_label"] == "A" else "INVALID")
            and r["direct_verdict"] != ("VALID" if r["terra_label"] == "A" else "INVALID")
            for r in paired_rows
        ),
    }
    metrics["prompt_comparison"] = comparison
    diagnostics = []
    for variant in VARIANTS:
        values = [row for row in evaluable if row["variant"] == variant]
        diagnostics.append(
            {
                "variant": variant, "n": len(values),
                "truncated_count": sum(bool(row["analysis_truncated"]) for row in values),
                "empty_analysis_count": sum(not str(row["analysis"]).strip() for row in values),
                "mean_analysis_tokens": sum(int(row["analysis_token_count"]) for row in values) / len(values),
                "valid_candidate_tokens": len(values[0]["valid_candidate_token_ids"]),
                "invalid_candidate_tokens": len(values[0]["invalid_candidate_token_ids"]),
            }
        )
    metrics["generation_diagnostics"] = diagnostics

    args.output_dir.mkdir(parents=True, exist_ok=True)
    atomic_json(args.output_dir / "metrics.json", metrics)
    write_csv(
        args.output_dir / "binary_metrics.csv", metric_rows,
        ["scope", "model", "n", "tp", "tn", "fp", "fn", "accuracy",
         "balanced_accuracy", "valid_precision", "valid_recall", "valid_f1",
         "invalid_recall", "mcc", "cohens_kappa", "roc_auc"],
    )
    write_csv(
        args.output_dir / "confusion_matrices.csv", confusion_rows,
        ["scope", "variant", "tp", "tn", "fp", "fn"],
    )
    write_csv(
        args.output_dir / "round_valid_rates.csv", rate_rows,
        ["round", "variant", "n", "predicted_valid_rate", "terra_valid_rate"],
    )
    write_csv(
        args.output_dir / "prompt_disagreements.csv", disagreements,
        ["question_id", "round", "question", "terra_label", "direct_verdict",
         "direct_valid_score", "direct_analysis", "solver_first_verdict",
         "solver_first_valid_score", "solver_first_analysis"],
    )
    write_csv(
        args.output_dir / "generation_diagnostics.csv", diagnostics,
        ["variant", "n", "truncated_count", "empty_analysis_count", "mean_analysis_tokens",
         "valid_candidate_tokens", "invalid_candidate_tokens"],
    )

    lines = [
        "# Binary few-shot logprob Judge", "",
        "Terra first-pass label A is the Valid reference; B-F are Invalid. Terra is a reference judgment, not absolute ground truth.", "",
        "## Overall", "",
        "| Method | Accuracy | Balanced accuracy | Valid P/R/F1 | Invalid recall | MCC | Kappa | AUC |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for model, title in (("direct", "Direct few-shot"), ("solver_first", "Solver-first few-shot"),
                         ("always_valid", "Always valid")):
        value = metrics["scopes"]["overall"][model]
        auc = "NA" if value["roc_auc"] is None else f"{value['roc_auc']:.3f}"
        lines.append(
            f"| {title} | {value['accuracy']:.3f} | {value['balanced_accuracy']:.3f} | "
            f"{value['valid_precision']:.3f}/{value['valid_recall']:.3f}/{value['valid_f1']:.3f} | "
            f"{value['invalid_recall']:.3f} | {value['mcc']:.3f} | {value['cohens_kappa']:.3f} | {auc} |"
        )
    lines.extend(["", "## Valid-rate trend", "", "| Round | Direct | Solver-first | Terra reference |",
                  "|---:|---:|---:|---:|"])
    for round_index in (1, 2, 3):
        direct = next(r for r in rate_rows if r["round"] == round_index and r["variant"] == "direct")
        solver = next(r for r in rate_rows if r["round"] == round_index and r["variant"] == "solver_first")
        lines.append(
            f"| V{round_index} | {direct['predicted_valid_rate']:.1%} | "
            f"{solver['predicted_valid_rate']:.1%} | {direct['terra_valid_rate']:.1%} |"
        )
    lines.extend([
        "", f"Paired questions: {comparison['paired_count']}; same verdict: {comparison['same_verdict']}; "
        f"direct-only correct: {comparison['direct_only_correct']}; solver-first-only correct: "
        f"{comparison['solver_first_only_correct']}.", "",
        "Generation diagnostics: " + "; ".join(
            f"{row['variant']} truncated={row['truncated_count']}, empty={row['empty_analysis_count']}, "
            f"mean_tokens={row['mean_analysis_tokens']:.1f}"
            for row in diagnostics
        ) + ".", "",
        "`valid_score` is a logprob-derived ranking score: the two-candidate softmax of model-computed sequence log-likelihoods for ` VALID` and ` INVALID`. It is not self-reported confidence or a calibrated probability.",
    ])
    (args.output_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
