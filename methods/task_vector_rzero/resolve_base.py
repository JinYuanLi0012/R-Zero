#!/usr/bin/env python3
"""Resolve one immutable Base snapshot and verify it on resume."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from huggingface_hub import snapshot_download


ALLOW_PATTERNS = [
    "*.json",
    "*.safetensors",
    "*.model",
    "*.txt",
    "*.jinja",
    "*.py",
    "tokenizer.*",
    "merges.txt",
    "vocab.*",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".tmp-{os.getpid()}")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def build_manifest(source: str, revision: str | None) -> dict[str, Any]:
    candidate = Path(source).expanduser()
    if candidate.is_dir():
        root = candidate.resolve()
        resolved_revision = None
        source_type = "local"
    else:
        root = Path(
            snapshot_download(
                repo_id=source,
                revision=revision,
                allow_patterns=ALLOW_PATTERNS,
            )
        ).resolve()
        resolved_revision = root.name if root.parent.name == "snapshots" else revision
        source_type = "huggingface"

    config = root / "config.json"
    weights = sorted(root.glob("*.safetensors"))
    if not config.is_file() or not weights:
        raise ValueError(f"Resolved Base is not a safetensors HF checkpoint: {root}")
    tracked_suffixes = {".json", ".safetensors", ".model", ".txt", ".jinja", ".py"}
    files = sorted(
        path for path in root.iterdir() if path.is_file() and path.suffix in tracked_suffixes
    )
    file_manifest = [
        {"name": path.name, "size": path.stat().st_size, "sha256": sha256(path)}
        for path in files
    ]
    identity_payload = json.dumps(file_manifest, sort_keys=True, separators=(",", ":")).encode()
    return {
        "format_version": 1,
        "source": source,
        "source_type": source_type,
        "requested_revision": revision,
        "resolved_revision": resolved_revision,
        "resolved_path": str(root),
        "files": file_manifest,
        "identity_sha256": hashlib.sha256(identity_payload).hexdigest(),
    }


def verify_manifest(manifest: dict[str, Any], source: str, revision: str | None) -> None:
    if manifest.get("source") != source or manifest.get("requested_revision") != revision:
        raise ValueError("Existing Base manifest was created for a different source or revision")
    root = Path(manifest["resolved_path"])
    tracked_suffixes = {".json", ".safetensors", ".model", ".txt", ".jinja", ".py"}
    expected_names = {item["name"] for item in manifest.get("files", [])}
    actual_names = {
        path.name for path in root.iterdir() if path.is_file() and path.suffix in tracked_suffixes
    }
    if actual_names != expected_names:
        raise ValueError(
            f"Immutable Base file set changed: missing={sorted(expected_names - actual_names)}, "
            f"extra={sorted(actual_names - expected_names)}"
        )
    for item in manifest.get("files", []):
        path = root / item["name"]
        if not path.is_file() or path.stat().st_size != item["size"] or sha256(path) != item["sha256"]:
            raise ValueError(f"Immutable Base file changed or is missing: {path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--revision")
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()

    if args.manifest.exists():
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        verify_manifest(manifest, args.model, args.revision)
    else:
        manifest = build_manifest(args.model, args.revision)
        atomic_json(args.manifest, manifest)
    print(json.dumps(manifest, sort_keys=True))


if __name__ == "__main__":
    main()
