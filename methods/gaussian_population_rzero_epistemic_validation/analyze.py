#!/usr/bin/env python3
"""Equal-footing analysis of every preregistered Gaussian perturbation scale."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from scipy.optimize import linear_sum_assignment
from scipy.stats import binomtest
from sklearn.metrics import roc_auc_score

from common import atomic_json, parse_sigmas, read_jsonl, sigma_key, stable_int


def load_summary(path: Path) -> pd.DataFrame:
    return pq.read_table(path).to_pandas()


def match_round(frame: pd.DataFrame) -> tuple[pd.DataFrame, bool]:
    quartile_size = len(frame) // 4
    high = frame.sort_values(["u_epi", "question_id"], ascending=[False, True]).head(quartile_size).reset_index(drop=True)
    low = frame.sort_values(["u_epi", "question_id"], ascending=[True, True]).head(quartile_size).reset_index(drop=True)

    def solve(h_caliper: float, d_caliper: float) -> pd.DataFrame:
        real_columns = len(low)
        costs = np.full((len(high), real_columns + len(high)), 1000.0)
        costs[:, real_columns:] = 100.0
        for i, hrow in high.iterrows():
            for j, lrow in low.iterrows():
                delta_h = abs(hrow.h_total - lrow.h_total)
                delta_difficulty = abs(hrow.original_difficulty - lrow.original_difficulty)
                if delta_h <= h_caliper and delta_difficulty <= d_caliper:
                    delta_length = abs(
                        math.log(max(hrow.question_length, 1))
                        - math.log(max(lrow.question_length, 1))
                    )
                    costs[i, j] = delta_h / h_caliper + delta_difficulty / d_caliper + 0.1 * delta_length
        row_indices, columns = linear_sum_assignment(costs)
        rows = []
        for i, j in zip(row_indices, columns):
            if j < real_columns and costs[i, j] < 100:
                rows.append(
                    {
                        "round": int(high.iloc[i]["round"]),
                        "high_question_id": high.iloc[i].question_id,
                        "low_question_id": low.iloc[j].question_id,
                        "high_valid": int(high.iloc[i].valid),
                        "low_valid": int(low.iloc[j].valid),
                        "validity_difference": int(high.iloc[i].valid) - int(low.iloc[j].valid),
                        "high_u_epi": float(high.iloc[i].u_epi),
                        "low_u_epi": float(low.iloc[j].u_epi),
                        "delta_h_total": float(abs(high.iloc[i].h_total - low.iloc[j].h_total)),
                        "delta_original_difficulty": float(
                            abs(high.iloc[i].original_difficulty - low.iloc[j].original_difficulty)
                        ),
                        "cost": float(costs[i, j]),
                    }
                )
        return pd.DataFrame(rows)

    pairs = solve(0.15, 0.06)
    relaxed = len(pairs) < 30
    if relaxed:
        pairs = solve(0.30, 0.12)
    return pairs, relaxed


def paired_statistics(pairs: pd.DataFrame, bootstrap_samples: int, seed: int) -> dict:
    if pairs.empty:
        return {
            "pairs": 0, "high_valid_rate": None, "low_valid_rate": None,
            "difference_pp": None, "ci95_pp": [None, None], "mcnemar_exact_p": None,
        }
    differences = pairs.validity_difference.to_numpy(dtype=float)
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(differences), size=(bootstrap_samples, len(differences)))
    boot = differences[indices].mean(axis=1) * 100
    high_wins = int(((pairs.high_valid == 1) & (pairs.low_valid == 0)).sum())
    low_wins = int(((pairs.high_valid == 0) & (pairs.low_valid == 1)).sum())
    discordant = high_wins + low_wins
    return {
        "pairs": int(len(pairs)),
        "high_valid_rate": float(pairs.high_valid.mean()),
        "low_valid_rate": float(pairs.low_valid.mean()),
        "difference_pp": float(differences.mean() * 100),
        "ci95_pp": [float(value) for value in np.quantile(boot, [0.025, 0.975])],
        "discordant_high_wins": high_wins,
        "discordant_low_wins": low_wins,
        "mcnemar_exact_p": float(binomtest(high_wins, discordant, 0.5).pvalue) if discordant else 1.0,
    }


def precision_table(frame: pd.DataFrame) -> pd.DataFrame:
    work = frame.copy()
    work["negative_h_within"] = -work.h_within
    methods = {
        "original_difficulty": "original_difficulty",
        "H_total": "h_total",
        "-H_within": "negative_h_within",
        "U_epi": "u_epi",
    }
    rows = []
    for budget in (0.10, 0.20, 0.30):
        for method, column in methods.items():
            selected_parts = []
            for round_index, group in work.groupby("round"):
                count = int(round(len(group) * budget))
                selected = group.sort_values([column, "question_id"], ascending=[False, True]).head(count)
                selected_parts.append(selected)
                rows.append(
                    {"scope": f"V{round_index}", "budget": budget, "method": method,
                     "selected": count, "precision": float(selected.valid.mean())}
                )
            combined = pd.concat(selected_parts)
            rows.append(
                {"scope": "V1-V3 combined", "budget": budget, "method": method,
                 "selected": len(combined), "precision": float(combined.valid.mean())}
            )
    return pd.DataFrame(rows)


def analyze_sigma(
    frame: pd.DataFrame, sigma: float, bootstrap_samples: int, seed: int
) -> tuple[pd.DataFrame, dict, pd.DataFrame]:
    pair_parts = []
    round_stats = {}
    for round_index, group in frame.groupby("round"):
        pairs, relaxed = match_round(group)
        if not pairs.empty:
            pairs.insert(0, "sigma", sigma)
        pair_parts.append(pairs)
        round_stats[f"V{round_index}"] = {
            **paired_statistics(pairs, bootstrap_samples, stable_int(seed, sigma, round_index)),
            "caliper_relaxed": relaxed,
        }
    pairs = pd.concat(pair_parts, ignore_index=True) if pair_parts else pd.DataFrame()
    v23 = pairs[pairs["round"].isin([2, 3])] if not pairs.empty else pairs
    precision = precision_table(frame)
    precision.insert(0, "sigma", sigma)
    valid_values = frame.valid.astype(int)
    auc = float(roc_auc_score(valid_values, frame.u_epi)) if valid_values.nunique() == 2 else None
    relationship = {
        "valid_rate": float(frame.valid.mean()),
        "mean_u_epi_valid": float(frame.loc[frame.valid, "u_epi"].mean()) if frame.valid.any() else None,
        "mean_u_epi_invalid": float(frame.loc[~frame.valid, "u_epi"].mean()) if (~frame.valid).any() else None,
        "u_epi_valid_roc_auc": auc,
    }
    statistics = {
        "primary_V2_V3": paired_statistics(v23, bootstrap_samples, stable_int(seed, sigma, "v23")),
        "rounds": round_stats,
        "valid_relationship": relationship,
    }
    return pairs, statistics, precision


def write_scale_plots(scale_rows: pd.DataFrame, precision: pd.DataFrame, output_dir: Path) -> None:
    labels = [f"{value:g}" for value in scale_rows.sigma]
    x = np.arange(len(labels))
    fig, axes = plt.subplots(2, 2, figsize=(10, 7))
    panels = [
        ("high_consensus_historical_agreement", "Historical answer retention"),
        ("extraction_failure_rate", "Extraction failure"),
        ("mean_u_epi", "Mean U_epi"),
        ("v23_matched_difference_pp", "V2+V3 matched validity difference (pp)"),
    ]
    for axis, (column, title) in zip(axes.flat, panels):
        axis.plot(x, scale_rows[column], marker="o")
        axis.set_xticks(x, labels)
        axis.set_xlabel("sigma")
        axis.set_title(title)
    fig.tight_layout()
    fig.savefig(output_dir / "cross_sigma_trajectories.png", dpi=180)
    plt.close(fig)

    p20 = precision[
        (precision.scope == "V1-V3 combined") & (precision.budget == 0.20)
    ]
    fig, axis = plt.subplots(figsize=(8, 4))
    for method, group in p20.groupby("method"):
        ordered = group.sort_values("sigma")
        axis.plot(range(len(ordered)), ordered.precision, marker="o", label=method)
    axis.set_xticks(x, labels)
    axis.set_xlabel("sigma")
    axis.set_ylabel("Precision@20%")
    axis.set_ylim(0, 1)
    axis.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "precision_at_20_across_sigmas.png", dpi=180)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=Path, required=True)
    parser.add_argument("--judge-results", type=Path, required=True)
    parser.add_argument("--score-root", type=Path, required=True)
    parser.add_argument("--sigmas", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--bootstrap-samples", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    sigmas = parse_sigmas(args.sigmas)
    if sigmas != [0.0, 0.0001, 0.0003, 0.001, 0.003]:
        raise ValueError("analysis requires the five preregistered sigma values")
    samples = read_jsonl(args.samples)
    judge = pd.DataFrame(read_jsonl(args.judge_results))
    if len(samples) != 600 or len(judge) != 600:
        raise RuntimeError("analysis requires 600 sampled rows and 600 Judge row results")
    if {row["question_id"] for row in samples} != set(judge.question_id):
        raise RuntimeError("sample and Judge IDs do not match")

    all_pairs = []
    all_precision = []
    all_question_scores = []
    all_diagnostics = []
    scale_summaries = []
    sigma_results = {}
    for sigma in sigmas:
        pieces = [
            load_summary(
                args.score_root / f"v{round_index}" / "summary" / f"sigma_{sigma_key(sigma)}.parquet"
            )
            for round_index in (1, 2, 3)
        ]
        frame = pd.concat(pieces, ignore_index=True).merge(
            judge[["question_id", "label", "confidence", "valid"]],
            on="question_id", how="left", validate="one_to_one",
        )
        if len(frame) != 600 or frame.valid.isna().any():
            raise RuntimeError(f"sigma {sigma} does not have a complete 600-question grid")
        pairs, statistics, precision = analyze_sigma(frame, sigma, args.bootstrap_samples, args.seed)
        statistics["precision_at_k"] = json.loads(precision.to_json(orient="records"))
        all_pairs.append(pairs)
        all_precision.append(precision)
        frame.insert(0, "analysis_sigma", sigma)
        all_question_scores.append(frame)

        for round_index, group in frame.groupby("round"):
            for label in ["A", "B", "C", "D", "E", "F"]:
                all_diagnostics.append(
                    {"sigma": sigma, "round": round_index, "metric": f"judge_label_{label}_rate",
                     "value": float((group.label == label).mean())}
                )
            for column in [
                "original_majority_rate", "original_difficulty", "h_total", "h_within", "u_epi",
                "extraction_success_rate", "historical_answer_agreement_rate", "confidence",
            ]:
                all_diagnostics.extend(
                    {"sigma": sigma, "round": round_index, "metric": f"{column}_{stat}", "value": float(value)}
                    for stat, value in {"mean": group[column].mean(), "median": group[column].median()}.items()
                )
            high_entropy = group[group.h_total >= group.h_total.quantile(0.75)]
            ratios = high_entropy.loc[high_entropy.h_total > 0, "h_within"] / high_entropy.loc[high_entropy.h_total > 0, "h_total"]
            all_diagnostics.append(
                {"sigma": sigma, "round": round_index, "metric": "high_total_entropy_within_fraction",
                 "value": float(ratios.mean()) if len(ratios) else None}
            )

        high_consensus = frame[frame.original_majority_rate >= 7 / 9 - 1e-9]
        primary = statistics["primary_V2_V3"]
        scale_row = {
            "sigma": sigma,
            "completion_count": int(frame.completion_count.sum()),
            "extraction_failure_rate": float(1 - frame.extraction_success_rate.mean()),
            "high_consensus_question_count": int(len(high_consensus)),
            "high_consensus_historical_agreement": float(high_consensus.historical_answer_agreement_rate.mean()) if len(high_consensus) else None,
            "mean_h_total": float(frame.h_total.mean()),
            "mean_h_within": float(frame.h_within.mean()),
            "mean_u_epi": float(frame.u_epi.mean()),
            "v23_matched_pairs": primary["pairs"],
            "v23_matched_difference_pp": primary["difference_pp"],
            "v23_ci95_low_pp": primary["ci95_pp"][0],
            "v23_ci95_high_pp": primary["ci95_pp"][1],
            "v23_mcnemar_exact_p": primary["mcnemar_exact_p"],
            **statistics["valid_relationship"],
        }
        for budget in (0.10, 0.20, 0.30):
            selected = precision[
                (precision.scope == "V1-V3 combined")
                & (precision.budget == budget)
                & (precision.method == "U_epi")
            ]
            scale_row[f"u_epi_precision_at_{int(budget * 100)}"] = float(selected.iloc[0].precision)
        scale_summaries.append(scale_row)
        sigma_results[str(sigma)] = statistics

    pairs_frame = pd.concat(all_pairs, ignore_index=True)
    precision_frame = pd.concat(all_precision, ignore_index=True)
    question_frame = pd.concat(all_question_scores, ignore_index=True)
    scale_frame = pd.DataFrame(scale_summaries)
    pairs_frame.to_csv(args.output_dir / "matched_pairs_all_sigmas.csv", index=False)
    precision_frame.to_csv(args.output_dir / "precision_at_k_all_sigmas.csv", index=False)
    pd.DataFrame(all_diagnostics).to_csv(args.output_dir / "round_diagnostics_all_sigmas.csv", index=False)
    question_frame[[
        "analysis_sigma", "question_id", "round", "stratum", "sampling_weight",
        "original_majority_rate", "original_difficulty", "historical_answer_agreement_rate",
        "h_total", "h_within", "u_epi", "u_epi_norm", "conditional_valid_h_total",
        "conditional_valid_h_within", "conditional_valid_u_epi", "extraction_success_rate",
        "label", "confidence", "valid",
    ]].to_csv(args.output_dir / "question_level_scores_all_sigmas.csv", index=False)
    scale_frame.to_csv(args.output_dir / "cross_sigma_summary.csv", index=False)
    atomic_json(
        args.output_dir / "analysis_summary.json",
        {
            "scope_limitation": "Secondary discrimination within old-reward-retained V1-V3 data only; the deleted full 8k pools are not represented.",
            "preregistered_sigmas": sigmas,
            "sigma_zero_role": "Control for disagreement caused only by generation sampling randomness.",
            "no_post_hoc_sigma_selection": True,
            "per_sigma": sigma_results,
            "cross_sigma": scale_summaries,
        },
    )
    write_scale_plots(scale_frame, precision_frame, args.output_dir)

    table = scale_frame[[
        "sigma", "extraction_failure_rate", "high_consensus_historical_agreement",
        "mean_u_epi", "u_epi_valid_roc_auc", "v23_matched_pairs",
        "v23_matched_difference_pp", "v23_ci95_low_pp", "v23_ci95_high_pp",
    ]].to_markdown(index=False)
    report = f"""# R-Zero V1–V3 Epistemic Offline Validation

## Scope and fixed-scale design

This exploratory pilot covers 600 stratified questions from the old-reward-retained V1–V3 Solver datasets. The deleted 8k candidate pools are not represented. All five perturbation scales were fixed before analysis and are reported equally; no sigma is selected as a primary or best result. Sigma zero is the sampling-randomness control.

The core question is whether epistemic disagreement stably separates reasonable capability boundaries from question-induced confusion across scales, and at what scale this ability disappears as perturbations become destructive.

## Cross-sigma results

{table}

For every sigma, `analysis_summary.json` contains V2+V3 and per-round paired H1 results, exact McNemar tests, Valid-label relationships, and Precision@10/20/30. The trajectory plots show historical-answer retention on high-consensus questions, extraction failure, mean U_epi, matched validity separation, and Precision@20.

The interpretation should emphasize stability across adjacent nonzero scales and jointly inspect rising U_epi, answer retention, and extraction failure. An isolated best-looking scale is not treated as confirmatory evidence.
"""
    (args.output_dir / "report.md").write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
