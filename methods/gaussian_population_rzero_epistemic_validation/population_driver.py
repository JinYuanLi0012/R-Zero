#!/usr/bin/env python3
"""Run one TP=1 population worker per GPU and validate the produced shards."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "gaussian_population_rzero"))
from population_spec import assign_experts, make_expert_specs  # noqa: E402
from manifests import checkpoint_identity, software_versions  # noqa: E402

from common import atomic_json, read_jsonl, sigma_key, software_manifest  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--round-index", type=int, required=True)
    parser.add_argument("--sigmas", required=True)
    parser.add_argument("--gpu-ids", required=True)
    parser.add_argument("--population-size", type=int, required=True)
    parser.add_argument("--global-seed", type=int, required=True)
    parser.add_argument("--samples", type=int, required=True)
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--top-p", type=float, default=1.0)
    parser.add_argument("--top-k", type=int, default=40)
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.8)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    gpu_ids = [value.strip() for value in args.gpu_ids.split(",") if value.strip()]
    sigmas = [float(value) for value in args.sigmas.split(",") if value.strip()]
    if not gpu_ids or len(gpu_ids) > args.population_size:
        raise ValueError("GPU count must be between one and population size")
    processes = []
    assignments = {}
    for worker_index, gpu_id in enumerate(gpu_ids):
        experts = assign_experts(args.population_size, worker_index, len(gpu_ids))
        assignments[worker_index] = experts
        command = [
            sys.executable, str(HERE / "population_worker.py"),
            "--model", args.model, "--input", str(args.input),
            "--output-dir", str(args.output_dir), "--round-index", str(args.round_index),
            "--worker-index", str(worker_index), "--expert-indices", ",".join(map(str, experts)),
            "--sigmas", args.sigmas, "--population-size", str(args.population_size),
            "--global-seed", str(args.global_seed), "--samples", str(args.samples),
            "--max-tokens", str(args.max_tokens), "--batch-size", str(args.batch_size),
            "--temperature", str(args.temperature), "--top-p", str(args.top_p),
            "--top-k", str(args.top_k), "--gpu-memory-utilization", str(args.gpu_memory_utilization),
        ]
        if args.resume:
            command.append("--resume")
        environment = dict(os.environ)
        environment["CUDA_VISIBLE_DEVICES"] = gpu_id
        processes.append((worker_index, subprocess.Popen(command, env=environment)))
    statuses = [(index, process.wait()) for index, process in processes]
    failures = [(index, status) for index, status in statuses if status != 0]
    if failures:
        raise RuntimeError(f"population workers failed: {failures}")

    question_count = len(read_jsonl(args.input))
    for sigma in sigmas:
        for experts in assignments.values():
            for expert_index in experts:
                path = args.output_dir / f"sigma_{sigma_key(sigma)}" / f"expert_{expert_index}.parquet"
                expected = question_count * args.samples
                if not path.is_file() or pq.read_metadata(path).num_rows != expected:
                    raise RuntimeError(f"incomplete expert output: {path}; expected {expected} rows")
    atomic_json(
        args.output_dir / "generation_manifest.json",
        {
            "model": checkpoint_identity(args.model),
            "input": str(args.input),
            "round_index": args.round_index,
            "sigmas": sigmas,
            "population_size": args.population_size,
            "samples_per_expert": args.samples,
            "population_seed": args.global_seed,
            "gpu_ids": gpu_ids,
            "assignments": assignments,
            "experts_by_sigma": {
                str(sigma): [
                    spec.to_dict() for spec in make_expert_specs(
                        role="solver", round_index=args.round_index,
                        population_size=args.population_size, sigma=sigma,
                        global_seed=args.global_seed,
                    )
                ]
                for sigma in sigmas
            },
            "generation": {
                "temperature": args.temperature, "top_p": args.top_p, "top_k": args.top_k,
                "max_tokens": args.max_tokens, "batch_size": args.batch_size,
                "tensor_parallel_size": 1,
            },
            "software": {**software_manifest(), **software_versions()},
        },
    )


if __name__ == "__main__":
    main()
