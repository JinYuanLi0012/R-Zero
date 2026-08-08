"""Validate official verl checkpoints and rewind a stale tracker if needed."""

from __future__ import annotations

import os
import re
from pathlib import Path

from qwen35.rzero.pipeline.state import Artifact, StateError, validate_artifact


STEP_PATTERN = re.compile(r"global_steps?_(\d+)$")
TRACKER = "latest_checkpointed_iteration.txt"


def complete_steps(checkpoint_root: Path) -> list[int]:
    steps = []
    if not checkpoint_root.is_dir():
        return steps
    for child in checkpoint_root.iterdir():
        match = STEP_PATTERN.fullmatch(child.name)
        if not match:
            continue
        try:
            validate_artifact(Artifact(child / "actor", "checkpoint"))
        except StateError:
            continue
        steps.append(int(match.group(1)))
    return sorted(steps)


def recover_tracker(checkpoint_root: Path) -> int | None:
    """Point verl's tracker at the newest structurally complete checkpoint."""
    steps = complete_steps(checkpoint_root)
    tracker = checkpoint_root / TRACKER
    if not steps:
        if tracker.exists():
            raise StateError(f"{tracker} exists but no complete checkpoint is recoverable")
        return None
    selected = steps[-1]
    current = None
    if tracker.is_file():
        try:
            current = int(tracker.read_text(encoding="utf-8").strip())
        except ValueError:
            current = None
    if current == selected:
        return selected
    checkpoint_root.mkdir(parents=True, exist_ok=True)
    temporary = tracker.with_name(f".{tracker.name}.tmp-{os.getpid()}")
    temporary.write_text(f"{selected}\n", encoding="utf-8")
    os.replace(temporary, tracker)
    print(f"rewound verl checkpoint tracker from {current!r} to complete step {selected}")
    return selected
