#!/usr/bin/env python3
"""Cluster answers and compute total, within-expert, and epistemic entropy."""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "gaussian_population_rzero"))
from grading import answers_equivalent  # noqa: E402

from common import INVALID_CLASS, clip_mutual_information, entropy_from_counts, read_jsonl, sigma_key


def cluster_answers(records: list[dict]) -> tuple[list[str], list[str]]:
    """Return deterministic class ids and their representative answers."""
    representatives: list[str] = []
    class_ids: list[str] = []
    for record in sorted(records, key=lambda row: (row["expert_index"], row["sample_index"])):
        answer = str(record.get("extracted_answer") or "").strip()
        if not answer:
            class_ids.append(INVALID_CLASS)
            continue
        for index, representative in enumerate(representatives):
            if answers_equivalent(answer, representative):
                class_ids.append(f"answer_{index}")
                break
        else:
            class_ids.append(f"answer_{len(representatives)}")
            representatives.append(answer)
    return class_ids, representatives


def metrics_from_classes(
    records: list[dict], class_ids: list[str], population_size: int
) -> dict:
    paired = list(zip(sorted(records, key=lambda row: (row["expert_index"], row["sample_index"])), class_ids))

    def compute(include_invalid: bool) -> tuple[float, float, float, list[dict]]:
        selected = [(row, cls) for row, cls in paired if include_invalid or cls != INVALID_CLASS]
        expert_rows = []
        within_values = []
        expert_probabilities = []
        for expert_index in range(population_size):
            counts = Counter(cls for row, cls in selected if row["expert_index"] == expert_index)
            if counts or include_invalid:
                value = entropy_from_counts(counts.values())
                within_values.append(value)
                count_total = sum(counts.values())
                expert_probabilities.append(
                    {answer_class: count / count_total for answer_class, count in counts.items()}
                )
            else:
                value = None
            expert_rows.append(
                {
                    "expert_index": expert_index,
                    "counts": dict(sorted(counts.items())),
                    "entropy": value,
                    "valid_count": sum(counts.values()),
                }
            )
        mixture = Counter()
        for probabilities in expert_probabilities:
            for answer_class, probability in probabilities.items():
                mixture[answer_class] += probability / len(expert_probabilities)
        total_entropy = -sum(
            probability * math.log(probability) for probability in mixture.values() if probability > 0
        )
        within_entropy = sum(within_values) / len(within_values) if within_values else 0.0
        epistemic = clip_mutual_information(total_entropy - within_entropy)
        return total_entropy, within_entropy, epistemic, expert_rows

    h_total, h_within, u_epi, expert_distributions = compute(True)
    cv_total, cv_within, cv_u_epi, cv_experts = compute(False)
    total_counts = Counter(class_ids)
    return {
        "answer_class_counts": dict(sorted(total_counts.items())),
        "expert_distributions": expert_distributions,
        "valid_completion_count": sum(value for key, value in total_counts.items() if key != INVALID_CLASS),
        "invalid_completion_count": total_counts.get(INVALID_CLASS, 0),
        "extraction_success_rate": 1.0 - total_counts.get(INVALID_CLASS, 0) / len(class_ids),
        "h_total": h_total,
        "h_within": h_within,
        "u_epi": u_epi,
        "u_epi_norm": u_epi / math.log(population_size) if population_size > 1 else 0.0,
        "conditional_valid_h_total": cv_total,
        "conditional_valid_h_within": cv_within,
        "conditional_valid_u_epi": cv_u_epi,
        "conditional_valid_u_epi_norm": cv_u_epi / math.log(population_size) if population_size > 1 else 0.0,
        "conditional_valid_expert_distributions": cv_experts,
    }


def read_raw_shards(directory: Path) -> list[dict]:
    paths = sorted(directory.glob("expert_*.parquet"))
    if not paths:
        raise RuntimeError(f"no expert Parquet files found in {directory}")
    rows = []
    for path in paths:
        rows.extend(pq.read_table(path).to_pylist())
    return rows


def atomic_parquet(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.tmp-{os.getpid()}")
    pq.write_table(pa.Table.from_pylist(rows), temporary, compression="zstd")
    os.replace(temporary, path)


def aggregate_sigma(
    input_path: Path,
    raw_directory: Path,
    output_path: Path,
    population_size: int,
    samples: int,
) -> None:
    questions = {row["question_id"]: row for row in read_jsonl(input_path)}
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in read_raw_shards(raw_directory):
        grouped[row["question_id"]].append(row)
    if set(grouped) != set(questions):
        raise RuntimeError("raw completion question IDs do not match the prepared input")
    summaries = []
    expected = population_size * samples
    for question_id in sorted(grouped):
        records = grouped[question_id]
        if len(records) != expected:
            raise RuntimeError(f"{question_id} has {len(records)} completions; expected {expected}")
        pairs = {(row["expert_index"], row["sample_index"]) for row in records}
        if len(pairs) != expected:
            raise RuntimeError(f"{question_id} has duplicate or missing expert/sample indices")
        class_ids, representatives = cluster_answers(records)
        metrics = metrics_from_classes(records, class_ids, population_size)
        historical_answer = str(questions[question_id].get("historical_answer") or "")
        matching_classes = {
            f"answer_{index}" for index, representative in enumerate(representatives)
            if answers_equivalent(representative, historical_answer)
        }
        historical_matches = sum(answer_class in matching_classes for answer_class in class_ids)
        base = questions[question_id]
        sigma = float(records[0]["sigma"])
        summaries.append(
            {
                **base,
                "sigma": sigma,
                "completion_count": len(records),
                "historical_answer_agreement_rate": historical_matches / len(records),
                "answer_representatives_json": json.dumps(representatives, ensure_ascii=False),
                **{
                    key + "_json" if isinstance(value, (dict, list)) else key: (
                        json.dumps(value, ensure_ascii=False, sort_keys=True)
                        if isinstance(value, (dict, list)) else value
                    )
                    for key, value in metrics.items()
                },
            }
        )
    atomic_parquet(output_path, summaries)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--sigmas", required=True)
    parser.add_argument("--population-size", type=int, required=True)
    parser.add_argument("--samples", type=int, required=True)
    args = parser.parse_args()
    for sigma in (float(value) for value in args.sigmas.split(",") if value):
        key = sigma_key(sigma)
        aggregate_sigma(
            args.input,
            args.raw_root / f"sigma_{key}",
            args.output_dir / f"sigma_{key}.parquet",
            args.population_size,
            args.samples,
        )


if __name__ == "__main__":
    main()
