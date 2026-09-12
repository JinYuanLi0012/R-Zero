"""Equations 7, 8, 15, 16 and the SD-independent row split. No LLM imports."""
from __future__ import annotations

import json
import os
import random
from collections import Counter
from pathlib import Path

import numpy as np


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".tmp-{os.getpid()}")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    temporary.replace(path)


def seenness(embeddings, prototype, tau):
    if tau <= 0:
        raise ValueError("tau must be positive")
    x, w = np.asarray(embeddings, dtype=np.float64), np.asarray(prototype, dtype=np.float64)
    distance = np.sum((x - w) ** 2, axis=-1)
    return np.exp(-distance / tau), distance


def bce_gradient(embeddings, labels, prototype, tau):
    """Analytic full-batch BCE gradient; log(p)=-distance/tau avoids underflow.

    Only protect log(0) at an exact zero distance. No clipping of far-away
    positive examples, normalization, learned radius, or automatic tau tuning.
    """
    x, y, w = (np.asarray(v, dtype=np.float64) for v in (embeddings, labels, prototype))
    p, distance = seenness(x, w, tau)
    a = distance / tau
    one_minus_p = np.maximum(-np.expm1(-a), 1e-12)
    loss = np.mean(y * a - (1 - y) * np.log(one_minus_p))
    factors = y - (1 - y) * p / one_minus_p
    gradient = np.mean(factors[:, None] * (2 / tau) * (w - x), axis=0)
    return float(loss), gradient


def fit_prototype(embeddings, labels, previous, *, tau, learning_rate, steps, ema_rate):
    x, y = np.asarray(embeddings, dtype=np.float64), np.asarray(labels, dtype=np.float64)
    if x.ndim != 2 or len(x) != len(y) or not len(x):
        raise ValueError("expected nonempty aligned embeddings and labels")
    if not np.isfinite(x).all() or set(np.unique(y)) != {0.0, 1.0}:
        raise ValueError("finite features and both binary classes are required")
    if not (tau > 0 and learning_rate > 0 and steps >= 1 and 0 < ema_rate <= 1):
        raise ValueError("invalid SD hyperparameters")
    # B.2.1: first initialization AFTER S1, using the current curated pool centroid.
    old = x.mean(axis=0) if previous is None else np.asarray(previous, dtype=np.float64)
    if old.shape != (x.shape[1],):
        raise ValueError("prototype dimension does not match solver embeddings")
    fitted = old.copy()
    losses = []
    for _ in range(steps):
        loss, gradient = bce_gradient(x, y, fitted, tau)
        losses.append(loss)
        fitted -= learning_rate * gradient
    updated = (1 - ema_rate) * old + ema_rate * fitted
    if not np.isfinite(updated).all():
        raise ValueError("non-finite prototype; inspect SD diagnostics")
    p, distance = seenness(x, updated, tau)
    diagnostics = {
        "training_bce_before_steps": losses,
        "training_bce_after_ema": bce_gradient(x, y, updated, tau)[0],
        "training_accuracy_at_0p5": float(np.mean((p >= 0.5) == y)),
        "seen_probability_mean": float(p.mean()),
        "seen_probability_for_seen": float(p[y == 1].mean()),
        "seen_probability_for_holdout": float(p[y == 0].mean()),
        "novelty_std": float((1 - p).std()),
        "near_one_novelty_fraction": float(np.mean(p < 1e-6)),
        "distance_squared_mean": float(distance.mean()),
        "distance_squared_p50": float(np.median(distance)),
        "prototype_norm": float(np.linalg.norm(updated)),
        "prototype_change_norm": float(np.linalg.norm(updated - old)),
    }
    return updated, diagnostics


def curate_and_split(rows, *, votes=10, min_count=3, max_count=7, seed=42):
    """Count-band filtering, then random 1:1 ROW split; no SD or dedup decisions."""
    curated = []
    for index, row in enumerate(rows):
        answers = row.get("results", [])
        score = row.get("score")
        if not answers or not isinstance(score, (int, float)):
            continue
        if not row.get("question", "").strip() or row.get("answer") in (None, "", "None"):
            continue
        # Stock Phase-B scorer reports majority / NONEMPTY answers. Recover the
        # integer count and implement the paper's explicit [3,7] count filter.
        count = round(score * len(answers))
        if not min_count <= count <= max_count:
            continue
        curated.append({**row, "source_row_id": index, "majority_count": count,
                        "baseline_nonempty_score": score, "score": count / votes})
    random.Random(seed).shuffle(curated)
    dropped = curated.pop() if len(curated) % 2 else None
    half = len(curated) // 2
    seen, unseen = curated[:half], curated[half:]
    for label, group in [(1, seen), (0, unseen)]:
        for row in group:
            row["sd_label"] = label
    seen_texts = {row["question"] for row in seen}
    unseen_texts = {row["question"] for row in unseen}
    diagnostics = {
        "input_rows": len(rows), "curated_rows": len(curated),
        "seen_rows": half, "unseen_rows": half,
        "odd_row_dropped_source_id": None if dropped is None else dropped["source_row_id"],
        "exact_question_overlap_across_split": len(seen_texts & unseen_texts),
        "unique_questions": len(seen_texts | unseen_texts),
        "majority_count_histogram": dict(Counter(row["majority_count"] for row in curated)),
    }
    return seen, unseen, diagnostics
