"""Export a selected official verl FSDP checkpoint to Hugging Face format."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from qwen35.rzero.official_verl import build_pythonpath, verl_source_root


def checkpoint_actor(checkpoint_root: Path, step: int) -> Path:
    candidates = [
        checkpoint_root / f"global_step_{step}" / "actor",
        checkpoint_root / f"global_steps_{step}" / "actor",
    ]
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError(f"no actor checkpoint for step {step}: {candidates}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint-root", type=Path, required=True)
    parser.add_argument("--step", type=int, required=True)
    parser.add_argument("--target-dir", type=Path, required=True)
    args = parser.parse_args()
    actor = checkpoint_actor(args.checkpoint_root, args.step)
    args.target_dir.parent.mkdir(parents=True, exist_ok=True)
    official_root = verl_source_root()
    repo_root = Path(__file__).resolve().parents[2]
    env = os.environ.copy()
    env["PYTHONPATH"] = build_pythonpath(official_root, repo_root, env.get("PYTHONPATH"))
    subprocess.run(
        [
            sys.executable,
            "-m",
            "verl.model_merger",
            "merge",
            "--backend",
            "fsdp",
            "--local_dir",
            str(actor),
            "--target_dir",
            str(args.target_dir),
        ],
        check=True,
        cwd=official_root,
        env=env,
    )


if __name__ == "__main__":
    main()
