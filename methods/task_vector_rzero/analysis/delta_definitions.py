#!/usr/bin/env python3
"""Discover immutable checkpoints and define the analysis delta families."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DeltaSpec:
    """One parameter delta, expressed as end checkpoint minus start checkpoint."""

    delta_id: str
    family: str
    round: int
    start: str
    end: str


@dataclass(frozen=True)
class RunInputs:
    run_root: Path
    base_identity: str
    checkpoints: dict[str, Path]
    deltas: tuple[DeltaSpec, ...]
    rounds: int

    @property
    def delta_ids(self) -> list[str]:
        return [item.delta_id for item in self.deltas]

    def to_manifest(self) -> dict[str, Any]:
        return {
            "run_root": str(self.run_root),
            "base_identity": self.base_identity,
            "rounds": self.rounds,
            "checkpoints": {key: str(value) for key, value in self.checkpoints.items()},
            "deltas": [asdict(item) for item in self.deltas],
        }


def _load(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def _require_stage(state: dict[str, Any], stage: str) -> None:
    item = state.get("stages", {}).get(stage)
    if not item:
        raise ValueError(f"Run is missing completed stage {stage!r}")
    artifacts = [Path(path) for path in item.get("artifacts", [])]
    if not artifacts or not all(path.exists() for path in artifacts):
        raise ValueError(f"Completed stage {stage!r} has missing artifacts")


def _questioner_path(run_root: Path, round_number: int) -> Path:
    if round_number == 1:
        return run_root / "questioners/q1/huggingface"
    return run_root / f"questioners/q{round_number}/global_step_5/actor/huggingface"


def discover_run_inputs(run_root: Path, rounds: int = 5) -> RunInputs:
    """Resolve all model paths and enforce the plan's exact delta definitions."""

    run_root = run_root.expanduser().resolve()
    state = _load(run_root / "state/run_state.json")
    base_manifest = _load(run_root / "state/base_manifest.json")
    configured_rounds = int(state.get("configuration", {}).get("num_rounds", rounds))
    if configured_rounds != rounds:
        raise ValueError(f"Expected {rounds} rounds, run records {configured_rounds}")
    if state.get("configuration", {}).get("task_vector_method") != "relex_rank1":
        raise ValueError("Delta geometry v1 requires a relex_rank1 run")

    base = Path(base_manifest["resolved_path"]).expanduser().resolve()
    checkpoints: dict[str, Path] = {"base": base}
    for round_number in range(1, rounds + 1):
        for stage in ("questioner", "base_fit", "relex_rank1", "compose"):
            _require_stage(state, f"round_{round_number}/{stage}")
        checkpoints[f"q{round_number}"] = _questioner_path(run_root, round_number)
        checkpoints[f"a{round_number}"] = (
            run_root
            / f"base_fits/a{round_number}/global_step_15/actor/huggingface"
        )
        checkpoints[f"r{round_number}"] = run_root / f"rank1_fits/r{round_number}"
        checkpoints[f"v{round_number}"] = run_root / f"composed_solvers/v{round_number}"

    missing = {key: path for key, path in checkpoints.items() if not path.is_dir()}
    if missing:
        rendered = ", ".join(f"{key}={path}" for key, path in missing.items())
        raise FileNotFoundError(f"Missing model directories: {rendered}")

    deltas: list[DeltaSpec] = []
    for round_number in range(1, rounds + 1):
        q_start = "base" if round_number == 1 else f"q{round_number - 1}"
        deltas.append(
            DeltaSpec(
                f"questioner_full_r{round_number}",
                "questioner_full",
                round_number,
                q_start,
                f"q{round_number}",
            )
        )
    for round_number in range(1, rounds + 1):
        deltas.append(
            DeltaSpec(
                f"solver_rank1_r{round_number}",
                "solver_rank1",
                round_number,
                "base",
                f"r{round_number}",
            )
        )
    for round_number in range(1, rounds + 1):
        deltas.append(
            DeltaSpec(
                f"solver_full_r{round_number}",
                "solver_full",
                round_number,
                "base",
                f"a{round_number}",
            )
        )

    return RunInputs(
        run_root=run_root,
        base_identity=str(base_manifest["identity_sha256"]),
        checkpoints=checkpoints,
        deltas=tuple(deltas),
        rounds=rounds,
    )


def input_fingerprint(
    inputs: RunInputs,
    model_files: dict[str, list[Path]],
    analysis_version: int = 1,
) -> tuple[str, dict[str, Any]]:
    """Fingerprint definitions and cheap immutable file metadata for resume safety."""

    files: dict[str, list[dict[str, Any]]] = {}
    for model_id, paths in sorted(model_files.items()):
        files[model_id] = [
            {
                "path": str(path.resolve()),
                "size": path.stat().st_size,
                "mtime_ns": path.stat().st_mtime_ns,
            }
            for path in sorted(paths)
        ]
    payload = {
        "analysis_version": analysis_version,
        "inputs": inputs.to_manifest(),
        "files": files,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest(), payload
