#!/usr/bin/env python3
"""Pure NumPy derivations from streamed delta Gram matrices."""

from __future__ import annotations

import math
from typing import Any, Iterable

import numpy as np


EPS = 1e-30


def cosine_from_gram(gram: np.ndarray) -> np.ndarray:
    gram = np.asarray(gram, dtype=np.float64)
    norms = np.sqrt(np.maximum(np.diag(gram), 0.0))
    denominator = np.outer(norms, norms)
    cosine = np.divide(gram, denominator, out=np.zeros_like(gram), where=denominator > EPS)
    return np.clip(cosine, -1.0, 1.0)


def _safe_angle(cosine: float) -> float:
    return math.degrees(math.acos(max(-1.0, min(1.0, cosine))))


def historical_metrics(gram: np.ndarray, indices: list[int]) -> list[dict[str, float | int]]:
    rows: list[dict[str, float | int]] = []
    for position, index in enumerate(indices):
        delta_sq = max(0.0, float(gram[index, index]))
        delta_norm = math.sqrt(delta_sq)
        if position == 0:
            rows.append(
                {
                    "round": 1,
                    "delta_norm": delta_norm,
                    "history_norm": 0.0,
                    "history_cosine": 0.0,
                    "history_angle_degrees": 0.0,
                    "parallel_signed": 0.0,
                    "parallel_norm": 0.0,
                    "orthogonal_norm": delta_norm,
                    "orthogonal_ratio": 1.0 if delta_norm else 0.0,
                }
            )
            continue
        history = indices[:position]
        history_sq = max(0.0, float(gram[np.ix_(history, history)].sum()))
        history_norm = math.sqrt(history_sq)
        dot = float(gram[index, history].sum())
        denominator = delta_norm * history_norm
        cosine = dot / denominator if denominator > EPS else 0.0
        cosine = max(-1.0, min(1.0, cosine))
        parallel_signed = dot / history_norm if history_norm > EPS else 0.0
        orthogonal_sq = max(0.0, delta_sq - parallel_signed * parallel_signed)
        orthogonal_norm = math.sqrt(orthogonal_sq)
        rows.append(
            {
                "round": position + 1,
                "delta_norm": delta_norm,
                "history_norm": history_norm,
                "history_cosine": cosine,
                "history_angle_degrees": _safe_angle(cosine),
                "parallel_signed": parallel_signed,
                "parallel_norm": abs(parallel_signed),
                "orthogonal_norm": orthogonal_norm,
                "orthogonal_ratio": orthogonal_norm / delta_norm if delta_norm > EPS else 0.0,
            }
        )
    return rows


def adjacent_metrics(gram: np.ndarray, indices: list[int]) -> list[dict[str, float | int]]:
    cosine = cosine_from_gram(gram)
    return [
        {
            "from_round": position,
            "to_round": position + 1,
            "cosine": float(cosine[indices[position - 1], indices[position]]),
            "angle_degrees": _safe_angle(float(cosine[indices[position - 1], indices[position]])),
        }
        for position in range(1, len(indices))
    ]


def relex_metrics(
    gram: np.ndarray,
    rank_indices: list[int],
    full_indices: list[int],
) -> list[dict[str, float | int]]:
    rows: list[dict[str, float | int]] = []
    for position, (rank_index, full_index) in enumerate(zip(rank_indices, full_indices), start=1):
        rank_sq = max(0.0, float(gram[rank_index, rank_index]))
        full_sq = max(0.0, float(gram[full_index, full_index]))
        rank_norm = math.sqrt(rank_sq)
        full_norm = math.sqrt(full_sq)
        dot = float(gram[rank_index, full_index])
        denominator = rank_norm * full_norm
        cosine = dot / denominator if denominator > EPS else 0.0
        cosine = max(-1.0, min(1.0, cosine))
        residual_sq = max(0.0, rank_sq + full_sq - 2.0 * dot)
        projection = dot / full_norm if full_norm > EPS else 0.0
        orthogonal_sq = max(0.0, rank_sq - projection * projection)
        rows.append(
            {
                "round": position,
                "rank1_norm": rank_norm,
                "full_norm": full_norm,
                "norm_ratio": rank_norm / full_norm if full_norm > EPS else 0.0,
                "cosine": cosine,
                "angle_degrees": _safe_angle(cosine),
                "relative_reconstruction_error": math.sqrt(residual_sq) / full_norm
                if full_norm > EPS
                else 0.0,
                "rank1_parallel_signed": projection,
                "rank1_orthogonal_norm": math.sqrt(orthogonal_sq),
                "rank1_orthogonal_ratio": math.sqrt(orthogonal_sq) / rank_norm
                if rank_norm > EPS
                else 0.0,
            }
        )
    return rows


def _orient_columns(coordinates: np.ndarray) -> np.ndarray:
    coordinates = coordinates.copy()
    for column in range(coordinates.shape[1]):
        values = coordinates[:, column]
        pivot = int(np.argmax(np.abs(values)))
        if values[pivot] < 0:
            coordinates[:, column] *= -1
    return coordinates


def uncentered_coordinates(gram: np.ndarray, dimensions: int = 2) -> tuple[np.ndarray, np.ndarray]:
    """Return exact coordinates whose inner products approximate ``gram`` by top components."""

    symmetric = (np.asarray(gram, dtype=np.float64) + np.asarray(gram, dtype=np.float64).T) / 2
    eigenvalues, eigenvectors = np.linalg.eigh(symmetric)
    order = np.argsort(eigenvalues)[::-1]
    eigenvalues = np.maximum(eigenvalues[order], 0.0)
    eigenvectors = eigenvectors[:, order]
    dimensions = min(dimensions, len(eigenvalues))
    coordinates = eigenvectors[:, :dimensions] * np.sqrt(eigenvalues[:dimensions])
    total = float(eigenvalues.sum())
    explained = eigenvalues[:dimensions] / total if total > EPS else np.zeros(dimensions)
    return _orient_columns(coordinates), explained


def normalized_subgram(gram: np.ndarray, indices: list[int]) -> np.ndarray:
    subgram = np.asarray(gram, dtype=np.float64)[np.ix_(indices, indices)]
    return cosine_from_gram(subgram)


def cumulative_coefficient_matrix(
    delta_count: int,
    questioner_indices: list[int],
    solver_indices: list[int],
) -> tuple[np.ndarray, list[str]]:
    """Build Base/Q1..Q5/V1..V5 coefficients in the original delta basis."""

    rows = [np.zeros(delta_count, dtype=np.float64)]
    labels = ["Base"]
    for position in range(len(questioner_indices)):
        row = np.zeros(delta_count, dtype=np.float64)
        row[questioner_indices[: position + 1]] = 1.0
        rows.append(row)
        labels.append(f"Q{position + 1}")
    for position in range(len(solver_indices)):
        row = np.zeros(delta_count, dtype=np.float64)
        row[solver_indices[: position + 1]] = 1.0
        rows.append(row)
        labels.append(f"V{position + 1}")
    return np.stack(rows), labels


def family_indices(delta_ids: list[str], prefix: str) -> list[int]:
    indices = [index for index, delta_id in enumerate(delta_ids) if delta_id.startswith(prefix)]
    return sorted(indices, key=lambda index: int(delta_ids[index].rsplit("r", 1)[1]))


def derive_geometry(gram: np.ndarray, delta_ids: Iterable[str]) -> dict[str, Any]:
    """Derive every global direction metric from one exact delta Gram matrix."""

    delta_ids = list(delta_ids)
    gram = np.asarray(gram, dtype=np.float64)
    if gram.shape != (len(delta_ids), len(delta_ids)):
        raise ValueError("Gram shape does not match delta IDs")
    questioner = family_indices(delta_ids, "questioner_full_")
    solver_rank1 = family_indices(delta_ids, "solver_rank1_")
    solver_full = family_indices(delta_ids, "solver_full_")
    if not (len(questioner) == len(solver_rank1) == len(solver_full) == 5):
        raise ValueError("Expected exactly five deltas in each family")

    families = {
        "questioner_full": questioner,
        "solver_rank1": solver_rank1,
        "solver_full": solver_full,
    }
    cosine = cosine_from_gram(gram)
    adjacent = {name: adjacent_metrics(gram, indices) for name, indices in families.items()}
    historical = {name: historical_metrics(gram, indices) for name, indices in families.items()}
    relex = relex_metrics(gram, solver_rank1, solver_full)

    direction_indices = questioner + solver_rank1
    direction_gram = normalized_subgram(gram, direction_indices)
    direction_coordinates, direction_explained = uncentered_coordinates(direction_gram)

    rank_full_indices = solver_full + solver_rank1
    rank_full_gram = normalized_subgram(gram, rank_full_indices)
    rank_full_coordinates, rank_full_explained = uncentered_coordinates(rank_full_gram)

    coefficients, trajectory_labels = cumulative_coefficient_matrix(
        len(delta_ids), questioner, solver_rank1
    )
    trajectory_gram = coefficients @ gram @ coefficients.T
    trajectory_coordinates, trajectory_explained = uncentered_coordinates(trajectory_gram)

    return {
        "families": families,
        "cosine": cosine,
        "adjacent": adjacent,
        "historical": historical,
        "relex": relex,
        "direction": {
            "labels": [delta_ids[index] for index in direction_indices],
            "coordinates": direction_coordinates,
            "explained": direction_explained,
        },
        "rank_full_direction": {
            "labels": [delta_ids[index] for index in rank_full_indices],
            "coordinates": rank_full_coordinates,
            "explained": rank_full_explained,
        },
        "trajectory": {
            "labels": trajectory_labels,
            "coordinates": trajectory_coordinates,
            "explained": trajectory_explained,
            "gram": trajectory_gram,
        },
    }
