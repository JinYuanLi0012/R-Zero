"""Merge scored shards into the canonical local Solver Parquet dataset."""

from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path

from qwen35.rzero.data import solver_record


def repeat_for_integration(records: list[dict], minimum_rows: int) -> list[dict]:
    """Deterministically fill a non-formal integration batch.

    This is intentionally opt-in and must never be used by the formal profile.
    It preserves the curated examples and only supplies enough repeated rows for
    verl's drop-last training dataloader to execute one integration step.
    """
    if minimum_rows <= 0:
        raise ValueError("minimum_rows must be positive")
    if not records or len(records) >= minimum_rows:
        return records
    unique_count = len(records)
    expanded = list(records)
    while len(expanded) < minimum_rows:
        source_index = len(expanded) % unique_count
        row = copy.deepcopy(records[source_index])
        extra_info = dict(row.get("extra_info") or {})
        extra_info.update(
            {
                "index": len(expanded),
                "integration_repeat": len(expanded) // unique_count,
                "integration_source_index": source_index,
            }
        )
        row["extra_info"] = extra_info
        expanded.append(row)
    return expanded


def filter_candidates(
    rows: list[dict], minimum: float, maximum: float, deduplicate_questions: bool = False
) -> tuple[list[dict], int, int]:
    """Apply released difficulty/answer filtering, optionally deduplicating.

    Released R-Zero preserves every accepted row in shard order. Deduplication
    remains an explicit integration-only option and is never enabled formally.
    """
    accepted = [
        item
        for item in rows
        if minimum <= float(item.get("score", -1)) <= maximum
        and item.get("answer") not in {"", "None", None}
    ]
    if not deduplicate_questions:
        return accepted, len(accepted), 0
    unique: dict[str, dict] = {}
    for item in accepted:
        key = " ".join(str(item["question"]).split())
        unique.setdefault(key, item)
    return list(unique.values()), len(accepted), len(accepted) - len(unique)


def curate(
    inputs: list[Path],
    output: Path,
    minimum: float,
    maximum: float,
    fallback: Path | None = None,
    minimum_rows: int = 1,
    repeat_to_minimum: bool = False,
    deduplicate_questions: bool = False,
) -> dict[str, int | bool]:
    rows = []
    for path in inputs:
        rows.extend(json.loads(path.read_text(encoding="utf-8")))
    selected, accepted_count, duplicates_removed = filter_candidates(
        rows, minimum, maximum, deduplicate_questions
    )
    records = [
        solver_record(item["question"], item["answer"], float(item["score"]), index)
        for index, item in enumerate(selected)
    ]
    from datasets import Dataset, load_dataset

    used_fallback = False
    if not records and fallback:
        fallback_dataset = load_dataset("parquet", data_files=str(fallback), split="train")
        records = [dict(fallback_dataset[index]) for index in range(min(8, len(fallback_dataset)))]
        used_fallback = True
    if not records:
        raise RuntimeError("difficulty filtering produced an empty Solver dataset")
    unique_rows = len(records)
    if unique_rows < minimum_rows:
        if not repeat_to_minimum:
            raise RuntimeError(
                f"curated Solver dataset has {unique_rows} rows, fewer than the required "
                f"training batch of {minimum_rows}"
            )
        records = repeat_for_integration(records, minimum_rows)

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.name}.tmp-{os.getpid()}")
    Dataset.from_list(records).to_parquet(temporary)
    os.replace(temporary, output)
    return {
        "scored": len(rows),
        "accepted": accepted_count,
        "deduplicated": unique_rows,
        "deduplication_enabled": deduplicate_questions,
        "duplicates_removed": duplicates_removed,
        "training_rows": len(records),
        "repeated_for_integration": len(records) - unique_rows,
        "used_smoke_fallback": used_fallback,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--min-score", type=float, default=0.3)
    parser.add_argument("--max-score", type=float, default=0.8)
    parser.add_argument("--metadata", type=Path)
    parser.add_argument("--fallback", type=Path)
    parser.add_argument("--minimum-rows", type=int, default=1)
    parser.add_argument("--repeat-to-minimum", action="store_true")
    parser.add_argument("--deduplicate-questions", action="store_true")
    args = parser.parse_args()
    metadata = curate(
        args.input,
        args.output,
        args.min_score,
        args.max_score,
        args.fallback,
        args.minimum_rows,
        args.repeat_to_minimum,
        args.deduplicate_questions,
    )
    if args.metadata:
        args.metadata.parent.mkdir(parents=True, exist_ok=True)
        args.metadata.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
