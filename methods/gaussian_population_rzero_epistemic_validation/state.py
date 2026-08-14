#!/usr/bin/env python3
"""Tiny atomic completion markers used by run.sh --resume."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from common import atomic_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["is-complete", "complete"])
    parser.add_argument("--state-dir", type=Path, required=True)
    parser.add_argument("--stage", required=True)
    args = parser.parse_args()
    marker = args.state_dir / f"{args.stage}.complete.json"
    if args.command == "is-complete":
        raise SystemExit(0 if marker.is_file() else 1)
    atomic_json(marker, {"stage": args.stage, "completed_at": datetime.now(timezone.utc).isoformat()})


if __name__ == "__main__":
    main()
