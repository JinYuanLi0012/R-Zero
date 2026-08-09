"""Fail-fast environment smoke checks for the formal GPU host."""

from __future__ import annotations

import argparse
import gc
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

from qwen35.rzero.official_verl import assert_official_verl, build_pythonpath


def hydra_compose_command() -> list[str]:
    return [sys.executable, "-m", "verl.trainer.main_ppo", "--cfg", "job"]


def cuda_abi_matches(torch_cuda: str | None, image_cuda: str) -> bool:
    """Compare the CUDA ABI line while the image digest pins patch contents."""
    if torch_cuda is None:
        return False
    actual = torch_cuda.split(".")
    expected = image_cuda.split(".")
    return len(actual) >= 2 and len(expected) >= 2 and actual[:2] == expected[:2]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-verl-root", type=Path, required=True)
    parser.add_argument("--expected-verl-ref", required=True)
    parser.add_argument("--expected-vllm-version", required=True)
    parser.add_argument("--expected-transformers-version", required=True)
    parser.add_argument("--expected-torch-version", required=True)
    parser.add_argument("--expected-cuda-version", required=True)
    parser.add_argument("--load-vllm", action="store_true")
    args = parser.parse_args()

    import torch
    import transformers
    import verl
    import vllm
    from transformers import AutoConfig, AutoTokenizer

    verl_file = assert_official_verl(verl.__file__, args.expected_verl_root)
    verl_ref = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=args.expected_verl_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    versions = {
        "verl_ref": (verl_ref, args.expected_verl_ref),
        "vllm": (vllm.__version__, args.expected_vllm_version),
        "transformers": (transformers.__version__, args.expected_transformers_version),
        "torch": (torch.__version__.split("+", 1)[0], args.expected_torch_version),
    }
    mismatches = {name: pair for name, pair in versions.items() if pair[0] != pair[1]}
    if not cuda_abi_matches(torch.version.cuda, args.expected_cuda_version):
        mismatches["cuda_abi"] = (torch.version.cuda, args.expected_cuda_version)
    if mismatches:
        raise RuntimeError(f"runtime version mismatch: {mismatches}")
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
        "torch_cuda_abi": torch.version.cuda,
        "cuda_image_version": args.expected_cuda_version,
        "transformers": transformers.__version__,
        "vllm": vllm.__version__,
        "verl": getattr(verl, "__version__", "unknown"),
        "verl_ref": verl_ref,
        "verl_file": str(verl_file),
        "verl_hydra_compose": "ok",
        "model_type": config.model_type,
        "gpu_count": torch.cuda.device_count(),
        "gpu_names": [torch.cuda.get_device_name(index) for index in range(torch.cuda.device_count())],
    }
    if args.load_vllm:
        engine = vllm.LLM(
            model=args.model,
            tokenizer=args.model,
            language_model_only=True,
            gpu_memory_utilization=0.2,
            max_model_len=4096,
            enforce_eager=True,
            enable_chunked_prefill=False,
        )
        outputs = engine.generate(
            ["Return exactly the number 2."],
            vllm.SamplingParams(temperature=0.0, max_tokens=8),
            use_tqdm=False,
        )
        generated = outputs[0].outputs[0].text
        if not generated:
            raise RuntimeError("vLLM loaded Qwen3.5 but generated no text")
        del engine
        gc.collect()
        torch.cuda.empty_cache()
        result["vllm_model_load_generate"] = "ok"
        result["vllm_smoke_text"] = generated
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
