"""Fail-fast environment smoke checks for the formal GPU host."""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

from qwen35.rzero.official_verl import assert_official_verl, build_pythonpath


def hydra_compose_command() -> list[str]:
    return [sys.executable, "-m", "verl.trainer.main_ppo", "--cfg", "job"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-verl-root", type=Path, required=True)
    parser.add_argument("--load-vllm", action="store_true")
    args = parser.parse_args()

    import torch
    import transformers
    import verl
    import vllm
    from transformers import AutoConfig, AutoTokenizer

    verl_file = assert_official_verl(verl.__file__, args.expected_verl_root)
    repo_root = Path(__file__).resolve().parents[3]
    compose_env = os.environ.copy()
    compose_env["PYTHONPATH"] = build_pythonpath(args.expected_verl_root, repo_root, compose_env.get("PYTHONPATH"))
    subprocess.run(
        hydra_compose_command(),
        cwd=args.expected_verl_root,
        env=compose_env,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )

    config = AutoConfig.from_pretrained(args.model)
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    if config.model_type != "qwen3_5":
        raise RuntimeError(f"expected qwen3_5, got {config.model_type}")
    if not tokenizer.chat_template:
        raise RuntimeError("Qwen3.5 tokenizer is missing its official chat template")
    if torch.cuda.device_count() != 4:
        raise RuntimeError(f"formal host requires 4 visible GPUs, got {torch.cuda.device_count()}")

    result = {
        "python": platform.python_version(),
        "torch": torch.__version__,
        "transformers": transformers.__version__,
        "vllm": vllm.__version__,
        "verl": getattr(verl, "__version__", "unknown"),
        "verl_file": str(verl_file),
        "verl_hydra_compose": "ok",
        "model_type": config.model_type,
        "gpu_count": torch.cuda.device_count(),
        "gpu_names": [torch.cuda.get_device_name(index) for index in range(torch.cuda.device_count())],
    }
    if args.load_vllm:
        engine = vllm.LLM(model=args.model, tokenizer=args.model, language_model_only=True, gpu_memory_utilization=0.2)
        del engine
        result["vllm_model_load"] = "ok"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
