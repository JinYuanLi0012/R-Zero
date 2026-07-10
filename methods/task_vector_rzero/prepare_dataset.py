#!/usr/bin/env python3
"""Build the canonical local Parquet dataset and optionally mirror it to HF."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from datasets import Dataset, DatasetDict
from huggingface_hub import HfApi


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-dir", required=True, type=Path)
    parser.add_argument("--experiment-name", required=True)
    parser.add_argument("--num-shards", required=True, type=int)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--min-score", type=float, default=0.3)
    parser.add_argument("--max-score", type=float, default=0.8)
    parser.add_argument("--hf-repo")
    parser.add_argument("--hf-config")
    parser.add_argument("--no-upload", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.num_shards <= 0:
        raise ValueError("--num-shards must be positive")
    if args.min_score > args.max_score:
        raise ValueError("min score cannot exceed max score")
    if args.output.exists():
        raise FileExistsError(f"Dataset already exists: {args.output}")

    records: list[dict[str, Any]] = []
    source_files: list[Path] = []
    for shard in range(args.num_shards):
        path = args.generated_dir / f"{args.experiment_name}_{shard}_results.json"
        if not path.is_file():
            raise FileNotFoundError(f"Missing evaluated question shard: {path}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise ValueError(f"Expected a JSON list in {path}")
        records.extend(payload)
        source_files.append(path)

    filtered = [
        {
            "problem": item["question"],
            "answer": item["answer"],
            "score": float(item["score"]),
        }
        for item in records
        if args.min_score <= float(item.get("score", -1)) <= args.max_score
        and str(item.get("answer", "")).strip() not in {"", "None"}
        and str(item.get("question", "")).strip()
    ]
    if not filtered:
        raise ValueError("Filtering produced an empty training dataset")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    dataset = Dataset.from_list(filtered)
    dataset.to_parquet(str(args.output))

    uploaded = False
    if not args.no_upload:
        if not args.hf_repo:
            raise ValueError("--hf-repo is required unless --no-upload is set")
        token = os.getenv("HF_TOKEN") or os.getenv("HUGGING_FACE_HUB_TOKEN")
        if not token and Path("tokens.json").is_file():
            token = json.loads(Path("tokens.json").read_text(encoding="utf-8")).get("huggingface")
        api = HfApi(token=token)
        api.create_repo(args.hf_repo, repo_type="dataset", private=True, exist_ok=True)
        DatasetDict({"train": dataset}).push_to_hub(
            args.hf_repo,
            config_name=args.hf_config or args.experiment_name,
            private=True,
            token=token,
        )
        uploaded = True

    manifest = {
        "experiment_name": args.experiment_name,
        "raw_count": len(records),
        "filtered_count": len(filtered),
        "score_range": [args.min_score, args.max_score],
        "parquet": args.output.name,
        "parquet_sha256": sha256(args.output),
        "source_files": [
            {
                "path": str(path.relative_to(args.output.parent)),
                "sha256": sha256(path),
            }
            for path in source_files
        ],
        "hf_repo": args.hf_repo,
        "hf_config": args.hf_config or args.experiment_name,
        "hf_uploaded": uploaded,
    }
    atomic_json(args.output.parent / "dataset_manifest.json", manifest)
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
