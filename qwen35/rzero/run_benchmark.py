"""Run the unchanged upstream benchmark in an isolated output directory."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    args.output_dir.parent.mkdir(parents=True, exist_ok=True)
    temporary_parent = Path(tempfile.mkdtemp(prefix="benchmark-", dir=args.output_dir.parent))
    try:
        (temporary_parent / "evaluation").symlink_to((args.repo_root / "evaluation").resolve(), target_is_directory=True)
        env = os.environ.copy()
        env.setdefault("VLLM_USE_V1", "1")
        subprocess.run(
            ["bash", str(args.repo_root / "evaluation" / "evaluate.bash"), args.model],
            cwd=temporary_parent,
            env=env,
            check=True,
        )
        (temporary_parent / "evaluation").unlink()
        os.replace(temporary_parent, args.output_dir)
    except Exception:
        shutil.rmtree(temporary_parent, ignore_errors=True)
        raise


if __name__ == "__main__":
    main()
