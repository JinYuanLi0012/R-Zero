#!/usr/bin/env python3
"""Questioner reward using within-expert confidence and no cross-expert vote."""

from __future__ import annotations

import json
import os
import random
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence

import numpy as np
import regex as re
import requests
from mathruler.grader import extract_boxed_content
from nltk.translate.bleu_score import SmoothingFunction, sentence_bleu
from sklearn.cluster import AgglomerativeClustering

from reward_math import aggregate_population_payload, difficulty_from_expert_rates, majority_rate


def _bleu_distance_matrix(sentences: Sequence[str]) -> np.ndarray:
    size = len(sentences)
    distance = np.zeros((size, size))
    smoother = SmoothingFunction().method1
    for left in range(size):
        for right in range(left, size):
            if left == right:
                score = 1.0
            else:
                score = sentence_bleu(
                    [sentences[right].split()],
                    sentences[left].split(),
                    smoothing_function=smoother,
                )
            distance[left, right] = distance[right, left] = 1.0 - score
    return distance


def cluster_share_per_problem(
    problems: Sequence[str], distance_threshold: float = 0.5, linkage: str = "average"
) -> list[float]:
    if not problems:
        return []
    if len(problems) == 1:
        return [1.0]
    labels = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=distance_threshold,
        metric="precomputed",
        linkage=linkage,
    ).fit_predict(_bleu_distance_matrix(problems))
    sizes = Counter(labels)
    total = len(problems)
    return [sizes[label] / total for label in labels]


def _parsed_question(predict: str) -> tuple[str, str]:
    questions = re.findall(r"<question>(.*?)</question>", predict, re.DOTALL)
    boxed = extract_boxed_content(predict)
    if isinstance(boxed, (list, tuple)):
        answer = str(boxed[-1]).strip() if boxed else ""
    else:
        answer = str(boxed or "").strip()
    return (questions[-1].strip(), answer) if questions and answer else ("", "")


def _request_one(*, port: int, request_path: Path) -> list[dict[str, Any]]:
    output_path = request_path.with_name(request_path.stem + "_results.json")
    # Match standard R-Zero's caller_penalty.py: a population evaluation is one
    # blocking HTTP request with no client deadline and no automatic replay.
    # A requests timeout cannot cancel the in-flight vLLM generation; retrying
    # would only queue a complete duplicate evaluation behind MODEL_LOCK.
    response = requests.get(
        f"http://127.0.0.1:{port}/evaluate",
        params={"name": str(request_path)},
    )
    response.raise_for_status()
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    output_path.unlink(missing_ok=True)
    request_path.unlink(missing_ok=True)
    return payload


def query_solver_population(
    records: list[dict[str, Any]],
    *,
    num_services: int,
    port_base: int,
) -> list[list[dict[str, Any]]]:
    storage = Path(os.environ["STORAGE_PATH"]) / "temp_results"
    storage.mkdir(parents=True, exist_ok=True)
    token = f"{time.time_ns()}_{os.getpid()}_{random.randint(0, 99999)}"
    paths = []
    for service in range(num_services):
        path = storage / f"gaussian_population_{token}_service{service}.json"
        path.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
        paths.append(path)

    payloads: list[list[dict[str, Any]] | None] = [None] * num_services
    with ThreadPoolExecutor(max_workers=num_services) as executor:
        futures = {
            executor.submit(
                _request_one,
                port=port_base + service,
                request_path=paths[service],
            ): service
            for service in range(num_services)
        }
        for future in as_completed(futures):
            payloads[futures[future]] = future.result()
    if any(payload is None for payload in payloads):
        raise RuntimeError("one or more solver population services returned no payload")
    return [payload for payload in payloads if payload is not None]


def _write_feedback_audit(
    rates: dict[int, list[float]], *, population_size: int, expert_samples: int
) -> None:
    configured = os.getenv("SOLVER_POPULATION_AUDIT_DIR")
    if not configured:
        return
    directory = Path(configured)
    directory.mkdir(parents=True, exist_ok=True)
    token = f"{time.time_ns()}_{os.getpid()}_{random.randint(0, 99999)}"
    path = directory / f"feedback_{token}.json"
    temporary = path.with_name(f"{path.name}.tmp")
    temporary.write_text(
        json.dumps(
            {
                "population_size": population_size,
                "samples_per_expert": expert_samples,
                "valid_question_count": len(rates),
                "question_expert_majority_rates": {
                    str(index): values for index, values in sorted(rates.items())
                },
                "cross_expert_answer_vote": False,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def compute_score(
    predicts: list[str],
    ground_truths: list[str],
    *,
    num_services: int,
    port_base: int,
    population_size: int,
    expert_samples: int = 10,
    distance_threshold: float = 0.5,
    **_: Any,
) -> list[dict[str, float]]:
    del ground_truths  # R-Zero questioner reward is self-contained.
    parsed = [_parsed_question(predict) for predict in predicts]
    records = [
        {"question_index": index, "question": question, "answer": answer}
        for index, (question, answer) in enumerate(parsed)
    ]
    valid_indices = {index for index, (question, answer) in enumerate(parsed) if question and answer}
    if not valid_indices:
        penalties = cluster_share_per_problem(
            [question for question, _ in parsed], distance_threshold=distance_threshold
        )
        return [
            {"overall": -1.0, "format": 0.0, "difficulty": 0.0, "similarity": penalty}
            for penalty in penalties
        ]
    payloads = query_solver_population(
        records,
        num_services=num_services,
        port_base=port_base,
    )
    rates = aggregate_population_payload(
        payloads,
        valid_indices=valid_indices,
        population_size=population_size,
        expected_samples=expert_samples,
    )
    _write_feedback_audit(
        rates, population_size=population_size, expert_samples=expert_samples
    )
    penalties = cluster_share_per_problem(
        [question for question, _ in parsed], distance_threshold=distance_threshold
    )
    scores: list[dict[str, float]] = []
    for index, ((question, answer), similarity) in enumerate(zip(parsed, penalties)):
        if not question or not answer:
            scores.append(
                {"overall": -1.0, "format": 0.0, "difficulty": 0.0, "similarity": similarity}
            )
            continue
        mean_rate, difficulty = difficulty_from_expert_rates(rates[index])
        scores.append(
            {
                "overall": difficulty - similarity,
                "format": 1.0,
                "difficulty": difficulty,
                "solver_confidence": mean_rate,
                "similarity": similarity,
            }
        )
    return scores
