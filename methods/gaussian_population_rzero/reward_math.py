"""Dependency-free Solver-population aggregation rules."""

from __future__ import annotations

from typing import Any, Callable, Sequence


def difficulty_from_expert_rates(rates: Sequence[float]) -> tuple[float, float]:
    if not rates:
        raise ValueError("at least one expert rate is required")
    if any(not 0.0 <= float(rate) <= 1.0 for rate in rates):
        raise ValueError("expert rates must lie in [0, 1]")
    mean_rate = sum(float(rate) for rate in rates) / len(rates)
    return mean_rate, 0.5 - abs(mean_rate - 0.5)


def majority_rate(
    answers: Sequence[str], expected_samples: int, equivalent: Callable[[str, str], bool]
) -> float:
    if len(answers) != expected_samples:
        raise ValueError(f"expected {expected_samples} rollouts, got {len(answers)}")
    representatives: list[str] = []
    counts: list[int] = []
    for answer in answers:
        answer = str(answer or "").strip()
        if not answer:
            continue
        for index, existing in enumerate(representatives):
            if answer == existing or equivalent(answer, existing) or equivalent(existing, answer):
                counts[index] += 1
                break
        else:
            representatives.append(answer)
            counts.append(1)
    return (max(counts) if counts else 0) / expected_samples


def aggregate_population_payload(
    payloads: Sequence[Sequence[dict[str, Any]]],
    *,
    valid_indices: set[int],
    population_size: int,
    expected_samples: int,
) -> dict[int, list[float]]:
    collected: dict[int, dict[int, float]] = {index: {} for index in valid_indices}
    for payload in payloads:
        for item in payload:
            question_index = int(item["question_index"])
            if question_index not in valid_indices:
                continue
            for score in item.get("expert_scores", []):
                expert_index = int(score["expert_index"])
                if int(score["num_samples"]) != expected_samples:
                    raise RuntimeError("solver expert returned an unexpected rollout count")
                if expert_index in collected[question_index]:
                    raise RuntimeError("duplicate solver expert result")
                collected[question_index][expert_index] = float(score["majority_rate"])

    expected_experts = set(range(population_size))
    rates: dict[int, list[float]] = {}
    for question_index, expert_scores in collected.items():
        if set(expert_scores) != expected_experts:
            missing = sorted(expected_experts - set(expert_scores))
            extra = sorted(set(expert_scores) - expected_experts)
            raise RuntimeError(
                f"question {question_index} has incomplete solver population; "
                f"missing={missing}, extra={extra}"
            )
        rates[question_index] = [expert_scores[index] for index in range(population_size)]
    return rates


def split_records(records: Sequence[dict[str, Any]], num_services: int) -> list[list[dict[str, Any]]]:
    """Split records contiguously so every question is handled by one center replica."""
    if num_services < 1:
        raise ValueError("num_services must be positive")
    base, remainder = divmod(len(records), num_services)
    shards = []
    cursor = 0
    for service in range(num_services):
        size = base + (1 if service < remainder else 0)
        shards.append(list(records[cursor : cursor + size]))
        cursor += size
    if cursor != len(records):
        raise AssertionError("center Solver sharding did not preserve all records")
    return shards


def aggregate_center_payload(
    payloads: Sequence[Sequence[dict[str, Any]]],
    *,
    valid_indices: set[int],
    expected_samples: int,
) -> dict[int, float]:
    """Require one and only one unperturbed-center score for every valid question."""
    rates: dict[int, float] = {}
    for payload in payloads:
        for item in payload:
            question_index = int(item["question_index"])
            if question_index not in valid_indices:
                raise RuntimeError(f"central Solver returned unexpected question {question_index}")
            if question_index in rates:
                raise RuntimeError(f"central Solver evaluated question {question_index} more than once")
            if int(item["num_samples"]) != expected_samples:
                raise RuntimeError("central Solver returned an unexpected rollout count")
            rate = float(item["majority_rate"])
            if not 0.0 <= rate <= 1.0:
                raise RuntimeError("central Solver returned a majority rate outside [0, 1]")
            rates[question_index] = rate
    if set(rates) != valid_indices:
        missing = sorted(valid_indices - set(rates))
        raise RuntimeError(f"central Solver feedback is incomplete; missing={missing}")
    return rates
