#!/usr/bin/env python3
"""Validate the public environment interface before allocating GPUs."""

from __future__ import annotations

import math
import os


def integer(name: str, minimum: int = 1) -> int:
    value = int(os.environ[name])
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    return value


def sigma(name: str) -> float:
    value = float(os.environ[name])
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"{name} must be finite and non-negative")
    return value


def gpu_list(name: str) -> list[str]:
    values = [value.strip() for value in os.environ[name].split(",") if value.strip()]
    if not values or len(set(values)) != len(values):
        raise ValueError(f"{name} must be a non-empty list of unique GPU ids")
    return values


def bounded_float(name: str, *, low: float, high: float) -> float:
    value = float(os.environ[name])
    if not math.isfinite(value) or not low < value <= high:
        raise ValueError(f"{name} must satisfy {low} < value <= {high}")
    return value


def main() -> None:
    rounds = integer("NUM_ROUNDS")
    questioners = integer("QUESTIONER_POPULATION_SIZE")
    solvers = integer("SOLVER_POPULATION_SIZE")
    budget = integer("QUESTION_TOTAL_BUDGET")
    if questioners > budget:
        raise ValueError("QUESTIONER_POPULATION_SIZE cannot exceed QUESTION_TOTAL_BUDGET")
    if integer("TENSOR_PARALLEL_SIZE") != 1:
        raise ValueError("the first implementation supports only TENSOR_PARALLEL_SIZE=1")
    if integer("SOLVER_EXPERT_SAMPLES", 2) != 10:
        raise ValueError("SOLVER_EXPERT_SAMPLES must be 10 to match standard R-Zero")
    if integer("SOLVER_LABEL_SAMPLES", 2) != 9:
        raise ValueError("SOLVER_LABEL_SAMPLES must be 9 to match standard R-Zero")
    if integer("SOLVER_EXPERT_RETRIES", 0) != 1:
        raise ValueError("SOLVER_EXPERT_RETRIES must be exactly 1")
    questioner_merge = integer("QUESTIONER_MERGE_STEP")
    questioner_save = integer("QUESTIONER_SAVE_FREQ")
    if questioner_merge > integer("QUESTIONER_MAX_STEPS"):
        raise ValueError("QUESTIONER_MERGE_STEP cannot exceed QUESTIONER_MAX_STEPS")
    if questioner_merge % questioner_save:
        raise ValueError("QUESTIONER_MERGE_STEP must be emitted by QUESTIONER_SAVE_FREQ")
    solver_merge = integer("SOLVER_MERGE_STEP")
    solver_save = integer("SOLVER_SAVE_FREQ")
    if solver_merge > integer("SOLVER_MAX_STEPS"):
        raise ValueError("SOLVER_MERGE_STEP cannot exceed SOLVER_MAX_STEPS")
    if solver_merge % solver_save:
        raise ValueError("SOLVER_MERGE_STEP must be emitted by SOLVER_SAVE_FREQ")
    sigma("QUESTIONER_NOISE_SIGMA")
    sigma("SOLVER_NOISE_SIGMA")
    bounded_float("SOLVER_EXPERT_GPU_MEMORY_UTILIZATION", low=0.0, high=1.0)
    bounded_float("QUESTION_GENERATION_GPU_MEMORY_UTILIZATION", low=0.0, high=1.0)
    bounded_float("SOLVER_LABEL_GPU_MEMORY_UTILIZATION", low=0.0, high=1.0)
    minimum_score = float(os.environ["DATASET_MIN_SCORE"])
    maximum_score = float(os.environ["DATASET_MAX_SCORE"])
    if not 0.0 <= minimum_score <= maximum_score <= 1.0:
        raise ValueError("dataset score range must lie in [0, 1]")
    qtrain = set(gpu_list("QUESTIONER_TRAIN_GPU_IDS"))
    sexpert = set(gpu_list("SOLVER_EXPERT_GPU_IDS"))
    if qtrain & sexpert:
        raise ValueError("Questioner training GPUs and Solver expert GPUs must be disjoint")
    gpu_list("QUESTION_GENERATION_GPU_IDS")
    print(
        f"validated rounds={rounds} Kq={questioners} Ks={solvers} B={budget} "
        f"sigma_q={os.environ['QUESTIONER_NOISE_SIGMA']} sigma_s={os.environ['SOLVER_NOISE_SIGMA']}"
    )


if __name__ == "__main__":
    main()
