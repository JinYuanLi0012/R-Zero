#!/usr/bin/env python3
"""Minimal validation for a merged local Hugging Face checkpoint."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("checkpoint", type=Path)
    parser.add_argument("--full-load", action="store_true")
    args = parser.parse_args()
    root = args.checkpoint.expanduser().resolve()
    if not (root / "config.json").is_file():
        raise FileNotFoundError(f"missing config.json in {root}")
    weights = sorted(root.glob("*.safetensors")) + sorted(root.glob("*.bin"))
    if not weights:
        raise FileNotFoundError(f"no model weight files in {root}")
    loaded = None
    if args.full_load:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(root, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            root, torch_dtype=torch.bfloat16, low_cpu_mem_usage=True, trust_remote_code=True
        )
        loaded = {"model_class": type(model).__name__, "tokenizer_class": type(tokenizer).__name__}
    print(json.dumps({"checkpoint": str(root), "weight_files": [p.name for p in weights], "loaded": loaded}, indent=2))


if __name__ == "__main__":
    main()
