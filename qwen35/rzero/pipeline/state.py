"""Atomic manifests, fingerprints and artifact validation."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class StateError(RuntimeError):
    pass


def canonical_hash(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temporary, path)


@dataclass(frozen=True)
class Artifact:
    path: Path
    kind: str = "file"
    expected_count: int | None = None


def validate_artifact(artifact: Artifact) -> dict[str, Any]:
    path = artifact.path
    if artifact.kind == "directory":
        if not path.is_dir() or not any(path.iterdir()):
            raise StateError(f"missing or empty directory: {path}")
        return {"path": str(path), "kind": artifact.kind}
    if artifact.kind == "model":
        if not (path / "config.json").is_file():
            raise StateError(f"model has no config.json: {path}")
        weights = list(path.glob("*.safetensors")) + list(path.glob("*.safetensors.index.json"))
        if not weights:
            raise StateError(f"model has no safetensors: {path}")
        return {
            "path": str(path),
            "kind": artifact.kind,
            "config_sha256": file_hash(path / "config.json"),
            "weights": sorted((item.name, item.stat().st_size) for item in weights),
        }
    if artifact.kind == "checkpoint":
        if not path.is_dir() or not (path / "fsdp_config.json").is_file():
            raise StateError(f"incomplete FSDP checkpoint: {path}")
        required_patterns = ["model_world_size_*_rank_*.pt", "optim_world_size_*_rank_*.pt", "extra_state_world_size_*_rank_*.pt"]
        files = []
        for pattern in required_patterns:
            matches = list(path.glob(pattern))
            if not matches:
                raise StateError(f"checkpoint {path} has no {pattern}")
            files.extend(matches)
        return {
            "path": str(path),
            "kind": artifact.kind,
            "fsdp_config_sha256": file_hash(path / "fsdp_config.json"),
            "files": sorted((item.name, item.stat().st_size) for item in files),
        }
    if not path.is_file() or path.stat().st_size == 0:
        raise StateError(f"missing or empty file: {path}")
    details: dict[str, Any] = {
        "path": str(path),
        "kind": artifact.kind,
        "size": path.stat().st_size,
        "sha256": file_hash(path),
    }
    if artifact.kind == "json":
        value = json.loads(path.read_text(encoding="utf-8"))
        if artifact.expected_count is not None:
            if not isinstance(value, list) or len(value) != artifact.expected_count:
                raise StateError(f"{path}: expected {artifact.expected_count} JSON rows")
            details["count"] = len(value)
    return details


class RunState:
    def __init__(self, run_dir: Path, fingerprint: str):
        self.run_dir = run_dir.resolve()
        self.fingerprint = fingerprint
        self.manifest_dir = self.run_dir / "manifests"

    def initialize(self, config_snapshot: dict[str, Any]) -> None:
        self.run_dir.mkdir(parents=True, exist_ok=True)
        run_manifest = self.manifest_dir / "run.json"
        if run_manifest.exists():
            existing = json.loads(run_manifest.read_text(encoding="utf-8"))
            if existing.get("fingerprint") != self.fingerprint:
                raise StateError("run fingerprint differs; use a new --run-dir")
            return
        atomic_write_json(
            run_manifest,
            {
                "schema_version": 1,
                "fingerprint": self.fingerprint,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "config": config_snapshot,
            },
        )

    def stage_manifest(self, stage_key: str) -> Path:
        return self.manifest_dir / "stages" / f"{stage_key}.json"

    def is_complete(
        self, stage_key: str, artifacts: list[Artifact], inputs: list[Artifact] | None = None
    ) -> bool:
        path = self.stage_manifest(stage_key)
        if not path.is_file():
            return False
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
            if manifest.get("status") != "complete" or manifest.get("fingerprint") != self.fingerprint:
                return False
            current = [validate_artifact(item) for item in artifacts]
            recorded = manifest.get("artifacts", [])
            current_inputs = [validate_artifact(item) for item in (inputs or [])]
            return current == recorded and current_inputs == manifest.get("inputs", [])
        except (OSError, ValueError, StateError, json.JSONDecodeError):
            return False

    def commit(
        self,
        stage_key: str,
        artifacts: list[Artifact],
        metadata: dict[str, Any] | None = None,
        inputs: list[Artifact] | None = None,
    ) -> None:
        validated = [validate_artifact(item) for item in artifacts]
        validated_inputs = [validate_artifact(item) for item in (inputs or [])]
        atomic_write_json(
            self.stage_manifest(stage_key),
            {
                "schema_version": 1,
                "stage": stage_key,
                "status": "complete",
                "fingerprint": self.fingerprint,
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "artifacts": validated,
                "inputs": validated_inputs,
                "metadata": metadata or {},
            },
        )

    def invalidate_from(self, ordered_keys: list[str], first_key: str) -> None:
        if first_key not in ordered_keys:
            raise StateError(f"unknown --from-stage {first_key!r}")
        for key in ordered_keys[ordered_keys.index(first_key) :]:
            manifest = self.stage_manifest(key)
            if manifest.exists():
                manifest.unlink()
