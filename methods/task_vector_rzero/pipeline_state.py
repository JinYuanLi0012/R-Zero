#!/usr/bin/env python3
"""Atomic state and resume markers for the task-vector R-Zero pipeline."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".tmp-{os.getpid()}")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def parse_fields(items: list[str]) -> dict[str, str]:
    fields: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"Expected KEY=VALUE, got {item!r}")
        key, value = item.split("=", 1)
        if not key:
            raise ValueError(f"Empty field name in {item!r}")
        fields[key] = value
    return fields


def fingerprint(fields: dict[str, str]) -> str:
    payload = json.dumps(fields, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def command_init(args: argparse.Namespace) -> int:
    fields = parse_fields(args.field)
    signature = fingerprint(fields)
    state_path = args.state
    if state_path.exists():
        state = load_json(state_path)
        previous = state.get("run_fingerprint")
        if previous != signature:
            raise RuntimeError(
                f"Existing run state has fingerprint {previous}, current config has {signature}. "
                "Use a different RUN_NAME instead of reusing incompatible artifacts."
            )
    else:
        state = {
            "format_version": 1,
            "created_at": now(),
            "run_fingerprint": signature,
            "configuration": fields,
            "stages": {},
        }
        atomic_json(state_path, state)
    print(signature)
    return 0


def artifacts_exist(paths: list[str]) -> bool:
    return all(Path(path).exists() for path in paths)


def command_check(args: argparse.Namespace) -> int:
    if not args.marker.is_file():
        return 1
    try:
        marker = load_json(args.marker)
    except (OSError, json.JSONDecodeError):
        return 1
    if marker.get("run_fingerprint") != args.fingerprint:
        return 1
    recorded = [str(path) for path in marker.get("artifacts", [])]
    if not artifacts_exist(recorded) or not artifacts_exist(args.require):
        return 1
    return 0


def command_complete(args: argparse.Namespace) -> int:
    missing = [path for path in args.artifact if not Path(path).exists()]
    if missing:
        raise FileNotFoundError(f"Cannot complete {args.stage}; missing artifacts: {missing}")
    metadata = parse_fields(args.meta)
    marker = {
        "stage": args.stage,
        "completed_at": now(),
        "run_fingerprint": args.fingerprint,
        "artifacts": args.artifact,
        "metadata": metadata,
    }
    atomic_json(args.marker, marker)

    state = load_json(args.state)
    if state.get("run_fingerprint") != args.fingerprint:
        raise RuntimeError("Run fingerprint changed while completing a stage")
    state.setdefault("stages", {})[args.stage] = marker
    state["updated_at"] = now()
    atomic_json(args.state, state)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init")
    init.add_argument("--state", required=True, type=Path)
    init.add_argument("--field", action="append", default=[])
    init.set_defaults(function=command_init)

    check = subparsers.add_parser("check")
    check.add_argument("--marker", required=True, type=Path)
    check.add_argument("--fingerprint", required=True)
    check.add_argument("--require", action="append", default=[])
    check.set_defaults(function=command_check)

    complete = subparsers.add_parser("complete")
    complete.add_argument("--state", required=True, type=Path)
    complete.add_argument("--marker", required=True, type=Path)
    complete.add_argument("--stage", required=True)
    complete.add_argument("--fingerprint", required=True)
    complete.add_argument("--artifact", action="append", default=[])
    complete.add_argument("--meta", action="append", default=[])
    complete.set_defaults(function=command_complete)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.function(args)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print(f"pipeline state error: {error}", file=sys.stderr)
        sys.exit(2)
