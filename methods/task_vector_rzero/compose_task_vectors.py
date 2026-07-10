#!/usr/bin/env python3
"""Compose cumulative R-Zero task vectors without loading whole models into RAM."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import shutil
import sys
import tempfile
from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import torch
from huggingface_hub import snapshot_download
from safetensors import safe_open
from safetensors.torch import save_file


INDEX_NAME = "model.safetensors.index.json"
DEFAULT_CHUNK_ELEMENTS = 8_000_000
STRUCTURAL_CONFIG_KEYS = (
    "model_type",
    "architectures",
    "hidden_size",
    "intermediate_size",
    "num_hidden_layers",
    "num_attention_heads",
    "num_key_value_heads",
    "head_dim",
    "vocab_size",
    "tie_word_embeddings",
    "hidden_act",
    "rms_norm_eps",
    "rope_theta",
    "rope_scaling",
    "max_position_embeddings",
    "sliding_window",
    "use_sliding_window",
)
EMBED_TOKENS_KEY = "model.embed_tokens.weight"
LM_HEAD_KEY = "lm_head.weight"


def _json_dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_model(model: str, revision: str | None = None) -> tuple[Path, dict[str, Any]]:
    candidate = Path(model).expanduser()
    if candidate.is_dir():
        resolved = candidate.resolve()
        return resolved, {
            "source": model,
            "resolved_path": str(resolved),
            "requested_revision": None,
            "resolved_revision": None,
        }

    resolved = Path(
        snapshot_download(
            repo_id=model,
            revision=revision,
            allow_patterns=[
                "*.json",
                "*.safetensors",
                "*.model",
                "*.txt",
                "*.jinja",
                "*.py",
                "tokenizer.*",
                "merges.txt",
                "vocab.*",
            ],
        )
    ).resolve()
    resolved_revision = revision
    if resolved.parent.name == "snapshots":
        resolved_revision = resolved.name
    return resolved, {
        "source": model,
        "resolved_path": str(resolved),
        "requested_revision": revision,
        "resolved_revision": resolved_revision,
    }


@dataclass(frozen=True)
class ModelLayout:
    root: Path
    weight_map: dict[str, str]
    shard_order: tuple[str, ...]
    shapes: dict[str, tuple[int, ...]]
    config: dict[str, Any]
    index_metadata: dict[str, Any]

    @classmethod
    def inspect(cls, root: Path) -> "ModelLayout":
        config_path = root / "config.json"
        if not config_path.is_file():
            raise ValueError(f"Missing config.json in {root}")
        config = json.loads(config_path.read_text(encoding="utf-8"))

        index_path = root / INDEX_NAME
        index_metadata: dict[str, Any] = {}
        if index_path.is_file():
            index = json.loads(index_path.read_text(encoding="utf-8"))
            weight_map = index.get("weight_map")
            if not isinstance(weight_map, dict) or not weight_map:
                raise ValueError(f"Invalid weight_map in {index_path}")
            weight_map = {str(key): str(value) for key, value in weight_map.items()}
            index_metadata = dict(index.get("metadata") or {})
            shard_order = tuple(dict.fromkeys(weight_map.values()))
        else:
            files = sorted(root.glob("*.safetensors"))
            if not files:
                raise ValueError(f"No safetensors weights found in {root}")
            weight_map = {}
            shard_order_list: list[str] = []
            for file_path in files:
                shard_order_list.append(file_path.name)
                with safe_open(file_path, framework="pt", device="cpu") as reader:
                    for key in reader.keys():
                        if key in weight_map:
                            raise ValueError(f"Tensor {key!r} appears in multiple files under {root}")
                        weight_map[key] = file_path.name
            shard_order = tuple(shard_order_list)

        missing_files = sorted({name for name in weight_map.values() if not (root / name).is_file()})
        if missing_files:
            raise ValueError(f"Missing weight shards in {root}: {missing_files}")

        shapes: dict[str, tuple[int, ...]] = {}
        by_file: dict[str, list[str]] = {}
        for key, filename in weight_map.items():
            by_file.setdefault(filename, []).append(key)
        for filename, keys in by_file.items():
            with safe_open(root / filename, framework="pt", device="cpu") as reader:
                actual = set(reader.keys())
                expected = set(keys)
                if actual != expected:
                    raise ValueError(
                        f"Index/file tensor mismatch in {root / filename}: "
                        f"missing={sorted(expected - actual)[:5]}, extra={sorted(actual - expected)[:5]}"
                    )
                for key in keys:
                    shapes[key] = tuple(reader.get_slice(key).get_shape())

        return cls(root, weight_map, shard_order, shapes, config, index_metadata)

    def structural_config(self) -> dict[str, Any]:
        return {key: self.config.get(key) for key in STRUCTURAL_CONFIG_KEYS if key in self.config}

    @property
    def tied_embeddings(self) -> bool:
        return bool(self.config.get("tie_word_embeddings", False))

    def task_vector_keys(self) -> set[str]:
        keys = set(self.weight_map)
        if self.tied_embeddings:
            if EMBED_TOKENS_KEY not in keys:
                raise ValueError(
                    f"Tied model {self.root} is missing canonical tensor {EMBED_TOKENS_KEY}"
                )
            # Match RELEX: lm_head is redundant and follows embed_tokens.
            keys.discard(LM_HEAD_KEY)
        return keys


def validate_compatible(base: ModelLayout, auxiliaries: list[ModelLayout]) -> None:
    base_keys = base.task_vector_keys()
    base_config = base.structural_config()
    for index, auxiliary in enumerate(auxiliaries, start=1):
        aux_keys = auxiliary.task_vector_keys()
        if aux_keys != base_keys:
            raise ValueError(
                f"Auxiliary {index} tensor keys differ from Base: "
                f"missing={sorted(base_keys - aux_keys)[:10]}, extra={sorted(aux_keys - base_keys)[:10]}"
            )
        mismatched_shapes = [
            key for key in base_keys if auxiliary.shapes[key] != base.shapes[key]
        ]
        if mismatched_shapes:
            key = mismatched_shapes[0]
            raise ValueError(
                f"Auxiliary {index} shape mismatch for {key}: "
                f"{auxiliary.shapes[key]} != {base.shapes[key]}"
            )
        if auxiliary.structural_config() != base_config:
            raise ValueError(
                f"Auxiliary {index} has an incompatible model config. "
                f"Base={base_config}, auxiliary={auxiliary.structural_config()}"
            )


def _copy_base_metadata(base: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=False)
    for source in base.iterdir():
        if source.name == INDEX_NAME or source.suffix in {".safetensors", ".bin"}:
            continue
        target = destination / source.name
        if source.is_dir():
            shutil.copytree(source, target)
        elif source.is_file():
            shutil.copy2(source, target)


def _chunks(shape: tuple[int, ...], max_elements: int) -> Iterable[tuple[Any, ...]]:
    if not shape:
        yield ()
        return
    row_elements = math.prod(shape[1:]) if len(shape) > 1 else 1
    rows = max(1, max_elements // max(1, row_elements))
    for start in range(0, shape[0], rows):
        yield (slice(start, min(shape[0], start + rows)),)


def _read_chunk(reader: Any, key: str, selection: tuple[Any, ...]) -> torch.Tensor:
    if not selection:
        return reader.get_tensor(key)
    return reader.get_slice(key)[selection]


def _ensure_finite(tensor: torch.Tensor, description: str) -> None:
    if tensor.is_floating_point() and not torch.isfinite(tensor).all().item():
        raise ValueError(f"NaN or Inf found in {description}")


def compose(
    base: ModelLayout,
    auxiliaries: list[ModelLayout],
    scales: list[float],
    output_dir: Path,
    chunk_elements: int,
    provenance: dict[str, Any],
) -> dict[str, Any]:
    if len(auxiliaries) != len(scales):
        raise ValueError("The number of auxiliary models and scales must match")
    if not auxiliaries:
        raise ValueError("At least one auxiliary model is required")
    if output_dir.exists():
        raise FileExistsError(f"Output already exists: {output_dir}")

    validate_compatible(base, auxiliaries)
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    temp_dir = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.tmp-", dir=output_dir.parent))
    shutil.rmtree(temp_dir)
    _copy_base_metadata(base.root, temp_dir)
    output_config_path = temp_dir / "config.json"
    output_config = json.loads(output_config_path.read_text(encoding="utf-8"))
    output_config["torch_dtype"] = "bfloat16"
    _json_dump(output_config_path, output_config)

    delta_sq = [0.0 for _ in auxiliaries]
    gram = [[0.0 for _ in auxiliaries] for _ in auxiliaries]
    combined_sq = 0.0
    per_tensor: dict[str, Any] = {}
    output_weight_map: dict[str, str] = {}
    output_shards: list[str] = []
    total_size = 0

    try:
        for shard_index, base_filename in enumerate(base.shard_order, start=1):
            keys = sorted(
                key
                for key, filename in base.weight_map.items()
                if filename == base_filename
                and not (base.tied_embeddings and key == LM_HEAD_KEY)
            )
            print(f"[{shard_index}/{len(base.shard_order)}] composing {base_filename} ({len(keys)} tensors)")
            output_tensors: dict[str, torch.Tensor] = {}

            if not keys:
                print(f"  skipping empty output shard after tied-weight normalization: {base_filename}")
                continue

            with ExitStack() as stack:
                readers: dict[tuple[int, str], Any] = {}

                def reader_for(model_index: int, layout: ModelLayout, filename: str) -> Any:
                    cache_key = (model_index, filename)
                    if cache_key not in readers:
                        readers[cache_key] = stack.enter_context(
                            safe_open(layout.root / filename, framework="pt", device="cpu")
                        )
                    return readers[cache_key]

                base_reader = reader_for(-1, base, base_filename)
                for key in keys:
                    shape = base.shapes[key]
                    first_selection = next(iter(_chunks(shape, chunk_elements)))
                    first = _read_chunk(base_reader, key, first_selection)
                    if not first.is_floating_point():
                        base_value = base_reader.get_tensor(key)
                        for aux_index, auxiliary in enumerate(auxiliaries):
                            aux_reader = reader_for(
                                aux_index, auxiliary, auxiliary.weight_map[key]
                            )
                            if not torch.equal(base_value, aux_reader.get_tensor(key)):
                                raise ValueError(
                                    f"Non-floating tensor {key} differs in auxiliary {aux_index + 1}"
                                )
                        output_tensors[key] = base_value
                        output_weight_map[key] = base_filename
                        total_size += base_value.numel() * base_value.element_size()
                        continue

                    output = torch.empty(shape, dtype=torch.bfloat16, device="cpu")
                    tensor_delta_sq = [0.0 for _ in auxiliaries]
                    tensor_combined_sq = 0.0
                    for selection in _chunks(shape, chunk_elements):
                        base_chunk = _read_chunk(base_reader, key, selection).float()
                        _ensure_finite(base_chunk, f"Base tensor {key}")
                        deltas: list[torch.Tensor] = []
                        combined = torch.zeros_like(base_chunk)
                        for aux_index, (auxiliary, scale) in enumerate(zip(auxiliaries, scales)):
                            aux_reader = reader_for(
                                aux_index, auxiliary, auxiliary.weight_map[key]
                            )
                            aux_chunk = _read_chunk(aux_reader, key, selection).float()
                            _ensure_finite(aux_chunk, f"auxiliary {aux_index + 1} tensor {key}")
                            delta = aux_chunk - base_chunk
                            value = (delta * delta).sum(dtype=torch.float64).item()
                            delta_sq[aux_index] += value
                            tensor_delta_sq[aux_index] += value
                            deltas.append(delta)
                            combined.add_(delta, alpha=scale)

                        for left in range(len(deltas)):
                            for right in range(left, len(deltas)):
                                value = (deltas[left] * deltas[right]).sum(dtype=torch.float64).item()
                                gram[left][right] += value
                                if left != right:
                                    gram[right][left] += value

                        value = (combined * combined).sum(dtype=torch.float64).item()
                        combined_sq += value
                        tensor_combined_sq += value
                        result = base_chunk + combined
                        _ensure_finite(result, f"composed tensor {key}")
                        converted = result.to(torch.bfloat16)
                        _ensure_finite(converted, f"BF16 composed tensor {key}")
                        if selection:
                            output[selection] = converted
                        else:
                            output = converted

                    output_tensors[key] = output.contiguous()
                    output_weight_map[key] = base_filename
                    total_size += output.numel() * output.element_size()
                    per_tensor[key] = {
                        "delta_norms": [math.sqrt(max(0.0, value)) for value in tensor_delta_sq],
                        "combined_update_norm": math.sqrt(max(0.0, tensor_combined_sq)),
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

        norms = [math.sqrt(max(0.0, value)) for value in delta_sq]
        cosine: list[list[float]] = []
        for left in range(len(auxiliaries)):
            row: list[float] = []
            for right in range(len(auxiliaries)):
                denominator = norms[left] * norms[right]
                row.append(gram[left][right] / denominator if denominator else 0.0)
            cosine.append(row)

        diagnostics = {
            "formula": "base + sum(scale_i * (auxiliary_i - base))",
            "scales": scales,
            "delta_norms": norms,
            "gram_matrix": gram,
            "cosine_similarity": cosine,
            "combined_update_norm": math.sqrt(max(0.0, combined_sq)),
            "per_tensor": per_tensor,
        }
        _json_dump(temp_dir / "task_vector_diagnostics.json", diagnostics)

        manifest = {
            "format_version": 1,
            "base": provenance["base"],
            "auxiliaries": provenance["auxiliaries"],
            "scales": scales,
            "output_dtype": "bfloat16",
            "chunk_elements": chunk_elements,
            "tensor_count": len(output_weight_map),
            "weight_files": [
                {
                    "name": filename,
                    "sha256": _sha256(temp_dir / filename),
                    "size": (temp_dir / filename).stat().st_size,
                }
                for filename in output_shards
            ],
            "diagnostics": "task_vector_diagnostics.json",
        }
        _json_dump(temp_dir / "task_vector_manifest.json", manifest)
        os.replace(temp_dir, output_dir)
        return manifest
    except BaseException:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compose Base + sum(scale_i * (auxiliary_i - Base)) into a HF checkpoint."
    )
    parser.add_argument("--base", required=True, help="Local HF checkpoint or Hugging Face repo ID")
    parser.add_argument("--auxiliary", action="append", required=True, help="Repeat for every Base-fit model")
    parser.add_argument("--scale", action="append", type=float, help="Repeat in auxiliary order; defaults to 1")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--base-revision")
    parser.add_argument(
        "--base-provenance",
        type=Path,
        help="Optional immutable Base manifest produced by resolve_base.py.",
    )
    parser.add_argument("--chunk-elements", type=int, default=DEFAULT_CHUNK_ELEMENTS)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.chunk_elements <= 0:
        raise ValueError("--chunk-elements must be positive")
    scales = args.scale if args.scale is not None else [1.0] * len(args.auxiliary)
    if len(scales) != len(args.auxiliary):
        raise ValueError("Provide exactly one --scale per --auxiliary, or omit all scales")

    base_path, base_provenance = resolve_model(args.base, args.base_revision)
    if args.base_provenance:
        base_provenance = json.loads(args.base_provenance.read_text(encoding="utf-8"))
    auxiliary_paths: list[Path] = []
    auxiliary_provenance: list[dict[str, Any]] = []
    for auxiliary in args.auxiliary:
        path, item = resolve_model(auxiliary)
        auxiliary_paths.append(path)
        auxiliary_provenance.append(item)

    manifest = compose(
        ModelLayout.inspect(base_path),
        [ModelLayout.inspect(path) for path in auxiliary_paths],
        scales,
        args.output.expanduser().resolve(),
        args.chunk_elements,
        {"base": base_provenance, "auxiliaries": auxiliary_provenance},
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"task-vector composition failed: {error}", file=sys.stderr)
        raise
