"""Optional, idempotent publication of a canonical local Parquet artifact."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from qwen35.rzero.pipeline.state import file_hash


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--repo-id", required=True)
    parser.add_argument("--config-name", required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--private", action="store_true")
    args = parser.parse_args()

    digest = file_hash(args.dataset)
    if args.receipt.is_file():
        existing = json.loads(args.receipt.read_text(encoding="utf-8"))
        if existing.get("sha256") == digest and existing.get("repo_id") == args.repo_id:
            print("dataset publication already committed")
            return

    from datasets import load_dataset

    dataset = load_dataset("parquet", data_files={"train": str(args.dataset)})
    dataset.push_to_hub(args.repo_id, config_name=args.config_name, private=args.private)
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(
        json.dumps(
            {"repo_id": args.repo_id, "config_name": args.config_name, "sha256": digest},
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
