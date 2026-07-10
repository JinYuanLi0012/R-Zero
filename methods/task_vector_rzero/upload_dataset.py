#!/usr/bin/env python3
"""Mirror the canonical local Parquet dataset to a private HF dataset repo."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from datasets import Dataset, DatasetDict
from huggingface_hub import HfApi


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parquet", required=True, type=Path)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    token = os.getenv("HF_TOKEN") or os.getenv("HUGGING_FACE_HUB_TOKEN")
    if not token and Path("tokens.json").is_file():
        token = json.loads(Path("tokens.json").read_text(encoding="utf-8")).get("huggingface")
    api = HfApi(token=token)
    api.create_repo(args.repo, repo_type="dataset", private=True, exist_ok=True)
    dataset = Dataset.from_parquet(str(args.parquet))
    DatasetDict({"train": dataset}).push_to_hub(
        args.repo,
        config_name=args.config,
        private=True,
        token=token,
    )
    print(f"Mirrored {args.parquet} to private dataset {args.repo} ({args.config})")


if __name__ == "__main__":
    main()
