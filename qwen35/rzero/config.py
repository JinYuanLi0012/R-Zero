"""Configuration loading and invariant checks.

The checked-in .yaml is deliberately JSON-compatible YAML so dry-run and unit
tests need no third-party YAML parser. JSON is a strict subset of YAML.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ConfigError(ValueError):
    """Raised when a formal-run invariant is violated."""


def load_config(path: str | Path) -> dict[str, Any]:
    config_path = Path(path).expanduser().resolve()
    with config_path.open(encoding="utf-8") as handle:
        config = json.load(handle)
    validate_config(config)
    config["_config_path"] = str(config_path)
    return config


def validate_config(config: dict[str, Any]) -> None:
    required = {"model", "runtime", "hardware", "algorithm", "data", "generation", "checkpoint"}
    missing = required - config.keys()
    if missing:
        raise ConfigError(f"missing config sections: {sorted(missing)}")

    model = config["model"]
    if model.get("id") != "Qwen/Qwen3.5-4B-Base":
        raise ConfigError("formal profile must use Qwen/Qwen3.5-4B-Base")
    revision = str(model.get("revision", ""))
    if not revision or revision in {"main", "latest"}:
        raise ConfigError("model.revision must be immutable")
    if not model.get("language_model_only"):
        raise ConfigError("Qwen3.5 must use the text-only serving path")

    runtime = config["runtime"]
    expected_runtime = {
        "cuda": "13.0.2",
        "torch": "2.11.0",
        "vllm": "0.24.0",
        "transformers": "5.5.3",
        "verl_ref": "4a2cba76f7f605d2b9f56e640faaeaa71c2c7f71",
        "base_image": "verlai/verl:vllm024.dev2",
        "base_image_digest": "sha256:b867883b0dd011363e69ab2ab344922a28c5bd0409e2a324e3ee70fb27ca7543",
        "training_backend": "fsdp2",
        "rollout_backend": "vllm",
    }
    runtime_mismatches = {
        key: (runtime.get(key), value) for key, value in expected_runtime.items() if runtime.get(key) != value
    }
    if runtime_mismatches:
        raise ConfigError(f"formal runtime profile changed: {runtime_mismatches}")
    if runtime.get("verl_source_root") != "/opt/verl":
        raise ConfigError("official verl source root must be /opt/verl")

    hardware = config["hardware"]
    if hardware.get("gpus") != [0, 1, 2, 3]:
        raise ConfigError("formal profile requires four GPUs numbered 0..3")
    if set(hardware["questioner_training_gpus"]) & set(hardware["questioner_solver_gpus"]):
        raise ConfigError("questioner training and frozen Solver GPUs must be disjoint")

    algorithm = config["algorithm"]
    if config.get("profile", "formal") != "formal":
        return
    expected = {
        "rounds": 5,
        "questioner_steps": 5,
        "solver_steps": 15,
        "questioner_rollouts": 4,
        "solver_rollouts": 5,
        "questioner_prompt_batch_size": 512,
        "solver_prompt_batch_size": 512,
        "questioner_update_batch_size": 16,
        "solver_update_batch_size": 128,
        "questioner_solver_samples": 10,
        "candidate_vote_samples": 9,
        "difficulty_min": 0.3,
        "difficulty_max": 0.8,
    }
    mismatches = {key: (algorithm.get(key), value) for key, value in expected.items() if algorithm.get(key) != value}
    if mismatches:
        raise ConfigError(f"released-code profile changed: {mismatches}")

    generation = config["generation"]
    total = generation.get("shards", 0) * generation.get("samples_per_shard", 0)
    if total != 8000:
        raise ConfigError(f"formal candidate count must be 8000, got {total}")
    if config["checkpoint"].get("save_freq") != 1 or config["checkpoint"].get("keep") != 2:
        raise ConfigError("checkpoint policy must save every step and retain two")
