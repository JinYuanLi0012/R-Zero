"""Resolve the immutable Qwen checkpoint and validate its architecture."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-id", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    from huggingface_hub import snapshot_download

    args.output_dir.mkdir(parents=True, exist_ok=True)
    resolved = snapshot_download(
        repo_id=args.repo_id,
        revision=args.revision,
        local_dir=args.output_dir,
    )
    config_path = Path(resolved) / "config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config.get("model_type") != "qwen3_5":
        raise RuntimeError(f"expected qwen3_5, found {config.get('model_type')!r}")
    (args.output_dir / "RZERO_MODEL_REVISION").write_text(args.revision + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
