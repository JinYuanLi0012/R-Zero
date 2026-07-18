#!/usr/bin/env python3
"""Population manifests and strict generation-budget verification."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
from pathlib import Path

from population_spec import allocate_quotas, make_expert_specs


def software_versions() -> dict[str, str]:
    versions = {"python": platform.python_version()}
    for package in ("torch", "vllm", "transformers", "ray", "verl"):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = "not-installed"
    try:
        versions["rzero_git_commit"] = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        versions["rzero_git_commit"] = "unknown"
    return versions


def checkpoint_identity(value: str) -> dict[str, object]:
    path = Path(value).expanduser()
    digest = hashlib.sha256()
    files = []
    if path.exists():
        candidates = [path] if path.is_file() else sorted(
            item for item in path.rglob("*")
            if item.is_file()
            and (item.name.endswith((".safetensors", ".bin")) or item.name in {
                "config.json", "model.safetensors.index.json", "pytorch_model.bin.index.json"
            })
        )
        for item in candidates:
            relative = item.name if path.is_file() else str(item.relative_to(path))
            file_hash = hashlib.sha256()
            with item.open("rb") as handle:
                for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
                    file_hash.update(chunk)
            hexdigest = file_hash.hexdigest()
            digest.update(relative.encode())
            digest.update(hexdigest.encode())
            files.append({"path": relative, "size": item.stat().st_size, "sha256": hexdigest})
        source_type = "local"
    else:
        digest.update(f"hub-or-unresolved:{value}".encode())
        source_type = "hub_or_unresolved"
    return {"source": value, "source_type": source_type, "identity_sha256": digest.hexdigest(), "files": files}


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.tmp-{os.getpid()}")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def population_manifest(args: argparse.Namespace) -> None:
    specs = make_expert_specs(
        role=args.role,
        round_index=args.round_index,
        population_size=args.population_size,
        sigma=args.sigma,
        global_seed=args.global_seed,
    )
    gpu_ids = [value.strip() for value in args.gpu_ids.split(",") if value.strip()]
    num_workers = min(len(gpu_ids), args.population_size)
    atomic_json(
        args.output,
        {
            "center": checkpoint_identity(args.center),
            "role": args.role,
            "round": args.round_index,
            "population_size": args.population_size,
            "sigma": args.sigma,
            "global_seed": args.global_seed,
            "samples_per_question": args.samples,
            "tensor_parallel_size": 1,
            "physical_gpu_ids": gpu_ids[:num_workers],
            "expert_gpu_assignment": {
                str(spec.expert_index): gpu_ids[spec.expert_index % num_workers]
                for spec in specs
            },
            "experts": [spec.to_dict() for spec in specs],
            "expert_checkpoints_persisted": False,
            "software_versions": software_versions(),
        },
    )


def verify_generation(args: argparse.Namespace) -> None:
    quotas = allocate_quotas(args.total_budget, args.population_size)
    observed = {index: 0 for index in range(args.population_size)}
    shard_manifests = []
    for shard in range(args.num_shards):
        path = args.generated_dir / f"{args.save_name}_{shard}_generation_manifest.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        shard_manifests.append(payload)
        for key, count in payload["expert_counts"].items():
            observed[int(key)] += int(count)
    expected = {index: quota for index, quota in enumerate(quotas)}
    if observed != expected:
        raise RuntimeError(f"generation quotas mismatch: observed={observed}, expected={expected}")
    gpu_ids = [value.strip() for value in args.gpu_ids.split(",") if value.strip()]
    atomic_json(
        args.output,
        {
            "questioner_population": checkpoint_identity(args.center),
            "round": args.round_index,
            "population_size": args.population_size,
            "sigma": args.sigma,
            "global_seed": args.global_seed,
            "total_budget": args.total_budget,
            "expected_quotas": expected,
            "observed_quotas": observed,
            "generated_count": sum(observed.values()),
            "num_physical_shards": args.num_shards,
            "physical_gpu_ids": gpu_ids[: args.num_shards],
            "expert_gpu_assignment": {
                str(index): gpu_ids[index % args.num_shards]
                for index in range(args.population_size)
            },
            "shards": shard_manifests,
            "expert_checkpoints_persisted": False,
            "software_versions": software_versions(),
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    population = commands.add_parser("population")
    population.add_argument("--center", required=True)
    population.add_argument("--role", choices=["questioner", "solver"], required=True)
    population.add_argument("--round-index", type=int, required=True)
    population.add_argument("--population-size", type=int, required=True)
    population.add_argument("--sigma", type=float, required=True)
    population.add_argument("--global-seed", type=int, required=True)
    population.add_argument("--samples", type=int, required=True)
    population.add_argument("--gpu-ids", required=True)
    population.add_argument("--output", type=Path, required=True)
    generation = commands.add_parser("verify-generation")
    generation.add_argument("--center", required=True)
    generation.add_argument("--round-index", type=int, required=True)
    generation.add_argument("--population-size", type=int, required=True)
    generation.add_argument("--sigma", type=float, required=True)
    generation.add_argument("--global-seed", type=int, required=True)
    generation.add_argument("--total-budget", type=int, required=True)
    generation.add_argument("--num-shards", type=int, required=True)
    generation.add_argument("--generated-dir", type=Path, required=True)
    generation.add_argument("--save-name", required=True)
    generation.add_argument("--gpu-ids", required=True)
    generation.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    population_manifest(args) if args.command == "population" else verify_generation(args)


if __name__ == "__main__":
    main()
