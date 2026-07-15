#!/usr/bin/env python3
"""Build Base + scale * (round-1 RELEX Rank-1 model - Base).

This is a post-processing experiment over one completed task-vector R-Zero run.
It never trains a model and never mutates the source run.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from .compose_task_vectors import (
        DEFAULT_CHUNK_ELEMENTS,
        ModelLayout,
        _json_dump,
        _sha256,
        compose,
        validate_compatible,
    )
    from .resolve_base import verify_manifest
except ImportError:  # Direct script execution.
    from compose_task_vectors import (
        DEFAULT_CHUNK_ELEMENTS,
        ModelLayout,
        _json_dump,
        _sha256,
        compose,
        validate_compatible,
    )
    from resolve_base import verify_manifest


STATE_NAME = "extrapolation_state.json"
SOURCE_RANK1_MANIFEST = "relex_rank1_manifest.json"
OUTPUT_MANIFEST = "task_vector_manifest.json"


@dataclass(frozen=True)
class SourceRun:
    root: Path
    base_path: Path
    base_provenance: dict[str, Any]
    rank1_path: Path
    rank1_manifest_sha256: str
    rank1_provenance: dict[str, Any]


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Missing JSON file: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def _same_path(left: str | Path, right: str | Path) -> bool:
    return Path(left).expanduser().resolve() == Path(right).expanduser().resolve()


def _validate_weight_records(root: Path, records: Any, description: str) -> None:
    if not isinstance(records, list) or not records:
        raise ValueError(f"{description} has no recorded weight files")
    for record in records:
        if not isinstance(record, dict):
            raise ValueError(f"Invalid weight record in {description}")
        name = record.get("name")
        if not isinstance(name, str) or Path(name).name != name:
            raise ValueError(f"Unsafe weight filename in {description}: {name!r}")
        path = root / name
        if not path.is_file():
            raise FileNotFoundError(f"Missing weight file in {description}: {path}")
        if path.stat().st_size != record.get("size"):
            raise ValueError(f"Weight size changed in {description}: {path}")
        if _sha256(path) != record.get("sha256"):
            raise ValueError(f"Weight hash changed in {description}: {path}")


def inspect_source_run(source_root: Path) -> SourceRun:
    source_root = source_root.expanduser().resolve()
    state = _load_json(source_root / "state" / "run_state.json")
    configuration = state.get("configuration") or {}
    if configuration.get("task_vector_method") != "relex_rank1":
        raise ValueError(f"Source run is not a RELEX Rank-1 run: {source_root}")

    rank1_path = (source_root / "rank1_fits" / "r1").resolve()
    marker = _load_json(source_root / "state" / "round_1" / "relex_rank1" / "_SUCCESS.json")
    if marker.get("stage") != "round_1/relex_rank1":
        raise ValueError("Round-1 Rank-1 success marker has the wrong stage")
    if marker.get("run_fingerprint") != state.get("run_fingerprint"):
        raise ValueError("Round-1 Rank-1 marker fingerprint does not match the source run")
    artifacts = marker.get("artifacts") or []
    if not any(_same_path(item, rank1_path) for item in artifacts):
        raise ValueError("Round-1 Rank-1 success marker does not record rank1_fits/r1")

    base_manifest_path = source_root / "state" / "base_manifest.json"
    base_provenance = _load_json(base_manifest_path)
    verify_manifest(
        base_provenance,
        str(base_provenance["source"]),
        base_provenance.get("requested_revision"),
    )
    base_path = Path(base_provenance["resolved_path"]).expanduser().resolve()

    rank1_manifest_path = rank1_path / SOURCE_RANK1_MANIFEST
    rank1_manifest = _load_json(rank1_manifest_path)
    if rank1_manifest.get("algorithm") != "relex_rank1_reconstruct":
        raise ValueError("rank1_fits/r1 is not a RELEX Rank-1 reconstruction")
    if rank1_manifest.get("rank") != 1:
        raise ValueError("rank1_fits/r1 was not reconstructed with rank=1")
    recorded_base = rank1_manifest.get("base") or {}
    expected_identity = base_provenance.get("identity_sha256")
    if expected_identity and recorded_base.get("identity_sha256") != expected_identity:
        raise ValueError("Round-1 Rank-1 model was built from a different immutable Base")
    _validate_weight_records(rank1_path, rank1_manifest.get("weight_files"), "source Rank-1 model")

    validate_compatible(
        ModelLayout.inspect(base_path),
        [ModelLayout.inspect(rank1_path)],
    )
    rank1_manifest_sha256 = _sha256(rank1_manifest_path)
    rank1_provenance = {
        "source": str(rank1_path),
        "resolved_path": str(rank1_path),
        "requested_revision": None,
        "resolved_revision": None,
        "relex_rank1_manifest_sha256": rank1_manifest_sha256,
    }
    return SourceRun(
        root=source_root,
        base_path=base_path,
        base_provenance=base_provenance,
        rank1_path=rank1_path,
        rank1_manifest_sha256=rank1_manifest_sha256,
        rank1_provenance=rank1_provenance,
    )


def _configuration(source: SourceRun, scales: list[float], chunk_elements: int) -> dict[str, Any]:
    return {
        "format_version": 1,
        "experiment": "round1_rank1_delta_extrapolation",
        "formula": "base + scale * (round1_rank1 - base)",
        "source_run_root": str(source.root),
        "base_identity_sha256": source.base_provenance.get("identity_sha256"),
        "round1_rank1_manifest_sha256": source.rank1_manifest_sha256,
        "scales": scales,
        "chunk_elements": chunk_elements,
    }


def _initialize_state(
    output_root: Path,
    configuration: dict[str, Any],
    resume: bool,
) -> dict[str, Any]:
    state_path = output_root / "state" / STATE_NAME
    if output_root.exists():
        if not resume:
            raise FileExistsError(
                f"Extrapolation output already exists: {output_root}. Use --resume or a new output run."
            )
        state = _load_json(state_path)
        if state.get("configuration") != configuration:
            raise ValueError(
                "Existing extrapolation output uses a different source, scale list, or chunk size"
            )
        return state

    (output_root / "state").mkdir(parents=True)
    (output_root / "composed_solvers").mkdir()
    state = {"format_version": 1, "configuration": configuration, "completed": {}}
    _json_dump(state_path, state)
    return state


def _validate_existing_output(
    output: Path,
    base: ModelLayout,
    source: SourceRun,
    scale: float,
    chunk_elements: int,
) -> dict[str, Any]:
    manifest = _load_json(output / OUTPUT_MANIFEST)
    if manifest.get("scales") != [scale]:
        raise ValueError(f"Existing {output} has the wrong scale")
    if manifest.get("chunk_elements") != chunk_elements:
        raise ValueError(f"Existing {output} has a different chunk size")
    auxiliaries = manifest.get("auxiliaries") or []
    if len(auxiliaries) != 1:
        raise ValueError(f"Existing {output} does not contain exactly one task vector")
    auxiliary = auxiliaries[0]
    if auxiliary.get("relex_rank1_manifest_sha256") != source.rank1_manifest_sha256:
        raise ValueError(f"Existing {output} was built from a different Rank-1 delta")
    if not _same_path(auxiliary.get("resolved_path", ""), source.rank1_path):
        raise ValueError(f"Existing {output} points to a different Rank-1 model")
    recorded_base = manifest.get("base") or {}
    if recorded_base.get("identity_sha256") != source.base_provenance.get("identity_sha256"):
        raise ValueError(f"Existing {output} was built from a different Base")
    _validate_weight_records(output, manifest.get("weight_files"), f"extrapolated model {output.name}")
    layout = ModelLayout.inspect(output)
    validate_compatible(base, [layout])
    return manifest


def build_extrapolations(
    source_root: Path,
    output_root: Path,
    scales: list[float],
    chunk_elements: int = DEFAULT_CHUNK_ELEMENTS,
    resume: bool = False,
) -> dict[str, Any]:
    if not scales:
        raise ValueError("At least one scale is required")
    if not all(float("-inf") < scale < float("inf") for scale in scales):
        raise ValueError("Every scale must be finite")
    if len(set(scales)) != len(scales):
        raise ValueError("Scales must be unique")
    if chunk_elements <= 0:
        raise ValueError("chunk_elements must be positive")

    source = inspect_source_run(source_root)
    output_root = output_root.expanduser().resolve()
    if output_root == source.root or source.root in output_root.parents:
        raise ValueError("Output root must be outside the read-only source run")
    configuration = _configuration(source, scales, chunk_elements)
    state = _initialize_state(output_root, configuration, resume)
    state_path = output_root / "state" / STATE_NAME
    base = ModelLayout.inspect(source.base_path)
    rank1 = ModelLayout.inspect(source.rank1_path)

    outputs: list[dict[str, Any]] = []
    for index, scale in enumerate(scales, start=1):
        name = f"v{index}"
        output = output_root / "composed_solvers" / name
        completed = state.setdefault("completed", {})
        if output.exists():
            if not resume:
                raise FileExistsError(f"Output already exists: {output}")
            manifest = _validate_existing_output(
                output, base, source, scale, chunk_elements
            )
            print(f"[resume] validated {name}: scale={scale} path={output}")
        else:
            if name in completed:
                raise FileNotFoundError(
                    f"State records {name} as complete but its model directory is missing: {output}"
                )
            print(f"[build] {name} = Base + {scale} * (R1 - Base)")
            manifest = compose(
                base,
                [rank1],
                [scale],
                output,
                chunk_elements,
                {
                    "base": source.base_provenance,
                    "auxiliaries": [source.rank1_provenance],
                },
            )
            _validate_existing_output(output, base, source, scale, chunk_elements)

        completed[name] = {
            "scale": scale,
            "path": str(output),
            "task_vector_manifest_sha256": _sha256(output / OUTPUT_MANIFEST),
        }
        _json_dump(state_path, state)
        outputs.append({"name": name, "scale": scale, "path": str(output), "manifest": manifest})

    summary = {
        "format_version": 1,
        "configuration": configuration,
        "outputs": [
            {
                "name": item["name"],
                "scale": item["scale"],
                "path": item["path"],
                "task_vector_manifest_sha256": state["completed"][item["name"]][
                    "task_vector_manifest_sha256"
                ],
            }
            for item in outputs
        ],
    }
    _json_dump(output_root / "rank1_extrapolation_manifest.json", summary)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build Base + k * first-round Rank-1 delta without training new rounds."
    )
    parser.add_argument("--source-run-root", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument(
        "--scale",
        action="append",
        type=float,
        dest="scales",
        help="Repeat in output order. Defaults to 1,2,3,4,5.",
    )
    parser.add_argument("--chunk-elements", type=int, default=DEFAULT_CHUNK_ELEMENTS)
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = build_extrapolations(
        args.source_run_root,
        args.output_root,
        args.scales or [1.0, 2.0, 3.0, 4.0, 5.0],
        args.chunk_elements,
        args.resume,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"rank1 extrapolation failed: {error}", file=sys.stderr)
        raise
