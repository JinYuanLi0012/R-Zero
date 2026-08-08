"""Run the unchanged upstream benchmark in an isolated output directory."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


def apply_text_only_overlay(evaluation_dir: Path) -> None:
    """Patch only temporary benchmark copies to pass vLLM's official flag."""
    replacements = {
        "generate.py": ("vllm.LLM(\n", "vllm.LLM(\n        language_model_only=True,\n"),
        "eval_supergpqa.py": ("LLM(model=", "LLM(language_model_only=True, model="),
        "eval_bbeh.py": ("LLM(model=", "LLM(language_model_only=True, model="),
        "eval_mmlupro.py": ("LLM(model=", "LLM(language_model_only=True, model="),
    }
    for relative, (old, new) in replacements.items():
        path = evaluation_dir / relative
        text = path.read_text(encoding="utf-8")
        if text.count(old) != 1:
            raise RuntimeError(f"upstream benchmark changed; text-only overlay no longer applies to {path}")
        path.write_text(text.replace(old, new), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    args.output_dir.parent.mkdir(parents=True, exist_ok=True)
    temporary_parent = Path(tempfile.mkdtemp(prefix="benchmark-", dir=args.output_dir.parent))
    try:
        evaluation_copy = temporary_parent / "evaluation"
        shutil.copytree(args.repo_root / "evaluation", evaluation_copy)
        apply_text_only_overlay(evaluation_copy)
        env = os.environ.copy()
        env.setdefault("VLLM_USE_V1", "1")
        subprocess.run(
            ["bash", str(args.repo_root / "evaluation" / "evaluate.bash"), args.model],
            cwd=temporary_parent,
            env=env,
            check=True,
        )
        shutil.rmtree(evaluation_copy)
        os.replace(temporary_parent, args.output_dir)
    except Exception:
        shutil.rmtree(temporary_parent, ignore_errors=True)
        raise


if __name__ == "__main__":
    main()
