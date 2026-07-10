#!/usr/bin/env python3
"""Structural validation for a local Hugging Face safetensors checkpoint."""

from __future__ import annotations

import argparse
import gc
import json
from pathlib import Path

from compose_task_vectors import ModelLayout


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("checkpoint", type=Path)
    parser.add_argument("--reference", type=Path)
    parser.add_argument(
        "--full-load",
        action="store_true",
        help="Actually load the model and tokenizer through Transformers.",
    )
    args = parser.parse_args()

    layout = ModelLayout.inspect(args.checkpoint.expanduser().resolve())
    if args.reference:
        reference = ModelLayout.inspect(args.reference.expanduser().resolve())
        if set(layout.weight_map) != set(reference.weight_map):
            raise ValueError("Checkpoint tensor keys do not match reference")
        for key in reference.weight_map:
            if layout.shapes[key] != reference.shapes[key]:
                raise ValueError(f"Shape mismatch for {key}")
        if layout.structural_config() != reference.structural_config():
            raise ValueError("Checkpoint structural config does not match reference")

    loading = None
    if args.full_load:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(layout.root, trust_remote_code=True)
        model, loading_info = AutoModelForCausalLM.from_pretrained(
            layout.root,
            torch_dtype=torch.bfloat16,
            low_cpu_mem_usage=True,
            trust_remote_code=True,
            output_loading_info=True,
        )
        missing = list(loading_info.get("missing_keys") or [])
        unexpected = list(loading_info.get("unexpected_keys") or [])
        mismatched = list(loading_info.get("mismatched_keys") or [])
        errors = list(loading_info.get("error_msgs") or [])
        if missing or unexpected or mismatched or errors:
            raise ValueError(
                "Transformers load reported inconsistent weights: "
                f"missing={missing[:10]}, unexpected={unexpected[:10]}, "
                f"mismatched={mismatched[:10]}, errors={errors[:3]}"
            )
        if layout.tied_embeddings:
            input_weight = model.get_input_embeddings().weight
            output_weight = model.get_output_embeddings().weight
            if input_weight.data_ptr() != output_weight.data_ptr():
                raise ValueError("tie_word_embeddings=true but input/output weights are not tied")
        loading = {
            "model_class": type(model).__name__,
            "tokenizer_class": type(tokenizer).__name__,
            "tied_embeddings": layout.tied_embeddings,
        }
        del model, tokenizer
        gc.collect()

    print(
        json.dumps(
            {
                "checkpoint": str(layout.root),
                "tensor_count": len(layout.weight_map),
                "weight_files": list(layout.shard_order),
                "structural_config": layout.structural_config(),
                "full_load": loading,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
