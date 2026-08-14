#!/usr/bin/env python3
from __future__ import annotations

import argparse
import random
from pathlib import Path

from common import atomic_json, question_hash, sha256_file, software_manifest, stable_int, write_jsonl


EXPECTED_COLUMNS = {"problem", "answer", "score"}


def locate_arrow(cache_root: Path, dataset_name: str) -> Path:
    candidates = sorted(
        path for path in cache_root.rglob(f"{dataset_name}-train.arrow")
        if not path.name.startswith("cache-")
    )
    if len(candidates) != 1:
        raise RuntimeError(
            f"expected exactly one train Arrow for {dataset_name}, found {len(candidates)}: {candidates}"
        )
    return candidates[0]


def load_round(path: Path, round_index: int, expected_rows: int, center: str) -> list[dict]:
    from datasets import Dataset

    dataset = Dataset.from_file(str(path))
    if len(dataset) != expected_rows:
        raise RuntimeError(f"V{round_index} expected {expected_rows} rows, found {len(dataset)}")
    if set(dataset.column_names) != EXPECTED_COLUMNS:
        raise RuntimeError(
            f"V{round_index} expected columns {sorted(EXPECTED_COLUMNS)}, found {dataset.column_names}"
        )
    rows = []
    for row_index, item in enumerate(dataset):
        question = str(item["problem"])
        digest = question_hash(question)
        score = float(item["score"])
        rows.append(
            {
                "question_id": f"v{round_index}:{row_index}:{digest[:16]}",
                "round": round_index,
                "arrow_row_index": row_index,
                "question_hash": digest,
                "question": question,
                "historical_answer": str(item["answer"]),
                "original_majority_rate": score,
                "original_difficulty": min(score, 1.0 - score),
                "question_length": len(question),
                "center_model": center,
            }
        )
    return rows


def stratified_sample(rows: list[dict], round_index: int, seed: int) -> list[dict]:
    ordered = sorted(
        rows,
        key=lambda row: (
            -row["original_difficulty"],
            stable_int(seed, round_index, row["question_id"]),
        ),
    )
    first = len(ordered) // 3
    second = 2 * len(ordered) // 3
    groups = {
        "high": (ordered[:first], 80),
        "mid": (ordered[first:second], 60),
        "low": (ordered[second:], 60),
    }
    selected = []
    for stratum, (population, count) in groups.items():
        rng = random.Random(stable_int(seed, "sample", round_index, stratum))
        picked = rng.sample(population, count)
        inclusion_probability = count / len(population)
        for row in picked:
            selected.append(
                {
                    **row,
                    "stratum": stratum,
                    "stratum_population": len(population),
                    "stratum_sample_size": count,
                    "sampling_weight": 1.0 / inclusion_probability,
                }
            )
    return sorted(selected, key=lambda row: row["question_id"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache-root", type=Path, required=True)
    parser.add_argument("--dataset-names", nargs=3, required=True)
    parser.add_argument("--expected-rows", nargs=3, type=int, required=True)
    parser.add_argument("--centers", nargs=3, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    all_selected = []
    sources = []
    for round_index, (name, expected, center) in enumerate(
        zip(args.dataset_names, args.expected_rows, args.centers), start=1
    ):
        arrow = locate_arrow(args.cache_root, name)
        rows = load_round(arrow, round_index, expected, center)
        selected = stratified_sample(rows, round_index, args.seed)
        write_jsonl(args.output_dir / f"v{round_index}_sample.jsonl", selected)
        all_selected.extend(selected)
        sources.append(
            {
                "round": round_index,
                "dataset_name": name,
                "arrow_path": str(arrow),
                "arrow_sha256": sha256_file(arrow),
                "row_count": len(rows),
                "center_model": center,
            }
        )

    write_jsonl(args.output_dir / "all_samples.jsonl", sorted(all_selected, key=lambda row: row["question_id"]))
    atomic_json(
        args.output_dir / "prepare_manifest.json",
        {
            "seed": args.seed,
            "sources": sources,
            "selected_count": len(all_selected),
            "selected_ids": [row["question_id"] for row in all_selected],
            "software": software_manifest(),
        },
    )
    if len(all_selected) != 600:
        raise AssertionError(f"expected 600 selected questions, got {len(all_selected)}")


if __name__ == "__main__":
    main()
