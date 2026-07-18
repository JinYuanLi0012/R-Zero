"""Dependency-free logical population identities and budget allocation."""

from __future__ import annotations

import hashlib
import math
from dataclasses import asdict, dataclass


def stable_seed(*parts: object) -> int:
    payload = "\0".join(str(part) for part in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") & ((1 << 63) - 1)


@dataclass(frozen=True)
class ExpertSpec:
    role: str
    round_index: int
    expert_index: int
    sigma: float
    global_seed: int
    expert_seed: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def make_expert_specs(
    *, role: str, round_index: int, population_size: int, sigma: float, global_seed: int
) -> list[ExpertSpec]:
    if role not in {"questioner", "solver"}:
        raise ValueError(f"unsupported population role: {role!r}")
    if round_index < 1:
        raise ValueError("round_index must be at least 1")
    if population_size < 1:
        raise ValueError("population_size must be positive")
    if not math.isfinite(sigma) or sigma < 0:
        raise ValueError("sigma must be finite and non-negative")
    return [
        ExpertSpec(
            role=role,
            round_index=round_index,
            expert_index=index,
            sigma=float(sigma),
            global_seed=int(global_seed),
            expert_seed=stable_seed(global_seed, role, round_index, index),
        )
        for index in range(population_size)
    ]


def allocate_quotas(total_budget: int, population_size: int) -> list[int]:
    if total_budget < 1:
        raise ValueError("total_budget must be positive")
    if population_size < 1:
        raise ValueError("population_size must be positive")
    if population_size > total_budget:
        raise ValueError("population_size cannot exceed total_budget")
    base, remainder = divmod(total_budget, population_size)
    quotas = [base + (1 if index < remainder else 0) for index in range(population_size)]
    if sum(quotas) != total_budget:
        raise AssertionError("quota allocation did not preserve the total budget")
    return quotas


def assign_experts(population_size: int, worker_index: int, num_workers: int) -> list[int]:
    if population_size < 1 or num_workers < 1:
        raise ValueError("population_size and num_workers must be positive")
    if not 0 <= worker_index < num_workers:
        raise ValueError("worker_index is outside the worker range")
    return list(range(worker_index, population_size, num_workers))
