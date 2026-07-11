#!/usr/bin/env python3
"""Materialize immutable round-1 Questioner and dataset bootstrap artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from datasets import Dataset, load_dataset
from huggingface_hub import HfApi

try:
    from .resolve_base import atomic_json, build_manifest, hf_token, verify_manifest
except ImportError:
    from resolve_base import atomic_json, build_manifest, hf_token, verify_manifest


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def materialize_model(args: argparse.Namespace) -> None:
    manifest_path = args.manifest
    token = hf_token()
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        verify_manifest(manifest, args.source, args.revision)
    else:
        manifest = build_manifest(args.source, args.revision, token)
        atomic_json(manifest_path, manifest)

    resolved = Path(manifest["resolved_path"]).resolve()
    output = args.output
    if os.path.lexists(output):
        if not output.is_symlink() or output.resolve() != resolved:
            raise ValueError(f"Bootstrap model output does not point to resolved snapshot: {output}")
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = output.with_name(output.name + f".tmp-{os.getpid()}")
        os.symlink(resolved, temporary, target_is_directory=True)
        os.replace(temporary, output)
    print(json.dumps(manifest, indent=2, sort_keys=True))


def _load_source_dataset(
    source: str,
    config: str | None,
    split: str,
    revision: str | None,
    token: str | None,
) -> tuple[Dataset, str | None]:
    candidate = Path(source).expanduser()
    if candidate.is_file():
        return load_dataset("parquet", data_files=str(candidate), split="train"), None
    if candidate.is_dir():
        return load_dataset("parquet", data_dir=str(candidate), split="train"), None

    info = HfApi(token=token).dataset_info(source, revision=revision, token=token)
    resolved_revision = info.sha
    kwargs: dict[str, Any] = {
        "path": source,
        "split": split,
        "revision": resolved_revision,
    }
    if config:
        kwargs["name"] = config
    if token:
        kwargs["token"] = token
    return load_dataset(**kwargs), resolved_revision


def _verify_existing_dataset(args: argparse.Namespace) -> bool:
    if not args.output.is_file() or not args.manifest.is_file():
        return False
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    expected = {
        "source": args.source,
        "requested_revision": args.revision,
        "config": args.config,
        "split": args.split,
    }
    actual = {key: manifest.get(key) for key in expected}
    if actual != expected:
        raise ValueError(f"Existing bootstrap dataset uses different inputs: {actual} != {expected}")
    if sha256(args.output) != manifest.get("parquet_sha256"):
        raise ValueError("Existing bootstrap dataset parquet hash changed")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return True


def materialize_dataset(args: argparse.Namespace) -> None:
    if _verify_existing_dataset(args):
        return
    if args.output.exists() or args.manifest.exists():
        raise FileExistsError("Bootstrap dataset output or manifest already exists incompletely")

    dataset, resolved_revision = _load_source_dataset(
        args.source, args.config, args.split, args.revision, hf_token()
    )
    required = {"problem", "answer"}
    missing = required - set(dataset.column_names)
    if missing:
        raise ValueError(f"Bootstrap dataset is missing required columns: {sorted(missing)}")
    if len(dataset) == 0:
        raise ValueError("Bootstrap dataset is empty")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_name(args.output.name + f".tmp-{os.getpid()}")
    dataset.to_parquet(str(temporary))
    os.replace(temporary, args.output)
    manifest = {
        "format_version": 1,
        "bootstrap": True,
        "source": args.source,
        "requested_revision": args.revision,
        "resolved_revision": resolved_revision,
        "config": args.config,
        "split": args.split,
        "filtered_count": len(dataset),
        "columns": list(dataset.column_names),
        "parquet": args.output.name,
        "parquet_sha256": sha256(args.output),
    }
    atomic_json(args.manifest, manifest)
    print(json.dumps(manifest, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    model = subparsers.add_parser("model")
    model.add_argument("--source", required=True)
    model.add_argument("--revision")
    model.add_argument("--output", required=True, type=Path)
    model.add_argument("--manifest", required=True, type=Path)
    model.set_defaults(function=materialize_model)

    dataset = subparsers.add_parser("dataset")
    dataset.add_argument("--source", required=True)
    dataset.add_argument("--config")
    dataset.add_argument("--split", default="train")
    dataset.add_argument("--revision")
    dataset.add_argument("--output", required=True, type=Path)
    dataset.add_argument("--manifest", required=True, type=Path)
    dataset.set_defaults(function=materialize_dataset)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.function(args)


if __name__ == "__main__":
    main()
