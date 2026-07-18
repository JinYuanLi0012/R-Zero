#!/usr/bin/env python3
"""Resolve the initial center to one immutable local HF snapshot."""

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
TRACKED_SUFFIXES = {".json", ".safetensors", ".model", ".txt", ".jinja", ".py"}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.tmp-{os.getpid()}")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _token() -> str | None:
    token = os.getenv("HF_TOKEN") or os.getenv("HUGGING_FACE_HUB_TOKEN")
    token_file = Path("tokens.json")
    if not token and token_file.is_file():
        token = json.loads(token_file.read_text(encoding="utf-8")).get("huggingface")
    return token


def _file_manifest(root: Path) -> list[dict[str, object]]:
    files = sorted(path for path in root.iterdir() if path.is_file() and path.suffix in TRACKED_SUFFIXES)
    return [
        {"name": path.name, "size": path.stat().st_size, "sha256": _sha256(path)}
        for path in files
    ]


def build_manifest(source: str, revision: str | None) -> dict[str, Any]:
    candidate = Path(source).expanduser()
    if candidate.is_dir():
        root = candidate.resolve()
        source_type = "local"
        resolved_revision = None
    else:
        root = Path(
            snapshot_download(
                repo_id=source,
                revision=revision,
                allow_patterns=ALLOW_PATTERNS,
                token=_token(),
            )
        ).resolve()
        source_type = "huggingface"
        resolved_revision = root.name if root.parent.name == "snapshots" else revision

    if not (root / "config.json").is_file() or not list(root.glob("*.safetensors")):
        raise ValueError(f"resolved base is not a safetensors Hugging Face checkpoint: {root}")
    files = _file_manifest(root)
    encoded = json.dumps(files, sort_keys=True, separators=(",", ":")).encode()
    return {
        "format_version": 1,
        "source": source,
        "source_type": source_type,
        "requested_revision": revision,
        "resolved_revision": resolved_revision,
        "resolved_path": str(root),
        "files": files,
        "identity_sha256": hashlib.sha256(encoded).hexdigest(),
    }


def verify_manifest(manifest: dict[str, Any], source: str, revision: str | None) -> None:
    if manifest.get("source") != source or manifest.get("requested_revision") != revision:
        raise ValueError("existing base manifest belongs to a different source or revision")
    root = Path(manifest["resolved_path"])
    if not root.is_dir():
        raise ValueError(f"resolved base directory is missing: {root}")
    expected = {str(item["name"]): item for item in manifest.get("files", [])}
    actual_names = {
        path.name for path in root.iterdir() if path.is_file() and path.suffix in TRACKED_SUFFIXES
    }
    if actual_names != set(expected):
        raise ValueError("immutable base file set changed")
    for name, item in expected.items():
        path = root / name
        if path.stat().st_size != item["size"] or _sha256(path) != item["sha256"]:
            raise ValueError(f"immutable base file changed: {path}")


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
        _atomic_json(args.manifest, manifest)
    print(json.dumps(manifest, sort_keys=True))


if __name__ == "__main__":
    main()
