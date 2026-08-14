#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import math
import os
import platform
import subprocess
from pathlib import Path
from typing import Any, Iterable


INVALID_CLASS = "__INVALID_BOXED_ANSWER__"


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.tmp-{os.getpid()}")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.tmp-{os.getpid()}")
    with temporary.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    os.replace(temporary, path)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def question_hash(question: str) -> str:
    return hashlib.sha256(str(question).encode("utf-8")).hexdigest()


def stable_int(*parts: object) -> int:
    payload = "\0".join(str(part) for part in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def sigma_key(sigma: float) -> str:
    if sigma == 0:
        return "0"
    return f"{sigma:.12g}".replace("-", "m").replace(".", "p")


def parse_sigmas(value: str) -> list[float]:
    values = [float(item.strip()) for item in value.split(",") if item.strip()]
    if not values or any(not math.isfinite(item) or item < 0 for item in values):
        raise ValueError("sigma list must contain finite non-negative values")
    if len(set(values)) != len(values):
        raise ValueError("sigma list contains duplicates")
    return values


def software_manifest() -> dict[str, str]:
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        commit = "unknown"
    result = {"python": platform.python_version(), "git_commit": commit}
    for package in ("datasets", "pyarrow", "torch", "vllm", "transformers", "openai", "scipy"):
        try:
            result[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            result[package] = "not-installed"
    return result


def entropy_from_counts(counts: Iterable[int]) -> float:
    values = [int(value) for value in counts if int(value) > 0]
    total = sum(values)
    if total == 0:
        return 0.0
    return -sum((value / total) * math.log(value / total) for value in values)


def clip_mutual_information(value: float, tolerance: float = 1e-12) -> float:
    if value < -tolerance:
        raise ValueError(f"mutual information is unexpectedly negative: {value}")
    return max(0.0, value)
