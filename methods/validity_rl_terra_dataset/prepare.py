#!/usr/bin/env python3
"""Load V1-V5, globally deduplicate question text, and make a blind fixed sample."""
from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Any

from common import atomic_json, normalize_question, question_hash, stable_int, write_jsonl


DEFAULT_SOURCES = {
    f"v{index}": f"jinyuan222/qwen3_4b_fullrun_authorsettings_solver_v{index}"
    for index in range(1, 6)
}
QUESTION_FIELDS = ("problem", "question", "prompt")


def parse_sources(values: list[str] | None) -> dict[str, str]:
    if not values:
        return dict(DEFAULT_SOURCES)
    result: dict[str, str] = {}
    for value in values:
        key, separator, location = value.partition("=")
        key = key.lower()
        if not separator or key not in DEFAULT_SOURCES or not location:
            raise ValueError("--source must look like v1=dataset-or-file (v1 through v5 exactly once)")
        result[key] = location
    if set(result) != set(DEFAULT_SOURCES):
        raise ValueError(f"--source must provide exactly {sorted(DEFAULT_SOURCES)}")
    return result


def extract_question(row: dict[str, Any], explicit_field: str | None = None) -> tuple[str, str]:
    fields = (explicit_field,) if explicit_field else QUESTION_FIELDS
    for field in fields:
        if not field or field not in row or row[field] is None:
            continue
        value = row[field]
        if isinstance(value, list):
            user_messages = [
                message.get("content") for message in value
                if isinstance(message, dict) and message.get("role") == "user"
            ]
            value = user_messages[-1] if user_messages else None
        elif isinstance(value, dict):
            value = value.get("content") or value.get("question") or value.get("problem")
        if isinstance(value, str) and normalize_question(value):
            return value, field
    raise ValueError(f"could not find a non-empty question in fields {fields}; row keys={sorted(row)}")


def load_local(path: Path) -> list[dict[str, Any]]:
    if path.suffix == ".jsonl":
        with path.open(encoding="utf-8") as handle:
            return [json.loads(line) for line in handle if line.strip()]
    if path.suffix == ".json":
        value = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(value, dict):
            for key in ("train", "data", "rows"):
                if isinstance(value.get(key), list):
                    return value[key]
        if isinstance(value, list):
            return value
        raise ValueError(f"unsupported JSON shape in {path}")
    from datasets import load_dataset

    extension = "parquet" if path.suffix == ".parquet" else "arrow"
    return list(load_dataset(extension, data_files=str(path), split="train"))


def load_source(location: str, revision: str | None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    path = Path(location).expanduser()
    if path.exists():
        rows = load_local(path)
        return rows, {"location": str(path.resolve()), "revision": None, "split": "local"}

    from datasets import DatasetDict, load_dataset
    from huggingface_hub import HfApi

    resolved_revision = HfApi().dataset_info(location, revision=revision).sha
    loaded = load_dataset(location, revision=resolved_revision)
    if isinstance(loaded, DatasetDict):
        split = "train" if "train" in loaded else next(iter(loaded)) if len(loaded) == 1 else None
        if split is None:
            raise ValueError(f"{location} has multiple splits but no train split: {list(loaded)}")
        dataset = loaded[split]
    else:
        dataset, split = loaded, "train"
    return list(dataset), {"location": location, "revision": resolved_revision, "split": split}


def sample_rows(
    sources: dict[str, list[dict[str, Any]]], per_round: int, train_per_round: int,
    seed: int, question_field: str | None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not 0 <= train_per_round <= per_round:
        raise ValueError("train-per-round must be between zero and per-round")
    occurrences: dict[str, list[dict[str, Any]]] = defaultdict(list)
    field_by_round: dict[str, str] = {}
    raw_counts: dict[str, int] = {}
    for round_name in sorted(sources):
        raw_counts[round_name] = len(sources[round_name])
        for row_index, row in enumerate(sources[round_name]):
            question, detected_field = extract_question(row, question_field)
            field_by_round.setdefault(round_name, detected_field)
            digest = question_hash(question)
            occurrences[digest].append({
                "round": round_name, "source_row_index": row_index,
                "question": question, "question_hash": digest,
            })

    # Assign each cross-round duplicate to one deterministic, seed-dependent owner before sampling.
    owned: dict[str, list[dict[str, Any]]] = {name: [] for name in sources}
    for digest, candidates in occurrences.items():
        owner = min(candidates, key=lambda row: stable_int(seed, "dedupe-owner", digest, row["round"]))
        owned[owner["round"]].append(owner)

    sampled: list[dict[str, Any]] = []
    for round_name in sorted(owned):
        population = owned[round_name]
        if len(population) < per_round:
            raise RuntimeError(
                f"{round_name} has only {len(population)} globally unique owned questions; "
                f"cannot sample {per_round}"
            )
        rng = random.Random(stable_int(seed, "sample", round_name))
        selected = rng.sample(population, per_round)
        rng.shuffle(selected)
        for index, row in enumerate(selected):
            opaque_id = f"q_{stable_int(seed, 'opaque', row['question_hash']):016x}"
            sampled.append({
                "id": opaque_id,
                "round": round_name,
                "question": row["question"],
                "question_hash": row["question_hash"],
                "source_row_index": row["source_row_index"],
                "split": "train" if index < train_per_round else "validation",
            })
    if len({row["question_hash"] for row in sampled}) != len(sampled):
        raise AssertionError("sample contains duplicate normalized question text")
    sampled.sort(key=lambda row: (row["round"], row["split"], row["id"]))
    stats = {
        "raw_rows_by_round": raw_counts,
        "detected_question_field_by_round": field_by_round,
        "unique_normalized_questions": len(occurrences),
        "duplicate_occurrences_removed": sum(len(rows) - 1 for rows in occurrences.values()),
        "owned_unique_questions_by_round": {key: len(value) for key, value in owned.items()},
    }
    return sampled, stats


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--source", action="append", help="Override all sources: v1=repo-or-path")
    parser.add_argument("--revision", help="Optional shared Hugging Face revision; resolved SHAs are recorded")
    parser.add_argument("--question-field", help="Override automatic problem/question/prompt detection")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--per-round", type=int, default=460)
    parser.add_argument("--train-per-round", type=int, default=400)
    args = parser.parse_args()

    locations = parse_sources(args.source)
    rows_by_round, provenance = {}, {}
    for round_name, location in sorted(locations.items()):
        rows_by_round[round_name], provenance[round_name] = load_source(location, args.revision)
    sampled, stats = sample_rows(
        rows_by_round, args.per_round, args.train_per_round, args.seed, args.question_field
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.output_dir / "sampled_questions.jsonl", sampled)
    write_jsonl(args.output_dir / "terra_blind_input.jsonl", [
        {"id": row["id"], "question": row["question"]} for row in sampled
    ])
    atomic_json(args.output_dir / "prepare_manifest.json", {
        "sampling_seed": args.seed,
        "per_round": args.per_round,
        "train_per_round": args.train_per_round,
        "validation_per_round": args.per_round - args.train_per_round,
        "source_datasets": provenance,
        "sampling_statistics": stats,
        "sampled_count": len(sampled),
    })


if __name__ == "__main__":
    main()
