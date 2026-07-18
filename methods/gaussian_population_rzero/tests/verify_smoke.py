#!/usr/bin/env python3
"""Verify the persisted invariants of a completed one-round GPU smoke run."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load(path: Path):
    if not path.is_file():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_root", type=Path)
    args = parser.parse_args()
    root = args.run_root

    solver_population = load(root / "questioners/q1/solver_population_manifest.json")
    assert solver_population["population_size"] == 3
    assert solver_population["samples_per_question"] == 10
    feedback_files = sorted((root / "questioners/q1/solver_population_feedback").glob("*.json"))
    assert feedback_files, "no Solver-population feedback audit was persisted"
    for path in feedback_files:
        audit = load(path)
        assert audit["population_size"] == 3
        assert audit["samples_per_expert"] == 10
        assert audit["cross_expert_answer_vote"] is False
        assert all(len(rates) == 3 for rates in audit["question_expert_majority_rates"].values())

    questioner_population = load(root / "datasets/d1/questioner_population_manifest.json")
    assert questioner_population["total_budget"] == 7
    assert list(questioner_population["expected_quotas"].values()) == [3, 2, 2]
    assert questioner_population["generated_count"] == 7

    generated_dir = root / "datasets/d1/generated_question"
    labeled = []
    for path in generated_dir.glob("*_results.json"):
        labeled.extend(load(path))
    assert all(item["labeler_role"] == "central_solver" for item in labeled)
    assert all(item["labeler_samples"] == 9 for item in labeled)
    assert all(len(item["results"]) == 9 for item in labeled)

    assert (root / "questioners/q1/global_step_1/actor/huggingface").is_dir()
    assert (root / "solvers/s1/global_step_1/actor/huggingface").is_dir()
    assert not list(root.rglob("*expert*checkpoint*")), "expert checkpoints must never persist"
    print("Gaussian-population one-round smoke artifacts verified")


if __name__ == "__main__":
    main()
