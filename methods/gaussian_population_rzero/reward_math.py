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
