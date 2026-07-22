#!/usr/bin/env python3
"""Stream 4B checkpoints and compute exact task-vector geometry statistics."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import sys
from contextlib import ExitStack
from pathlib import Path
from typing import Any

import numpy as np
import torch
from safetensors import safe_open

try:
    from methods.task_vector_rzero.compose_task_vectors import (
        LM_HEAD_KEY,
        ModelLayout,
        _chunks,
        _read_chunk,
        validate_compatible,
    )
except ImportError as error:  # pragma: no cover - actionable CLI error
    raise ImportError(
        "Run with the R-Zero repository root on PYTHONPATH so the analysis can reuse "
        "methods.task_vector_rzero.compose_task_vectors."
    ) from error

try:
    from .delta_definitions import RunInputs, discover_run_inputs, input_fingerprint
    from .geometry import cosine_from_gram, derive_geometry
except ImportError:  # Direct script execution.
    from delta_definitions import RunInputs, discover_run_inputs, input_fingerprint
    from geometry import cosine_from_gram, derive_geometry


ANALYSIS_VERSION = 2
LAYER_PATTERN = re.compile(r"(?:^|\.)layers\.(\d+)(?:\.|$)")


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".tmp-{os.getpid()}")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".tmp-{os.getpid()}")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def write_matrix_csv(path: Path, labels: list[str], matrix: np.ndarray) -> None:
    rows = [
        {"delta_id": label, **{other: float(matrix[i, j]) for j, other in enumerate(labels)}}
        for i, label in enumerate(labels)
    ]
    write_csv(path, ["delta_id", *labels], rows)


def write_rect_matrix_csv(
    path: Path,
    row_labels: list[str],
    column_labels: list[str],
    matrix: np.ndarray,
) -> None:
    if matrix.shape != (len(row_labels), len(column_labels)):
        raise ValueError(f"Rectangular matrix shape mismatch for {path}")
    rows = [
        {
            "delta_id": row_label,
            **{column_label: float(matrix[i, j]) for j, column_label in enumerate(column_labels)},
        }
        for i, row_label in enumerate(row_labels)
    ]
    write_csv(path, ["delta_id", *column_labels], rows)


def maybe_write_parquet(path: Path, rows: list[dict[str, Any]]) -> bool:
    """Write Parquet when pandas+pyarrow are available; CSV remains canonical fallback."""

    try:
        import pandas as pd
    except ImportError:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".tmp-{os.getpid()}")
    try:
        pd.DataFrame(rows).to_parquet(temporary, index=False)
        os.replace(temporary, path)
    except Exception as error:  # Parquet is optional; the CSV is canonical.
        temporary.unlink(missing_ok=True)
        print(f"warning: optional Parquet export failed for {path}: {error}", file=sys.stderr)
        return False
    return True


def layer_name(key: str) -> str:
    match = LAYER_PATTERN.search(key)
    if match:
        return f"layer_{int(match.group(1)):02d}"
    if "embed_tokens" in key:
        return "embedding"
    if key == LM_HEAD_KEY:
        return "lm_head"
    if key.endswith("model.norm.weight") or key == "model.norm.weight":
        return "final_norm"
    return "other"


def module_name(key: str) -> str:
    categories = (
        ("embed_tokens", "embedding"),
        ("lm_head", "lm_head"),
        ("self_attn.q_proj", "attention_q"),
        ("self_attn.k_proj", "attention_k"),
        ("self_attn.v_proj", "attention_v"),
        ("self_attn.o_proj", "attention_o"),
        ("mlp.gate_proj", "mlp_gate"),
        ("mlp.up_proj", "mlp_up"),
        ("mlp.down_proj", "mlp_down"),
    )
    for pattern, category in categories:
        if pattern in key:
            return category
    if "norm" in key:
        return "normalization"
    return "other"


def inspect_layouts(inputs: RunInputs) -> dict[str, ModelLayout]:
    required = {"base"}
    for delta in inputs.deltas:
        required.update((delta.start, delta.end))
    required.update(f"v{round_number}" for round_number in range(1, inputs.rounds + 1))
    layouts = {model_id: ModelLayout.inspect(inputs.checkpoints[model_id]) for model_id in sorted(required)}
    validate_compatible(layouts["base"], [layout for key, layout in layouts.items() if key != "base"])
    return layouts


def model_files(layouts: dict[str, ModelLayout]) -> dict[str, list[Path]]:
    result: dict[str, list[Path]] = {}
    for model_id, layout in layouts.items():
        paths = [layout.root / filename for filename in sorted(set(layout.weight_map.values()))]
        paths.append(layout.root / "config.json")
        index = layout.root / "model.safetensors.index.json"
        if index.is_file():
            paths.append(index)
        result[model_id] = paths
    return result


def empty_accumulator(fingerprint: str, delta_count: int, start_ids: list[str]) -> dict[str, Any]:
    return {
        "format_version": 1,
        "analysis_version": ANALYSIS_VERSION,
        "fingerprint": fingerprint,
        "completed_tensors": [],
        "gram": np.zeros((delta_count, delta_count), dtype=np.float64).tolist(),
        "start_norm_sq": {model_id: 0.0 for model_id in start_ids},
        "layers": {},
        "modules": {},
        "floating_parameter_count": 0,
        "non_floating_tensors": [],
    }


def load_accumulator(
    path: Path,
    fingerprint: str,
    delta_count: int,
    start_ids: list[str],
    resume: bool,
) -> dict[str, Any]:
    if not path.exists():
        return empty_accumulator(fingerprint, delta_count, start_ids)
    if not resume:
        raise FileExistsError(f"Cache already exists: {path}; pass --resume or use a new output")
    state = json.loads(path.read_text(encoding="utf-8"))
    if state.get("fingerprint") != fingerprint:
        raise RuntimeError("Cached analysis fingerprint does not match current inputs")
    if np.asarray(state.get("gram", [])).shape != (delta_count, delta_count):
        raise RuntimeError("Cached Gram matrix has the wrong shape")
    return state


def tensor_cache_name(key: str) -> str:
    digest = hashlib.sha1(key.encode()).hexdigest()[:12]
    readable = re.sub(r"[^A-Za-z0-9_.-]+", "_", key)[-80:]
    return f"{digest}_{readable}.json"


def _bucket(state: dict[str, Any], kind: str, name: str, delta_count: int, start_ids: list[str]) -> dict[str, Any]:
    buckets = state[kind]
    if name not in buckets:
        buckets[name] = {
            "gram": np.zeros((delta_count, delta_count), dtype=np.float64).tolist(),
            "start_norm_sq": {model_id: 0.0 for model_id in start_ids},
            "parameter_count": 0,
            "tensor_count": 0,
        }
    return buckets[name]


def add_array(target: list[list[float]], value: np.ndarray) -> list[list[float]]:
    return (np.asarray(target, dtype=np.float64) + value).tolist()


def read_chunk(reader: Any, key: str, selection: tuple[Any, ...]) -> torch.Tensor:
    value = _read_chunk(reader, key, selection)
    if value.is_floating_point():
        value = value.float()
        if not torch.isfinite(value).all().item():
            raise ValueError(f"NaN or Inf in checkpoint tensor {key}")
    return value


def process_tensor(
    key: str,
    inputs: RunInputs,
    layouts: dict[str, ModelLayout],
    chunk_elements: int,
    device: torch.device,
    start_ids: list[str],
) -> dict[str, Any]:
    delta_count = len(inputs.deltas)
    tensor_gram = np.zeros((delta_count, delta_count), dtype=np.float64)
    start_norm_sq = {model_id: 0.0 for model_id in start_ids}
    shape = layouts["base"].shapes[key]
    required_models = {"base"}
    for delta in inputs.deltas:
        required_models.update((delta.start, delta.end))

    with ExitStack() as stack:
        readers = {
            model_id: stack.enter_context(
                safe_open(layout.root / layout.weight_map[key], framework="pt", device="cpu")
            )
            for model_id, layout in layouts.items()
            if model_id in required_models
        }
        first_selection = next(iter(_chunks(shape, chunk_elements)))
        first = read_chunk(readers["base"], key, first_selection)
        if not first.is_floating_point():
            base_value = readers["base"].get_tensor(key)
            for model_id, reader in readers.items():
                if model_id != "base" and not torch.equal(base_value, reader.get_tensor(key)):
                    raise ValueError(f"Non-floating tensor changed in {model_id}: {key}")
            return {
                "key": key,
                "floating": False,
                "shape": list(shape),
                "parameter_count": 0,
            }

        for selection in _chunks(shape, chunk_elements):
            values = {
                model_id: read_chunk(reader, key, selection)
                for model_id, reader in readers.items()
            }
            flat_deltas = [
                (values[delta.end] - values[delta.start]).reshape(-1)
                for delta in inputs.deltas
            ]
            delta_matrix = torch.stack(flat_deltas).to(device=device, non_blocking=False)
            chunk_gram = (delta_matrix @ delta_matrix.T).double().cpu().numpy()
            tensor_gram += chunk_gram
            del delta_matrix, flat_deltas

            for model_id in start_ids:
                vector = values[model_id].reshape(-1).to(device=device, non_blocking=False)
                start_norm_sq[model_id] += float(torch.dot(vector, vector).double().cpu().item())
                del vector
            del values

    if not np.isfinite(tensor_gram).all():
        raise ValueError(f"Non-finite Gram contribution for {key}")
    return {
        "key": key,
        "floating": True,
        "shape": list(shape),
        "parameter_count": int(math.prod(shape)) if shape else 1,
        "gram": tensor_gram.tolist(),
        "start_norm_sq": start_norm_sq,
        "layer": layer_name(key),
        "module": module_name(key),
    }


def merge_tensor_result(
    state: dict[str, Any],
    result: dict[str, Any],
    delta_count: int,
    start_ids: list[str],
) -> None:
    key = result["key"]
    if not result["floating"]:
        state["non_floating_tensors"].append(key)
        state["completed_tensors"].append(key)
        return
    gram = np.asarray(result["gram"], dtype=np.float64)
    state["gram"] = add_array(state["gram"], gram)
    for model_id in start_ids:
        state["start_norm_sq"][model_id] += float(result["start_norm_sq"][model_id])
    parameter_count = int(result["parameter_count"])
    state["floating_parameter_count"] += parameter_count
    for kind, name in (("layers", result["layer"]), ("modules", result["module"])):
        bucket = _bucket(state, kind, name, delta_count, start_ids)
        bucket["gram"] = add_array(bucket["gram"], gram)
        for model_id in start_ids:
            bucket["start_norm_sq"][model_id] += float(result["start_norm_sq"][model_id])
        bucket["parameter_count"] += parameter_count
        bucket["tensor_count"] += 1
    state["completed_tensors"].append(key)


def delta_norm_rows(
    gram: np.ndarray,
    inputs: RunInputs,
    start_norm_sq: dict[str, float],
    parameter_count: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, delta in enumerate(inputs.deltas):
        norm_sq = max(0.0, float(gram[index, index]))
        norm = math.sqrt(norm_sq)
        start_norm = math.sqrt(max(0.0, float(start_norm_sq[delta.start])))
        rows.append(
            {
                "delta_id": delta.delta_id,
                "family": delta.family,
                "round": delta.round,
                "start": delta.start,
                "end": delta.end,
                "parameter_count": parameter_count,
                "l2_norm": norm,
                "rms": norm / math.sqrt(parameter_count) if parameter_count else 0.0,
                "start_l2_norm": start_norm,
                "relative_l2": norm / start_norm if start_norm else 0.0,
            }
        )
    return rows


def group_rows(
    state: dict[str, Any],
    kind: str,
    inputs: RunInputs,
    global_gram: np.ndarray,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for group_name, bucket in sorted(state[kind].items()):
        gram = np.asarray(bucket["gram"], dtype=np.float64)
        norms = delta_norm_rows(
            gram,
            inputs,
            bucket["start_norm_sq"],
            int(bucket["parameter_count"]),
        )
        cosine = cosine_from_gram(gram)
        for index, row in enumerate(norms):
            row = {"group_type": kind[:-1], "group": group_name, **row}
            global_norm_sq = max(0.0, float(global_gram[index, index]))
            group_norm_sq = max(0.0, float(gram[index, index]))
            row["fraction_global_delta_norm_sq"] = (
                group_norm_sq / global_norm_sq if global_norm_sq else 0.0
            )
            family_indices = [
                i for i, spec in enumerate(inputs.deltas) if spec.family == inputs.deltas[index].family
            ]
            family_position = family_indices.index(index)
            if family_position > 0:
                previous = family_indices[family_position - 1]
                row["previous_round_cosine"] = float(cosine[index, previous])
            else:
                # Keep this column numeric for both CSV and Parquet.  An empty
                # string makes PyArrow infer an object/string column and then
                # reject the later floating-point values.
                row["previous_round_cosine"] = None
            rows.append(row)
    return rows


def empty_composition_accumulator(fingerprint: str, rounds: int) -> dict[str, Any]:
    return {
        "format_version": 1,
        "fingerprint": fingerprint,
        "completed_tensors": [],
        "actual_norm_sq": [0.0] * rounds,
        "intended_norm_sq": [0.0] * rounds,
        "residual_norm_sq": [0.0] * rounds,
        "actual_intended_dot": [0.0] * rounds,
        "parameter_count": 0,
    }


def process_composition_tensor(
    key: str,
    inputs: RunInputs,
    layouts: dict[str, ModelLayout],
    chunk_elements: int,
    device: torch.device,
) -> dict[str, Any]:
    shape = layouts["base"].shapes[key]
    required = ["base"] + [f"r{i}" for i in range(1, inputs.rounds + 1)] + [
        f"v{i}" for i in range(1, inputs.rounds + 1)
    ]
    metrics = {
        "actual_norm_sq": np.zeros(inputs.rounds, dtype=np.float64),
        "intended_norm_sq": np.zeros(inputs.rounds, dtype=np.float64),
        "residual_norm_sq": np.zeros(inputs.rounds, dtype=np.float64),
        "actual_intended_dot": np.zeros(inputs.rounds, dtype=np.float64),
    }
    with ExitStack() as stack:
        readers = {
            model_id: stack.enter_context(
                safe_open(
                    layouts[model_id].root / layouts[model_id].weight_map[key],
                    framework="pt",
                    device="cpu",
                )
            )
            for model_id in required
        }
        first_selection = next(iter(_chunks(shape, chunk_elements)))
        first = read_chunk(readers["base"], key, first_selection)
        if not first.is_floating_point():
            base_value = readers["base"].get_tensor(key)
            for model_id, reader in readers.items():
                if model_id != "base" and not torch.equal(base_value, reader.get_tensor(key)):
                    raise ValueError(f"Non-floating composition tensor changed in {model_id}: {key}")
            return {"key": key, "floating": False, "parameter_count": 0}

        for selection in _chunks(shape, chunk_elements):
            base = read_chunk(readers["base"], key, selection).reshape(-1).to(device)
            intended = torch.zeros_like(base)
            for index in range(inputs.rounds):
                rank = read_chunk(readers[f"r{index + 1}"], key, selection).reshape(-1).to(device)
                composed = read_chunk(readers[f"v{index + 1}"], key, selection).reshape(-1).to(device)
                intended = intended + (rank - base)
                actual = composed - base
                residual = actual - intended
                metrics["actual_norm_sq"][index] += float(torch.dot(actual, actual).double().cpu())
                metrics["intended_norm_sq"][index] += float(torch.dot(intended, intended).double().cpu())
                metrics["residual_norm_sq"][index] += float(torch.dot(residual, residual).double().cpu())
                metrics["actual_intended_dot"][index] += float(
                    torch.dot(actual, intended).double().cpu()
                )
                del rank, composed, actual, residual
            del base, intended
    return {
        "key": key,
        "floating": True,
        "parameter_count": int(math.prod(shape)) if shape else 1,
        **{name: value.tolist() for name, value in metrics.items()},
    }


def run_composition_validation(
    output: Path,
    inputs: RunInputs,
    layouts: dict[str, ModelLayout],
    keys: list[str],
    fingerprint: str,
    chunk_elements: int,
    device: torch.device,
    resume: bool,
) -> list[dict[str, Any]]:
    cache_dir = output / "cache"
    state_path = cache_dir / "composition_accumulator.json"
    tensor_dir = cache_dir / "composition_tensors"
    tensor_dir.mkdir(parents=True, exist_ok=True)
    if state_path.exists():
        if not resume:
            raise FileExistsError(
                f"Composition cache already exists: {state_path}; pass --resume"
            )
        state = json.loads(state_path.read_text(encoding="utf-8"))
        if state.get("fingerprint") != fingerprint:
            raise RuntimeError("Composition validation fingerprint mismatch")
    else:
        state = empty_composition_accumulator(fingerprint, inputs.rounds)
    completed = set(state["completed_tensors"])
    for position, key in enumerate((key for key in keys if key not in completed), start=1):
        print(f"[composition {position}] {key}", flush=True)
        result = process_composition_tensor(key, inputs, layouts, chunk_elements, device)
        atomic_json(tensor_dir / tensor_cache_name(key), result)
        if result["floating"]:
            for metric in (
                "actual_norm_sq",
                "intended_norm_sq",
                "residual_norm_sq",
                "actual_intended_dot",
            ):
                state[metric] = (
                    np.asarray(state[metric], dtype=np.float64)
                    + np.asarray(result[metric], dtype=np.float64)
                ).tolist()
            state["parameter_count"] += int(result["parameter_count"])
        state["completed_tensors"].append(key)
        atomic_json(state_path, state)
    if len(set(state["completed_tensors"])) != len(keys):
        raise RuntimeError("Composition validation did not process every tensor")
    rows: list[dict[str, Any]] = []
    for index in range(inputs.rounds):
        actual_sq = max(0.0, float(state["actual_norm_sq"][index]))
        intended_sq = max(0.0, float(state["intended_norm_sq"][index]))
        residual_sq = max(0.0, float(state["residual_norm_sq"][index]))
        dot = float(state["actual_intended_dot"][index])
        actual_norm = math.sqrt(actual_sq)
        intended_norm = math.sqrt(intended_sq)
        denominator = actual_norm * intended_norm
        rows.append(
            {
                "round": index + 1,
                "actual_composed_norm": actual_norm,
                "intended_cumulative_norm": intended_norm,
                "actual_intended_cosine": max(-1.0, min(1.0, dot / denominator))
                if denominator
                else 0.0,
                "residual_norm": math.sqrt(residual_sq),
                "relative_residual": math.sqrt(residual_sq) / actual_norm if actual_norm else 0.0,
                "parameter_count": state["parameter_count"],
            }
        )
    write_csv(output / "metrics/composition_consistency.csv", list(rows[0]), rows)
    return rows


def validate_numerical_invariants(
    state: dict[str, Any], gram: np.ndarray, cosine: np.ndarray
) -> dict[str, Any]:
    """Fail closed if aggregation or the small global Gram matrix is inconsistent."""

    symmetric = (gram + gram.T) / 2.0
    scale = max(1.0, float(np.max(np.abs(gram))))
    symmetry_relative = float(np.max(np.abs(gram - gram.T))) / scale
    eigenvalues = np.linalg.eigvalsh(symmetric)
    max_eigenvalue = max(1.0, float(np.max(eigenvalues)))
    minimum_eigenvalue = float(np.min(eigenvalues))
    minimum_eigenvalue_relative = minimum_eigenvalue / max_eigenvalue

    nonzero = np.diag(gram) > 0.0
    cosine_diagonal_error = (
        float(np.max(np.abs(np.diag(cosine)[nonzero] - 1.0))) if np.any(nonzero) else 0.0
    )

    aggregate_checks: dict[str, dict[str, float | int]] = {}
    for kind in ("layers", "modules"):
        buckets = state[kind]
        aggregate_gram = sum(
            (np.asarray(bucket["gram"], dtype=np.float64) for bucket in buckets.values()),
            np.zeros_like(gram),
        )
        gram_relative_error = float(np.max(np.abs(aggregate_gram - gram))) / scale
        parameter_count = sum(int(bucket["parameter_count"]) for bucket in buckets.values())
        aggregate_checks[kind] = {
            "gram_relative_error": gram_relative_error,
            "parameter_count": parameter_count,
        }
        if gram_relative_error > 1e-10:
            raise RuntimeError(f"{kind} Gram aggregation does not reproduce the global Gram")
        if parameter_count != int(state["floating_parameter_count"]):
            raise RuntimeError(f"{kind} parameter count does not reproduce the global count")

    if symmetry_relative > 1e-12:
        raise RuntimeError("Global Gram matrix is not symmetric within numerical tolerance")
    if minimum_eigenvalue_relative < -1e-5:
        raise RuntimeError("Global Gram matrix is not positive semidefinite within tolerance")
    if cosine_diagonal_error > 1e-10:
        raise RuntimeError("Nonzero-delta cosine diagonal differs from one")

    return {
        "status": "passed",
        "symmetry_relative_error": symmetry_relative,
        "minimum_eigenvalue": minimum_eigenvalue,
        "minimum_eigenvalue_relative": minimum_eigenvalue_relative,
        "cosine_diagonal_max_error": cosine_diagonal_error,
        "aggregate_checks": aggregate_checks,
        "tolerances": {
            "symmetry_relative_error": 1e-12,
            "minimum_eigenvalue_relative": -1e-5,
            "cosine_diagonal_max_error": 1e-10,
            "aggregate_gram_relative_error": 1e-10,
        },
    }


def save_derived_outputs(
    output: Path,
    inputs: RunInputs,
    state: dict[str, Any],
    fingerprint_payload: dict[str, Any],
    device_name: str,
    chunk_elements: int,
) -> None:
    gram = np.asarray(state["gram"], dtype=np.float64)
    delta_ids = inputs.delta_ids
    derived = derive_geometry(gram, delta_ids)
    cosine = derived["cosine"]
    numerical_validation = validate_numerical_invariants(state, gram, cosine)

    metrics_dir = output / "metrics"
    matrices_dir = output / "matrices"
    embeddings_dir = output / "embeddings"
    cache_dir = output / "cache"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    matrices_dir.mkdir(parents=True, exist_ok=True)
    embeddings_dir.mkdir(parents=True, exist_ok=True)
    atomic_json(metrics_dir / "numerical_validation.json", numerical_validation)

    global_rows = delta_norm_rows(
        gram,
        inputs,
        state["start_norm_sq"],
        int(state["floating_parameter_count"]),
    )
    write_csv(metrics_dir / "global_norms.csv", list(global_rows[0]), global_rows)

    direction_rows: list[dict[str, Any]] = []
    for family, rows in derived["adjacent"].items():
        direction_rows.extend({"metric": "adjacent", "family": family, **row} for row in rows)
    for family, rows in derived["historical"].items():
        direction_rows.extend({"metric": "historical", "family": family, **row} for row in rows)
    direction_fields = sorted({key for row in direction_rows for key in row})
    write_csv(metrics_dir / "direction_metrics.csv", direction_fields, direction_rows)

    relex_rows = list(derived["relex"])
    write_csv(metrics_dir / "relex_retention.csv", list(relex_rows[0]), relex_rows)

    layer_rows = group_rows(state, "layers", inputs, gram)
    module_rows = group_rows(state, "modules", inputs, gram)
    group_fields = sorted({key for row in layer_rows + module_rows for key in row})
    write_csv(metrics_dir / "per_layer_metrics.csv", group_fields, layer_rows)
    write_csv(metrics_dir / "per_module_metrics.csv", group_fields, module_rows)
    maybe_write_parquet(metrics_dir / "per_layer_metrics.parquet", layer_rows)
    maybe_write_parquet(metrics_dir / "per_module_metrics.parquet", module_rows)

    tensor_rows: list[dict[str, Any]] = []
    tensor_dir = cache_dir / "tensors"
    for path in sorted(tensor_dir.glob("*.json")):
        item = json.loads(path.read_text(encoding="utf-8"))
        if not item.get("floating"):
            continue
        item_gram = np.asarray(item["gram"], dtype=np.float64)
        for index, delta in enumerate(inputs.deltas):
            tensor_rows.append(
                {
                    "tensor": item["key"],
                    "layer": item["layer"],
                    "module": item["module"],
                    "delta_id": delta.delta_id,
                    "family": delta.family,
                    "round": delta.round,
                    "parameter_count": item["parameter_count"],
                    "l2_norm": math.sqrt(max(0.0, float(item_gram[index, index]))),
                }
            )
    if tensor_rows:
        write_csv(metrics_dir / "per_tensor_norms.csv", list(tensor_rows[0]), tensor_rows)
        maybe_write_parquet(metrics_dir / "per_tensor_norms.parquet", tensor_rows)

    write_matrix_csv(matrices_dir / "all_delta_gram.csv", delta_ids, gram)
    write_matrix_csv(matrices_dir / "all_delta_cosine.csv", delta_ids, cosine)
    for family, indices in derived["families"].items():
        labels = [delta_ids[index] for index in indices]
        write_matrix_csv(
            matrices_dir / f"{family}_cosine.csv",
            labels,
            cosine[np.ix_(indices, indices)],
        )
    q = derived["families"]["questioner_full"]
    rank = derived["families"]["solver_rank1"]
    full = derived["families"]["solver_full"]
    write_rect_matrix_csv(
        matrices_dir / "questioner_solver_cross_cosine.csv",
        [delta_ids[index] for index in q],
        [delta_ids[index] for index in rank],
        cosine[np.ix_(q, rank)],
    )
    write_rect_matrix_csv(
        matrices_dir / "rank1_full_cross_cosine.csv",
        [delta_ids[index] for index in rank],
        [delta_ids[index] for index in full],
        cosine[np.ix_(rank, full)],
    )

    for filename, key in (
        ("direction_svd.csv", "direction"),
        ("rank1_vs_full_svd.csv", "rank_full_direction"),
        ("cumulative_trajectory.csv", "trajectory"),
    ):
        item = derived[key]
        rows = [
            {"label": label, "component_1": float(point[0]), "component_2": float(point[1])}
            for label, point in zip(item["labels"], item["coordinates"])
        ]
        write_csv(embeddings_dir / filename, list(rows[0]), rows)

    with (cache_dir / "gram_matrices.npz.tmp").open("wb") as handle:
        np.savez_compressed(
            handle,
            gram=gram,
            cosine=cosine,
            direction_coordinates=derived["direction"]["coordinates"],
            direction_explained=derived["direction"]["explained"],
            rank_full_coordinates=derived["rank_full_direction"]["coordinates"],
            rank_full_explained=derived["rank_full_direction"]["explained"],
            trajectory_coordinates=derived["trajectory"]["coordinates"],
            trajectory_explained=derived["trajectory"]["explained"],
        )
    os.replace(cache_dir / "gram_matrices.npz.tmp", cache_dir / "gram_matrices.npz")

    manifest = {
        "format_version": 1,
        "analysis_version": ANALYSIS_VERSION,
        "status": "complete",
        "definition": (
            "Questioner: Q1-Base and Qi-Q(i-1); Solver primary: Ri-Base; "
            "Solver control: Ai(step15)-Base"
        ),
        "run_inputs": inputs.to_manifest(),
        "input_fingerprint": state["fingerprint"],
        "fingerprint_payload": fingerprint_payload,
        "device": device_name,
        "chunk_elements": chunk_elements,
        "floating_parameter_count": state["floating_parameter_count"],
        "tensor_count": len(state["completed_tensors"]),
        "non_floating_tensors": state["non_floating_tensors"],
        "direction_explained": derived["direction"]["explained"].tolist(),
        "rank_full_explained": derived["rank_full_direction"]["explained"].tolist(),
        "trajectory_explained": derived["trajectory"]["explained"].tolist(),
        "numerical_validation": numerical_validation,
    }
    atomic_json(output / "manifest.json", manifest)


def configure_device(name: str) -> torch.device:
    device = torch.device(name)
    if device.type == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA requested but torch.cuda.is_available() is false")
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
    return device


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--chunk-elements", type=int, default=1_000_000)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--max-tensors", type=int, help="Dry-run only; process at most N tensors.")
    parser.add_argument(
        "--skip-composed-validation",
        action="store_true",
        help="Skip the second pass that verifies V_i against cumulative rank1 deltas.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.chunk_elements <= 0:
        raise ValueError("--chunk-elements must be positive")
    if args.max_tensors is not None and args.max_tensors <= 0:
        raise ValueError("--max-tensors must be positive")
    output = args.output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    cache_dir = output / "cache"
    tensor_dir = cache_dir / "tensors"
    tensor_dir.mkdir(parents=True, exist_ok=True)

    inputs = discover_run_inputs(args.run_root)
    layouts = inspect_layouts(inputs)
    fingerprint, fingerprint_payload = input_fingerprint(inputs, model_files(layouts), ANALYSIS_VERSION)
    start_ids = list(dict.fromkeys(delta.start for delta in inputs.deltas))
    state_path = cache_dir / "accumulator.json"
    state = load_accumulator(
        state_path,
        fingerprint,
        len(inputs.deltas),
        start_ids,
        args.resume,
    )
    completed = set(state["completed_tensors"])
    device = configure_device(args.device)

    base = layouts["base"]
    keys = sorted(base.task_vector_keys(), key=lambda key: (base.weight_map[key], key))
    pending = [key for key in keys if key not in completed]
    if args.max_tensors is not None:
        pending.sort(key=lambda key: math.prod(base.shapes[key]) if base.shapes[key] else 1)
        pending = pending[: args.max_tensors]
    print(
        f"Delta geometry: {len(inputs.deltas)} deltas, {len(keys)} tensors, "
        f"{len(pending)} pending, device={device}, fingerprint={fingerprint}"
    )

    for position, key in enumerate(pending, start=1):
        print(f"[{position}/{len(pending)}] {key}", flush=True)
        result = process_tensor(
            key,
            inputs,
            layouts,
            args.chunk_elements,
            device,
            start_ids,
        )
        tensor_path = tensor_dir / tensor_cache_name(key)
        atomic_json(tensor_path, result)
        merge_tensor_result(state, result, len(inputs.deltas), start_ids)
        atomic_json(state_path, state)

    all_complete = len(set(state["completed_tensors"])) == len(keys)
    if args.max_tensors is not None and not all_complete:
        atomic_json(
            output / "dry_run_status.json",
            {
                "status": "partial",
                "fingerprint": fingerprint,
                "completed": len(state["completed_tensors"]),
                "total": len(keys),
                "max_tensors": args.max_tensors,
            },
        )
        print(f"Dry-run complete: {len(state['completed_tensors'])}/{len(keys)} tensors cached")
        return
    if not all_complete:
        raise RuntimeError("Analysis ended without processing every tensor")

    if not args.skip_composed_validation:
        run_composition_validation(
            output,
            inputs,
            layouts,
            keys,
            fingerprint,
            args.chunk_elements,
            device,
            args.resume,
        )

    save_derived_outputs(
        output,
        inputs,
        state,
        fingerprint_payload,
        str(device),
        args.chunk_elements,
    )
    print(f"Delta geometry complete: {output}")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"delta geometry analysis failed: {error}", file=sys.stderr)
        raise
