"""Checkpoint lineage guard for safe verl recovery."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qwen35.rzero.pipeline.state import Artifact, StateError, atomic_write_json, canonical_hash, validate_artifact


LINEAGE_FILE = "RZERO_TRAINING_LINEAGE.json"


def build_training_lineage(
    *,
    role: str,
    model: Path,
    train_file: Path,
    val_file: Path,
    config_snapshot: dict[str, Any],
    total_steps: int,
) -> dict[str, Any]:
    snapshot = {key: value for key, value in config_snapshot.items() if not key.startswith("_")}
    model_artifact = validate_artifact(Artifact(model, "model"))
    return {
        "schema_version": 1,
        "role": role,
        "total_steps": total_steps,
        "config_fingerprint": canonical_hash(snapshot),
        "model_fingerprint": canonical_hash(model_artifact),
        "model": model_artifact,
        "train_data": validate_artifact(Artifact(train_file)),
        "validation_data": validate_artifact(Artifact(val_file)),
    }


def ensure_training_lineage(checkpoint_root: Path, expected: dict[str, Any], *, resume: bool) -> Path:
    """Create/validate lineage before verl may inspect an output directory."""
    checkpoint_root.mkdir(parents=True, exist_ok=True)
    lineage_path = checkpoint_root / LINEAGE_FILE
    checkpoint_state = list(checkpoint_root.glob("global_step*"))
    tracker = checkpoint_root / "latest_checkpointed_iteration.txt"

    if lineage_path.is_file():
        try:
            recorded = json.loads(lineage_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise StateError(f"invalid training lineage: {lineage_path}") from error
        if canonical_hash(recorded) != canonical_hash(expected):
            raise StateError(
                f"checkpoint lineage mismatch at {checkpoint_root}; refusing to resume or relabel stale training state"
            )
        if not resume and (checkpoint_state or tracker.exists()):
            raise StateError(f"fresh training requested but checkpoint state already exists: {checkpoint_root}")
        return lineage_path

    if checkpoint_state or tracker.exists():
        raise StateError(f"checkpoint state has no R-Zero lineage and cannot be trusted: {checkpoint_root}")
    atomic_write_json(lineage_path, expected)
    return lineage_path
