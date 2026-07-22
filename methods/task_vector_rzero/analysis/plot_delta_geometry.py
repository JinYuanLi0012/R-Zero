#!/usr/bin/env python3
"""Render deterministic static figures from completed delta-geometry tables."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


FAMILY_COLORS = {
    "questioner_full": "#E68613",
    "solver_rank1": "#2B6CB0",
    "solver_full": "#7A8A99",
}


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_matrix(path: Path) -> tuple[list[str], list[str], np.ndarray]:
    rows = read_rows(path)
    if not rows:
        raise ValueError(f"Empty matrix CSV: {path}")
    column_labels = [key for key in rows[0] if key != "delta_id"]
    row_labels = [row["delta_id"] for row in rows]
    matrix = np.asarray(
        [[float(row[label]) for label in column_labels] for row in rows], dtype=float
    )
    return row_labels, column_labels, matrix


def save(fig: plt.Figure, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output.with_suffix(".png"), dpi=180, bbox_inches="tight")
    fig.savefig(output.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)


def short_label(value: str) -> str:
    replacements = {
        "questioner_full_r": "Q",
        "solver_rank1_r": "S-rank1-",
        "solver_full_r": "S-full-",
    }
    for prefix, replacement in replacements.items():
        if value.startswith(prefix):
            return value.replace(prefix, replacement)
    return value


def plot_global_norms(analysis: Path, figures: Path) -> None:
    rows = read_rows(analysis / "metrics/global_norms.csv")
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    for family in ("questioner_full", "solver_rank1", "solver_full"):
        selected = sorted(
            (row for row in rows if row["family"] == family), key=lambda row: int(row["round"])
        )
        rounds = [int(row["round"]) for row in selected]
        axes[0].plot(
            rounds,
            [float(row["l2_norm"]) for row in selected],
            marker="o",
            linewidth=2,
            color=FAMILY_COLORS[family],
            label=family.replace("_", " "),
        )
        axes[1].plot(
            rounds,
            [float(row["relative_l2"]) for row in selected],
            marker="o",
            linewidth=2,
            color=FAMILY_COLORS[family],
            label=family.replace("_", " "),
        )
    axes[0].set_title("Global delta L2 norm")
    axes[1].set_title("Delta norm relative to round start")
    for axis in axes:
        axis.set_xlabel("Round")
        axis.set_xticks(range(1, 6))
        axis.grid(alpha=0.25)
    axes[0].set_ylabel("L2 norm")
    axes[1].set_ylabel("Relative L2")
    axes[0].legend(frameon=False)
    fig.suptitle("Questioner and Solver update magnitudes")
    fig.tight_layout()
    save(fig, figures / "global_delta_norms")


def plot_heatmap(
    matrix_path: Path,
    output: Path,
    title: str,
    vmin: float = -1.0,
    vmax: float = 1.0,
) -> None:
    row_labels, column_labels, matrix = read_matrix(matrix_path)
    row_labels = [short_label(label) for label in row_labels]
    column_labels = [short_label(label) for label in column_labels]
    width = max(5.0, 0.65 * len(column_labels) + 2)
    height = max(4.5, 0.65 * len(row_labels) + 1.5)
    fig, axis = plt.subplots(figsize=(width, height))
    image = axis.imshow(matrix, cmap="coolwarm", vmin=vmin, vmax=vmax, aspect="equal")
    axis.set_xticks(range(len(column_labels)), column_labels, rotation=45, ha="right")
    axis.set_yticks(range(len(row_labels)), row_labels)
    axis.set_title(title)
    threshold = (vmin + vmax) / 2
    for row in range(matrix.shape[0]):
        for column in range(matrix.shape[1]):
            value = matrix[row, column]
            color = "white" if abs(value - threshold) > 0.55 * (vmax - vmin) else "black"
            axis.text(column, row, f"{value:.2f}", ha="center", va="center", fontsize=8, color=color)
    fig.colorbar(image, ax=axis, fraction=0.046, pad=0.04, label="Cosine similarity")
    fig.tight_layout()
    save(fig, output)


def plot_direction_metrics(analysis: Path, figures: Path) -> None:
    rows = read_rows(analysis / "metrics/direction_metrics.csv")
    adjacent = [row for row in rows if row["metric"] == "adjacent"]
    historical = [row for row in rows if row["metric"] == "historical" and int(row["round"]) > 1]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    for family in FAMILY_COLORS:
        selected = sorted(
            (row for row in adjacent if row["family"] == family),
            key=lambda row: int(row["to_round"]),
        )
        axes[0].plot(
            [int(row["to_round"]) for row in selected],
            [float(row["angle_degrees"]) for row in selected],
            marker="o",
            linewidth=2,
            label=family.replace("_", " "),
            color=FAMILY_COLORS[family],
        )
        selected = sorted(
            (row for row in historical if row["family"] == family),
            key=lambda row: int(row["round"]),
        )
        axes[1].plot(
            [int(row["round"]) for row in selected],
            [float(row["history_cosine"]) for row in selected],
            marker="o",
            linewidth=2,
            label=family.replace("_", " "),
            color=FAMILY_COLORS[family],
        )
    axes[0].axhline(90, color="black", linestyle="--", alpha=0.35)
    axes[0].set_title("Angle to previous round")
    axes[0].set_ylabel("Degrees")
    axes[1].axhline(0, color="black", linestyle="--", alpha=0.35)
    axes[1].set_title("Cosine with accumulated history")
    axes[1].set_ylabel("Cosine")
    for axis in axes:
        axis.set_xlabel("Round")
        axis.set_xticks(range(2, 6))
        axis.grid(alpha=0.2)
    axes[0].legend(frameon=False)
    fig.tight_layout()
    save(fig, figures / "direction_progression")

    fig, axis = plt.subplots(figsize=(7.5, 4.8))
    x = np.arange(2, 6)
    width = 0.24
    for offset, family in enumerate(FAMILY_COLORS):
        selected = sorted(
            (row for row in historical if row["family"] == family),
            key=lambda row: int(row["round"]),
        )
        axis.bar(
            x + (offset - 1) * width,
            [float(row["orthogonal_ratio"]) for row in selected],
            width,
            color=FAMILY_COLORS[family],
            label=family.replace("_", " "),
        )
    axis.set_xticks(x)
    axis.set_xlabel("Round")
    axis.set_ylabel("Orthogonal norm / delta norm")
    axis.set_ylim(0, 1.05)
    axis.set_title("Novel direction relative to accumulated history")
    axis.legend(frameon=False)
    axis.grid(axis="y", alpha=0.2)
    fig.tight_layout()
    save(fig, figures / "historical_alignment")


def plot_relex(analysis: Path, figures: Path) -> None:
    rows = sorted(
        read_rows(analysis / "metrics/relex_retention.csv"), key=lambda row: int(row["round"])
    )
    rounds = [int(row["round"]) for row in rows]
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.2))
    series = (
        ("norm_ratio", "Rank1 / Full norm", None),
        ("cosine", "Rank1–Full cosine", (-1.05, 1.05)),
        ("relative_reconstruction_error", "Relative reconstruction error", None),
    )
    for axis, (key, title, ylim) in zip(axes, series):
        axis.plot(rounds, [float(row[key]) for row in rows], marker="o", linewidth=2.2)
        axis.set_title(title)
        axis.set_xlabel("Round")
        axis.set_xticks(rounds)
        axis.grid(alpha=0.25)
        if ylim:
            axis.set_ylim(*ylim)
    fig.suptitle("RELEX full-to-rank1 retention")
    fig.tight_layout()
    save(fig, figures / "relex_retention")


def read_embedding(path: Path) -> tuple[list[str], np.ndarray]:
    rows = read_rows(path)
    return [row["label"] for row in rows], np.asarray(
        [[float(row["component_1"]), float(row["component_2"])] for row in rows]
    )


def plot_direction_plane(analysis: Path, figures: Path) -> None:
    labels, points = read_embedding(analysis / "embeddings/direction_svd.csv")
    fig, axis = plt.subplots(figsize=(8, 7))
    for label, point in zip(labels, points):
        family = "questioner_full" if label.startswith("questioner") else "solver_rank1"
        axis.arrow(
            0,
            0,
            point[0],
            point[1],
            color=FAMILY_COLORS[family],
            alpha=0.82,
            width=0.006,
            length_includes_head=True,
        )
        axis.text(point[0] * 1.05, point[1] * 1.05, short_label(label), fontsize=9)
    axis.axhline(0, color="black", linewidth=0.7, alpha=0.3)
    axis.axvline(0, color="black", linewidth=0.7, alpha=0.3)
    axis.set_aspect("equal", adjustable="datalim")
    axis.set_title("Joint unit-delta direction plane")
    axis.set_xlabel("Component 1")
    axis.set_ylabel("Component 2")
    axis.grid(alpha=0.15)
    fig.tight_layout()
    save(fig, figures / "direction_plane")


def plot_rank_full_plane(analysis: Path, figures: Path) -> None:
    labels, points = read_embedding(analysis / "embeddings/rank1_vs_full_svd.csv")
    by_label = {label: point for label, point in zip(labels, points)}
    fig, axis = plt.subplots(figsize=(8, 7))
    for round_number in range(1, 6):
        full_label = f"solver_full_r{round_number}"
        rank_label = f"solver_rank1_r{round_number}"
        full = by_label[full_label]
        rank = by_label[rank_label]
        axis.plot([full[0], rank[0]], [full[1], rank[1]], color="#A0AEC0", linewidth=1)
        axis.arrow(
            0,
            0,
            full[0],
            full[1],
            color=FAMILY_COLORS["solver_full"],
            linestyle="--",
            alpha=0.65,
            length_includes_head=True,
        )
        axis.arrow(
            0,
            0,
            rank[0],
            rank[1],
            color=FAMILY_COLORS["solver_rank1"],
            alpha=0.85,
            width=0.004,
            length_includes_head=True,
        )
        axis.text(full[0] * 1.04, full[1] * 1.04, f"F{round_number}", fontsize=8)
        axis.text(rank[0] * 1.04, rank[1] * 1.04, f"R{round_number}", fontsize=8)
    axis.axhline(0, color="black", linewidth=0.7, alpha=0.3)
    axis.axvline(0, color="black", linewidth=0.7, alpha=0.3)
    axis.set_aspect("equal", adjustable="datalim")
    axis.set_title("Solver full vs RELEX rank1 directions")
    axis.set_xlabel("Component 1")
    axis.set_ylabel("Component 2")
    axis.grid(alpha=0.15)
    fig.tight_layout()
    save(fig, figures / "rank1_vs_full_plane")


def evaluation_map(path: Path | None) -> dict[str, dict[str, float]]:
    if not path or not path.is_file():
        return {}
    result: dict[str, dict[str, float]] = {}
    for row in read_rows(path):
        result[row["model"]] = {
            key: float(value) for key, value in row.items() if key != "model" and value != ""
        }
    return result


def plot_trajectory(analysis: Path, figures: Path, evaluation_csv: Path | None) -> None:
    labels, points = read_embedding(analysis / "embeddings/cumulative_trajectory.csv")
    evaluations = evaluation_map(evaluation_csv)
    fig, axis = plt.subplots(figsize=(8.5, 7))
    base = points[labels.index("Base")]
    axis.scatter(*base, marker="*", s=180, color="black", zorder=4)
    axis.text(base[0], base[1], "Base", ha="left", va="bottom")
    for family_prefix, color in (("Q", FAMILY_COLORS["questioner_full"]), ("V", FAMILY_COLORS["solver_rank1"])):
        selected = [(label, points[index]) for index, label in enumerate(labels) if label.startswith(family_prefix)]
        path = np.vstack([base, *[point for _, point in selected]])
        axis.plot(path[:, 0], path[:, 1], color=color, linewidth=2, marker="o")
        for label, point in selected:
            suffix = ""
            if label.startswith("V") and f"Rank1 {label}" in evaluations:
                suffix = f"\n{evaluations[f'Rank1 {label}'].get('Avg7', math.nan):.2f}"
            axis.text(point[0], point[1], label + suffix, fontsize=9, ha="left", va="bottom")
    axis.axhline(0, color="black", linewidth=0.7, alpha=0.3)
    axis.axvline(0, color="black", linewidth=0.7, alpha=0.3)
    axis.set_title("Cumulative Questioner and Rank1 Solver trajectories")
    axis.set_xlabel("Component 1")
    axis.set_ylabel("Component 2")
    axis.grid(alpha=0.15)
    fig.tight_layout()
    save(fig, figures / "cumulative_trajectory")


def plot_layer_heatmap(analysis: Path, figures: Path) -> None:
    rows = read_rows(analysis / "metrics/per_layer_metrics.csv")
    layers = sorted({row["group"] for row in rows if row["group"].startswith("layer_")})
    for family in FAMILY_COLORS:
        selected = [row for row in rows if row["family"] == family and row["group"] in layers]
        by_key = {(row["group"], int(row["round"])): float(row["relative_l2"]) for row in selected}
        matrix = np.asarray([[by_key.get((layer, round_number), np.nan) for layer in layers] for round_number in range(1, 6)])
        fig, axis = plt.subplots(figsize=(max(11, len(layers) * 0.32), 4.5))
        image = axis.imshow(matrix, cmap="viridis", aspect="auto")
        axis.set_xticks(range(len(layers)), [layer.replace("layer_", "L") for layer in layers], rotation=90)
        axis.set_yticks(range(5), [f"R{i}" for i in range(1, 6)])
        axis.set_title(f"Per-layer relative delta norm: {family.replace('_', ' ')}")
        axis.set_xlabel("Transformer layer")
        axis.set_ylabel("Round")
        fig.colorbar(image, ax=axis, label="Relative L2")
        fig.tight_layout()
        save(fig, figures / f"layer_norm_heatmap_{family}")


def plot_evaluation(evaluation_csv: Path | None, figures: Path) -> None:
    if not evaluation_csv or not evaluation_csv.is_file():
        return
    rows = read_rows(evaluation_csv)
    models = [row["model"] for row in rows]
    metrics = [key for key in rows[0] if key != "model"]
    values = np.asarray([[float(row[key]) for key in metrics] for row in rows])
    base = values[0]
    deltas = values - base
    fig, axes = plt.subplots(1, 2, figsize=(15, 5))
    for axis, matrix, title, cmap in (
        (axes[0], values, "Evaluation scores", "viridis"),
        (axes[1], deltas, "Evaluation delta vs Base", "coolwarm"),
    ):
        limit = np.max(np.abs(matrix)) if title.endswith("Base") else None
        image = axis.imshow(
            matrix,
            cmap=cmap,
            aspect="auto",
            vmin=-limit if limit else None,
            vmax=limit if limit else None,
        )
        axis.set_xticks(range(len(metrics)), metrics, rotation=45, ha="right")
        axis.set_yticks(range(len(models)), models)
        axis.set_title(title)
        for row in range(matrix.shape[0]):
            for column in range(matrix.shape[1]):
                axis.text(column, row, f"{matrix[row, column]:.2f}", ha="center", va="center", fontsize=7)
        fig.colorbar(image, ax=axis, fraction=0.03, pad=0.03)
    fig.tight_layout()
    save(fig, figures / "evaluation_geometry")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis-root", required=True, type=Path)
    parser.add_argument("--evaluation-csv", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    analysis = args.analysis_root.expanduser().resolve()
    figures = analysis / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    plot_global_norms(analysis, figures)
    for filename, title in (
        ("questioner_full_cosine.csv", "Questioner full-delta cosine"),
        ("solver_rank1_cosine.csv", "Solver rank1-delta cosine"),
        ("solver_full_cosine.csv", "Solver full-delta cosine"),
        ("questioner_solver_cross_cosine.csv", "Questioner–Solver rank1 joint cosine"),
        ("rank1_full_cross_cosine.csv", "Solver rank1–full joint cosine"),
    ):
        plot_heatmap(analysis / "matrices" / filename, figures / filename.removesuffix(".csv"), title)
    plot_direction_metrics(analysis, figures)
    plot_relex(analysis, figures)
    plot_direction_plane(analysis, figures)
    plot_rank_full_plane(analysis, figures)
    plot_trajectory(analysis, figures, args.evaluation_csv)
    plot_layer_heatmap(analysis, figures)
    plot_evaluation(args.evaluation_csv, figures)
    print(f"Figures written to {figures}")


if __name__ == "__main__":
    main()
