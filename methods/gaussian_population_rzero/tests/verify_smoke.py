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

    population_manifest = root / "questioners/q1/solver_population_manifest.json"
    central_manifest = root / "questioners/q1/solver_feedback_manifest.json"
    if population_manifest.is_file():
        solver_feedback = load(population_manifest)
        feedback_mode = "population"
        assert solver_feedback["population_size"] == 4
        assert solver_feedback["samples_per_question"] == 10
    else:
        solver_feedback = load(central_manifest)
        feedback_mode = "central"
        assert solver_feedback["solver_feedback_mode"] == "central"
        assert solver_feedback["logical_solver_count"] == 1
        assert solver_feedback["perturbed"] is False
        assert solver_feedback["physical_replicas"] == 2
        assert solver_feedback["each_question_evaluated_once"] is True
        assert not population_manifest.exists()
    feedback_files = sorted(
        (root / f"questioners/q1/solver_{feedback_mode}_feedback").glob("*.json")
    )
    assert feedback_files, "no Solver-population feedback audit was persisted"
    for path in feedback_files:
        audit = load(path)
        assert audit["solver_feedback_mode"] == feedback_mode
        assert audit["population_size"] == (4 if feedback_mode == "population" else 1)
        assert audit["physical_replicas"] == 2
        assert audit["samples_per_expert"] == 10
        assert audit["cross_expert_answer_vote"] is False
        expected_rates = 4 if feedback_mode == "population" else 1
        assert all(
            len(rates) == expected_rates
            for rates in audit["question_expert_majority_rates"].values()
        )

    questioner_population = load(root / "datasets/d1/questioner_population_manifest.json")
    assert questioner_population["population_size"] == 4
    assert questioner_population["total_budget"] == 2048
    assert list(questioner_population["expected_quotas"].values()) == [512] * 4
    assert questioner_population["generated_count"] == 2048
    attempt_seeds = [
        seed
        for seeds in questioner_population["observed_attempt_seeds"].values()
        for seed in seeds
    ]
    assert len(attempt_seeds) == 2048
    assert len(set(attempt_seeds)) == 2048

    generated_dir = root / "datasets/d1/generated_question"
    generated = []
    for path in generated_dir.glob("*.json"):
        if path.name.endswith("_results.json") or path.name.endswith("_manifest.json"):
            continue
        generated.extend(load(path))
    assert len(generated) == 2048
    assert len({item["source_sampling_seed"] for item in generated}) == 2048
    by_expert: dict[int, list[int]] = {}
    for item in generated:
        by_expert.setdefault(item["source_expert_index"], []).append(
            item["source_attempt_index"]
        )
    assert {key: sorted(value) for key, value in by_expert.items()} == {
        index: list(range(512)) for index in range(4)
    }
    labeled = []
    for path in generated_dir.glob("*_results.json"):
        labeled.extend(load(path))
    assert labeled, "central Solver produced no valid labels"
    assert all(item["labeler_role"] == "central_solver" for item in labeled)
    assert all(item["labeler_samples"] == 9 for item in labeled)
    assert all(len(item["results"]) == 9 for item in labeled)

    dataset = load(root / "datasets/d1/dataset_manifest.json")
    assert dataset["total_generation_budget"] == 2048
    assert dataset["generated_count"] == 2048
    assert dataset["filtered_count"] > 0
    assert dataset["score_range"] == [0.3, 0.8]
    assert dataset["labeler_role"] == "central_solver"
    assert dataset["labeler_samples"] == 9

    assert (root / "questioners/q1/global_step_1/actor/huggingface").is_dir()
    assert (root / "solvers/s1/global_step_1/actor/huggingface").is_dir()
    assert not list(root.rglob("*expert*checkpoint*")), "expert checkpoints must never persist"
    assert (root / "state/round_1/questioner/_SUCCESS.json").is_file()
    assert (root / "state/round_1/dataset/_SUCCESS.json").is_file()
    assert (root / "state/round_1/solver/_SUCCESS.json").is_file()
    summary = load(root / "summary.json")
    assert summary["rounds"] == 1
    assert summary["expert_checkpoints_persisted"] is False
    print("Production-shaped Gaussian-population smoke artifacts verified")


if __name__ == "__main__":
    main()
