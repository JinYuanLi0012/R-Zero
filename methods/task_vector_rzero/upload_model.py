#!/usr/bin/env python3
"""Explicit, opt-in upload of a local model checkpoint."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from huggingface_hub import HfApi


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", required=True, type=Path)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--private", action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args()

    token = os.getenv("HF_TOKEN") or os.getenv("HUGGING_FACE_HUB_TOKEN")
    if not token and Path("tokens.json").is_file():
        token = json.loads(Path("tokens.json").read_text(encoding="utf-8")).get("huggingface")
    api = HfApi(token=token)
    api.create_repo(args.repo, repo_type="model", private=args.private, exist_ok=True)
    api.upload_folder(repo_id=args.repo, folder_path=args.checkpoint, repo_type="model")
    print(f"Uploaded {args.checkpoint} to {args.repo}")


if __name__ == "__main__":
    main()
