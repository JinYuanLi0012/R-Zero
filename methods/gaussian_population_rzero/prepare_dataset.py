#!/usr/bin/env python3
"""Build the local Solver dataset while preserving population provenance."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
from pathlib import Path

from datasets import Dataset


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_json(path: Path, value: object) -> None:
    temporary = path.with_name(f"{path.name}.tmp-{os.getpid()}")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-dir", type=Path, required=True)
    parser.add_argument("--experiment-name", required=True)
    parser.add_argument("--num-shards", type=int, required=True)
    parser.add_argument("--total-budget", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--min-score", type=float, default=0.3)
    parser.add_argument("--max-score", type=float, default=0.8)
    args = parser.parse_args()

    records, generation_count, source_files = [], 0, []
    for shard in range(args.num_shards):
        generated = args.generated_dir / f"{args.experiment_name}_{shard}.json"
        evaluated = args.generated_dir / f"{args.experiment_name}_{shard}_results.json"
        if not generated.is_file() or not evaluated.is_file():
            raise FileNotFoundError(f"missing generated/evaluated shard {shard}")
        generated_payload = json.loads(generated.read_text(encoding="utf-8"))
        evaluated_payload = json.loads(evaluated.read_text(encoding="utf-8"))
        generation_count += len(generated_payload)
        records.extend(evaluated_payload)
        source_files.extend([generated, evaluated])
    if generation_count != args.total_budget:
        raise RuntimeError(f"generated {generation_count} attempts, expected exactly {args.total_budget}")

    filtered = [
        {
            "problem": str(item["question"]),
            "answer": str(item["answer"]),
            "score": float(item["score"]),
            "source_expert_index": int(item["source_expert_index"]),
            "source_expert_seed": int(item["source_expert_seed"]),
            "source_sigma": float(item["source_sigma"]),
            "source_round": int(item["source_round"]),
            "labeler_role": "central_solver",
            "labeler_samples": int(item["labeler_samples"]),
        }
        for item in records
        if args.min_score <= float(item.get("score", -1)) <= args.max_score
        and str(item.get("question", "")).strip()
        and str(item.get("answer", "")).strip() not in {"", "None"}
    ]
    if not filtered:
        raise ValueError("filtering produced an empty Solver dataset")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    Dataset.from_list(filtered).to_parquet(str(args.output))
    by_expert: dict[str, int] = {}
    for item in filtered:
        key = str(item["source_expert_index"])
        by_expert[key] = by_expert.get(key, 0) + 1
    atomic_json(
        args.output.parent / "dataset_manifest.json",
        {
            "experiment_name": args.experiment_name,
            "total_generation_budget": args.total_budget,
            "generated_count": generation_count,
            "evaluated_count": len(records),
            "filtered_count": len(filtered),
            "filtered_by_questioner_expert": by_expert,
            "score_range": [args.min_score, args.max_score],
            "labeler_role": "central_solver",
            "labeler_samples": 9,
            "parquet": args.output.name,
            "parquet_sha256": sha256(args.output),
            "source_files": [
                {"path": str(path.relative_to(args.generated_dir)), "sha256": sha256(path)}
                for path in source_files
            ],
            "software_versions": {
                "python": platform.python_version(),
                "datasets": importlib.metadata.version("datasets"),
            },
        },
    )


if __name__ == "__main__":
    main()
