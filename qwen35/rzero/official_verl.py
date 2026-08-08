"""Resolve and verify the official verl source tree used by this migration."""

from __future__ import annotations

import os
from pathlib import Path


DEFAULT_VERL_ROOT = Path("/opt/verl")


def verl_source_root(configured: str | Path | None = None) -> Path:
    value = os.environ.get("VERL_SOURCE_ROOT") or configured or DEFAULT_VERL_ROOT
    return Path(value).expanduser().resolve()


def build_pythonpath(verl_root: Path, repo_root: Path, inherited: str | None = None) -> str:
    """Put official verl first and retain the repository for qwen35 rewards."""
    ordered = [str(verl_root.resolve()), str(repo_root.resolve())]
    for entry in (inherited or "").split(os.pathsep):
        if entry and entry not in ordered:
            ordered.append(entry)
    return os.pathsep.join(ordered)


def assert_official_verl(module_file: str | Path, expected_root: Path) -> Path:
    resolved = Path(module_file).resolve()
    root = expected_root.resolve()
    if not resolved.is_relative_to(root):
        raise RuntimeError(f"verl resolved outside official source root: {resolved} (expected under {root})")
    return resolved
