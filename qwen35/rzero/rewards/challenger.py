"""Released Challenger reward adapted to verl's official BatchRewardManager.

The algorithm is unchanged: difficulty is ``min(p, 1-p)`` from a frozen
Solver's pass fraction and the BLEU-cluster population share is subtracted as a
diversity penalty.
"""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from qwen35.rzero.rewards.common import parse_questioner_response


def _split_balanced(items: list[dict[str, str]], count: int) -> list[list[dict[str, str]]]:
    quotient, remainder = divmod(len(items), count)
    return [
        items[index * quotient + min(index, remainder) : (index + 1) * quotient + min(index + 1, remainder)]
        for index in range(count)
    ]


def _score_partition(endpoint: str, items: list[dict[str, str]], timeout: float) -> list[dict[str, Any]]:
    if not items:
        return []
    import requests

    response = requests.post(f"{endpoint.rstrip('/')}/score", json={"items": items}, timeout=timeout)
    response.raise_for_status()
    results = response.json()["results"]
    if len(results) != len(items):
        raise RuntimeError(f"Solver endpoint {endpoint} returned {len(results)} results for {len(items)} inputs")
    return results


def call_solver_pool(
    items: list[dict[str, str]], endpoints: list[str], timeout: float = 7200
) -> list[dict[str, Any]]:
    if not endpoints:
        raise RuntimeError("RZERO_SOLVER_ENDPOINTS is empty")
    partitions = _split_balanced(items, len(endpoints))
    with ThreadPoolExecutor(max_workers=len(endpoints)) as executor:
        futures = [executor.submit(_score_partition, endpoint, part, timeout) for endpoint, part in zip(endpoints, partitions)]
        partition_results = [future.result() for future in futures]
    return [item for partition in partition_results for item in partition]


def cluster_share_per_problem(
    problems: list[str], distance_threshold: float = 0.5, linkage: str = "average"
) -> list[float]:
    if not problems:
        return []
    import numpy as np
    from nltk.translate.bleu_score import SmoothingFunction, sentence_bleu
    from sklearn.cluster import AgglomerativeClustering

    count = len(problems)
    distances = np.zeros((count, count))
    smoother = SmoothingFunction().method1
    for left in range(count):
        for right in range(left, count):
            score = 1.0 if left == right else sentence_bleu(
                [problems[right].split()], problems[left].split(), smoothing_function=smoother
            )
            distances[left, right] = distances[right, left] = 1 - score
    labels = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=distance_threshold,
        metric="precomputed",
        linkage=linkage,
    ).fit_predict(distances)
    sizes = {int(label): int((labels == label).sum()) for label in labels}
    return [sizes[int(label)] / count for label in labels]


def score_from_solver_results(
    parsed: list[dict[str, str]],
    solver_results: list[dict[str, Any]],
    distance_threshold: float = 0.5,
    cluster_fn=cluster_share_per_problem,
) -> list[dict[str, float]]:
    if len(parsed) != len(solver_results):
        raise ValueError("parsed responses and Solver results must remain aligned")
    penalties = cluster_fn([item["question"] for item in solver_results], distance_threshold)
    if len(penalties) != len(solver_results):
        raise RuntimeError("cluster penalty cardinality changed")
    scores = []
    for source, result, penalty in zip(parsed, solver_results, penalties):
        valid = bool(source["question"])
        pass_fraction = float(result["score"])
        difficulty = min(pass_fraction, 1 - pass_fraction) if valid else -1.0
        scores.append(
            {
                "score": difficulty - penalty,
                "format": 1.0 if valid else 0.0,
                "solver_difficulty": difficulty,
                "diversity_penalty": penalty,
            }
        )
    return scores


def compute_score(
    data_sources: list[str],
    solution_strs: list[str],
    ground_truths: list[str | None],
    extra_infos: list[dict[str, Any]],
    distance_threshold: float = 0.5,
    **_: Any,
) -> list[dict[str, float]]:
    del data_sources, ground_truths, extra_infos
    parsed = [parse_questioner_response(text) for text in solution_strs]
    endpoints = [item.strip() for item in os.environ.get("RZERO_SOLVER_ENDPOINTS", "").split(",") if item.strip()]
    solver_results = call_solver_pool(parsed, endpoints)
    return score_from_solver_results(parsed, solver_results, distance_threshold)
