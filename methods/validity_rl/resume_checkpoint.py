#!/usr/bin/env python3
"""Validate a two-rank recovery point without importing torch or contacting HF."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from find_resume_checkpoint import find_complete_checkpoint, require_nonempty


def resolve(root: Path, dataset: str, max_steps: int) -> Path:
    checkpoint = find_complete_checkpoint(root, world_size=2)
    if checkpoint is None:
        raise ValueError("No committed checkpoint tracker found; cannot resume")
    step = int(checkpoint.name.removeprefix("global_step_"))
    if step >= max_steps:
        raise ValueError(f"Checkpoint step {step} already reaches target {max_steps}; no updates remaining")
    for name in ("train.parquet", "validation.parquet", "audit.json"):
        require_nonempty(root / "data" / name)
    audit = json.loads((root / "data" / "audit.json").read_text())
    if audit.get("dataset") != dataset:
        raise ValueError("Dataset differs from the original run's audit.json; keep the original dataset")
    return checkpoint


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--max-steps", type=int, default=15)
    args = parser.parse_args()
    try:
        print(resolve(args.root, args.dataset, args.max_steps))
    except (OSError, ValueError) as error:
        print(f"Resume preflight failed: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
