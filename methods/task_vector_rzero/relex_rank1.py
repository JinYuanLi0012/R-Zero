#!/usr/bin/env python3
"""RELEX per-tensor rank-1 reconstruction for one Base-fit trajectory.

This is the rank=1, reconstruct-mode specialization of RELEX:
  M[t] = theta_t - theta_base
  G = M M^T
  V_1 = M^T U_1 / S_1
  delta_target_rank1 = (U_1[target] * S_1) V_1^T

As in RELEX, checkpoint deltas are formed in FP16, SVD work is FP32, and the
reconstructed checkpoint is saved in BF16.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import tempfile
from contextlib import ExitStack
from pathlib import Path
from typing import Any

import numpy as np
import torch
from safetensors import safe_open
from safetensors.torch import save_file

try:
    from .compose_task_vectors import (
        INDEX_NAME,
        LM_HEAD_KEY,
        ModelLayout,
        _chunks,
        _copy_base_metadata,
        _ensure_finite,
        _json_dump,
        _read_chunk,
        _sha256,
        resolve_model,
        validate_compatible,
    )
except ImportError:  # Direct script execution.
    from compose_task_vectors import (
        INDEX_NAME,
        LM_HEAD_KEY,
        ModelLayout,
        _chunks,
        _copy_base_metadata,
        _ensure_finite,
        _json_dump,
        _read_chunk,
        _sha256,
        resolve_model,
        validate_compatible,
    )


def relex_rank1_from_gram(gram: np.ndarray, target_index: int) -> tuple[np.ndarray, float, float]:
    """Return U_1, S_1 and rank-1 explained variance exactly as RELEX."""
    eigenvalues, eigenvectors = np.linalg.eigh(gram)
    order = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[order]
    eigenvectors = eigenvectors[:, order]
    nonnegative = np.maximum(eigenvalues, 0)
    total = float(np.sum(nonnegative))
    top = float(nonnegative[0]) if len(nonnegative) else 0.0
    explained = top / total if total > 0 else 0.0
    singular = math.sqrt(top)
    u1 = eigenvectors[:, 0].astype(np.float32)
    if target_index < 0 or target_index >= len(u1):
        raise IndexError("target checkpoint is outside the trajectory")
    return u1, singular, explained


def _delta_chunk(
    base_reader: Any,
    checkpoint_reader: Any,
    key: str,
    selection: tuple[Any, ...],
) -> torch.Tensor:
    # RELEX precompute_deltas.py loads Base/checkpoints as FP16 before subtraction.
    base_half = _read_chunk(base_reader, key, selection).to(torch.float16)
    checkpoint_half = _read_chunk(checkpoint_reader, key, selection).to(torch.float16)
    delta = (checkpoint_half - base_half).float()
    _ensure_finite(delta, f"RELEX delta for {key}")
    return delta


def reconstruct_rank1(
    base: ModelLayout,
    checkpoints: list[ModelLayout],
    steps: list[int],
    target_step: int,
    output_dir: Path,
    chunk_elements: int,
    provenance: dict[str, Any],
) -> dict[str, Any]:
    if len(checkpoints) < 2:
        raise ValueError("RELEX rank-1 requires at least two trajectory checkpoints")
    if len(checkpoints) != len(steps) or len(set(steps)) != len(steps):
        raise ValueError("Trajectory steps must be unique and match checkpoint count")
    if steps != sorted(steps):
        raise ValueError("Trajectory checkpoints must be ordered by increasing step")
    if target_step not in steps:
        raise ValueError("Target step must be one of the RELEX history checkpoints")
    if output_dir.exists():
        raise FileExistsError(f"Output already exists: {output_dir}")
    validate_compatible(base, checkpoints)

    target_index = steps.index(target_step)
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    temp_dir = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.tmp-", dir=output_dir.parent))
    shutil.rmtree(temp_dir)
    _copy_base_metadata(base.root, temp_dir)
    config_path = temp_dir / "config.json"
    output_config = json.loads(config_path.read_text(encoding="utf-8"))
    output_config["torch_dtype"] = "bfloat16"
    _json_dump(config_path, output_config)

    output_weight_map: dict[str, str] = {}
    output_shards: list[str] = []
    total_size = 0
    tensor_report: dict[str, Any] = {}

    try:
        for shard_index, base_filename in enumerate(base.shard_order, start=1):
            keys = sorted(
                key
                for key, filename in base.weight_map.items()
                if filename == base_filename
                and not (base.tied_embeddings and key == LM_HEAD_KEY)
            )
            print(
                f"[{shard_index}/{len(base.shard_order)}] RELEX rank-1 "
                f"{base_filename} ({len(keys)} tensors)"
            )
            if not keys:
                continue
            output_tensors: dict[str, torch.Tensor] = {}

            for key in keys:
                shape = base.shapes[key]

                def open_readers(stack: ExitStack) -> tuple[Any, list[Any]]:
                    base_reader = stack.enter_context(
                        safe_open(base.root / base.weight_map[key], framework="pt", device="cpu")
                    )
                    checkpoint_readers = [
                        stack.enter_context(
                            safe_open(
                                checkpoint.root / checkpoint.weight_map[key],
                                framework="pt",
                                device="cpu",
                            )
                        )
                        for checkpoint in checkpoints
                    ]
                    return base_reader, checkpoint_readers

                first_selection = next(iter(_chunks(shape, chunk_elements)))
                with ExitStack() as stack:
                    base_reader, checkpoint_readers = open_readers(stack)
                    first = _read_chunk(base_reader, key, first_selection)
                    if not first.is_floating_point():
                        base_value = base_reader.get_tensor(key)
                        for reader in checkpoint_readers:
                            if not torch.equal(base_value, reader.get_tensor(key)):
                                raise ValueError(f"Non-floating tensor changed in trajectory: {key}")
                        output_tensors[key] = base_value
                        output_weight_map[key] = base_filename
                        total_size += base_value.numel() * base_value.element_size()
                        continue

                # RELEX streaming pass 1: G = sum_chunks(M_chunk M_chunk^T).
                gram = np.zeros((len(checkpoints), len(checkpoints)), dtype=np.float32)
                target_delta_sq = 0.0
                with ExitStack() as stack:
                    base_reader, checkpoint_readers = open_readers(stack)
                    for selection in _chunks(shape, chunk_elements):
                        rows = [
                            _delta_chunk(base_reader, reader, key, selection).reshape(-1)
                            for reader in checkpoint_readers
                        ]
                        matrix = torch.stack(rows).float()
                        gram += (matrix @ matrix.T).cpu().numpy().astype(np.float32)
                        target = matrix[target_index]
                        target_delta_sq += (target * target).sum(dtype=torch.float64).item()

                u1, singular, explained = relex_rank1_from_gram(gram, target_index)
                threshold = singular * 1e-6 if singular > 0 else 1e-12
                coefficient = float(u1[target_index] * singular)
                output = torch.empty(shape, dtype=torch.bfloat16, device="cpu")
                reconstructed_sq = 0.0

                # RELEX streaming pass 2: V_1 = M^T U_1 / S_1, then c_target V_1^T.
                with ExitStack() as stack:
                    base_reader, checkpoint_readers = open_readers(stack)
                    u1_tensor = torch.from_numpy(u1)
                    for selection in _chunks(shape, chunk_elements):
                        base_chunk = _read_chunk(base_reader, key, selection).float()
                        rows = [
                            _delta_chunk(base_reader, reader, key, selection).reshape(-1)
                            for reader in checkpoint_readers
                        ]
                        matrix = torch.stack(rows).float()
                        if singular > threshold:
                            v1_chunk = (matrix.T @ u1_tensor) / singular
                            reconstructed = (coefficient * v1_chunk).reshape(base_chunk.shape)
                        else:
                            reconstructed = torch.zeros_like(base_chunk)
                        reconstructed_sq += (
                            reconstructed * reconstructed
                        ).sum(dtype=torch.float64).item()
                        result = base_chunk + reconstructed
                        _ensure_finite(result, f"rank-1 reconstructed tensor {key}")
                        converted = result.to(torch.bfloat16)
                        _ensure_finite(converted, f"BF16 rank-1 tensor {key}")
                        if selection:
                            output[selection] = converted
                        else:
                            output = converted

                output_tensors[key] = output.contiguous()
                output_weight_map[key] = base_filename
                total_size += output.numel() * output.element_size()
                tensor_report[key] = {
                    "explained_variance": explained,
                    "singular_value": singular,
                    "target_coefficient": coefficient,
                    "target_delta_norm": math.sqrt(max(0.0, target_delta_sq)),
                    "rank1_delta_norm": math.sqrt(max(0.0, reconstructed_sq)),
                }

            save_file(output_tensors, temp_dir / base_filename, metadata={"format": "pt"})
            output_shards.append(base_filename)
            del output_tensors

        if len(output_shards) > 1 or (base.root / INDEX_NAME).is_file():
            metadata = dict(base.index_metadata)
            metadata["total_size"] = total_size
            _json_dump(
                temp_dir / INDEX_NAME,
                {"metadata": metadata, "weight_map": output_weight_map},
            )

        variances = [item["explained_variance"] for item in tensor_report.values()]
        diagnostics = {
            "algorithm": "RELEX per-tensor SVD rank-1 reconstruction",
            "rank": 1,
            "steps": steps,
            "target_step": target_step,
            "delta_storage_dtype": "float16",
            "compute_dtype": "float32",
            "summary": {
                "mean_explained_variance": float(np.mean(variances)) if variances else 0.0,
                "min_explained_variance": float(np.min(variances)) if variances else 0.0,
                "max_explained_variance": float(np.max(variances)) if variances else 0.0,
                "tensor_count": len(variances),
            },
            "per_tensor": tensor_report,
        }
        _json_dump(temp_dir / "relex_rank1_diagnostics.json", diagnostics)
        manifest = {
            "format_version": 1,
            "algorithm": "relex_rank1_reconstruct",
            "base": provenance["base"],
            "trajectory": provenance["trajectory"],
            "steps": steps,
            "target_step": target_step,
            "rank": 1,
            "output_dtype": "bfloat16",
            "weight_files": [
                {
                    "name": filename,
                    "sha256": _sha256(temp_dir / filename),
                    "size": (temp_dir / filename).stat().st_size,
                }
                for filename in output_shards
            ],
            "diagnostics": "relex_rank1_diagnostics.json",
        }
        _json_dump(temp_dir / "relex_rank1_manifest.json", manifest)
        os.replace(temp_dir, output_dir)
        return manifest
    except BaseException:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--base-provenance", type=Path)
    parser.add_argument(
        "--checkpoint",
        action="append",
        required=True,
        help="Repeat as STEP=LOCAL_OR_HF_CHECKPOINT in ascending order.",
    )
    parser.add_argument("--target-step", required=True, type=int)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--chunk-elements", type=int, default=8_000_000)
    args = parser.parse_args()

    if args.chunk_elements <= 0:
        raise ValueError("--chunk-elements must be positive")
    base_path, base_provenance = resolve_model(args.base)
    if args.base_provenance:
        base_provenance = json.loads(args.base_provenance.read_text(encoding="utf-8"))

    steps: list[int] = []
    paths: list[Path] = []
    trajectory_provenance: list[dict[str, Any]] = []
    for item in args.checkpoint:
        if "=" not in item:
            raise ValueError(f"Expected STEP=CHECKPOINT, got {item!r}")
        step_text, model = item.split("=", 1)
        path, provenance = resolve_model(model)
        step = int(step_text)
        steps.append(step)
        paths.append(path)
        trajectory_provenance.append({"step": step, **provenance})

    manifest = reconstruct_rank1(
        ModelLayout.inspect(base_path),
        [ModelLayout.inspect(path) for path in paths],
        steps,
        args.target_step,
        args.output.expanduser().resolve(),
        args.chunk_elements,
        {"base": base_provenance, "trajectory": trajectory_provenance},
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
