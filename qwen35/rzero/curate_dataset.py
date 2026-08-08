"""Merge scored shards into the canonical local Solver Parquet dataset."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from qwen35.rzero.data import solver_record


def curate(inputs: list[Path], output: Path, minimum: float, maximum: float) -> dict[str, int]:
    rows = []
    for path in inputs:
        rows.extend(json.loads(path.read_text(encoding="utf-8")))
    accepted = [
        item
        for item in rows
        if minimum <= float(item.get("score", -1)) <= maximum
        and item.get("answer") not in {"", "None", None}
    ]
    # The migration plan requires merge-time de-duplication. Keep first occurrence
    # so shard ordering makes the result deterministic.
    unique: dict[str, dict] = {}
    for item in accepted:
        key = " ".join(str(item["question"]).split())
        unique.setdefault(key, item)
    records = [
        solver_record(item["question"], item["answer"], float(item["score"]), index)
        for index, item in enumerate(unique.values())
    ]
    if not records:
        raise RuntimeError("difficulty filtering produced an empty Solver dataset")

    from datasets import Dataset

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.name}.tmp-{os.getpid()}")
    Dataset.from_list(records).to_parquet(temporary)
    os.replace(temporary, output)
    return {"scored": len(rows), "accepted": len(accepted), "deduplicated": len(records)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--min-score", type=float, default=0.3)
    parser.add_argument("--max-score", type=float, default=0.8)
    parser.add_argument("--metadata", type=Path)
    args = parser.parse_args()
    metadata = curate(args.input, args.output, args.min_score, args.max_score)
    if args.metadata:
        args.metadata.parent.mkdir(parents=True, exist_ok=True)
        args.metadata.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
