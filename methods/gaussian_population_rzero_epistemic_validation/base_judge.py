#!/usr/bin/env python3
"""Prepare blind input, launch four Qwen Judge workers, and join their artifacts."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from common import atomic_json, read_jsonl, sha256_file, software_manifest, stable_int, write_jsonl


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model", default="Qwen/Qwen3-4B-Base")
    parser.add_argument("--gpu-ids", default="0,1,2,3")
    parser.add_argument("--expected-count", type=int, default=600)
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.8)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = arguments()
    source = read_jsonl(args.input)
    if len(source) != args.expected_count:
        raise RuntimeError(f"expected {args.expected_count} questions, found {len(source)}")
    question_ids = [row["question_id"] for row in source]
    if len(set(question_ids)) != len(question_ids):
        raise RuntimeError("question_id values are not unique")
    gpu_ids = [item.strip() for item in args.gpu_ids.split(",") if item.strip()]
    if not gpu_ids:
        raise ValueError("at least one GPU ID is required")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = args.output_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    mapping, blind = [], []
    for row in source:
        opaque = f"b_{stable_int(args.seed, 'base-judge', row['question_id']):016x}"
        blind.append({"opaque_base_judge_id": opaque, "question": str(row["question"])})
        mapping.append(
            {
                "opaque_base_judge_id": opaque, "question_id": row["question_id"],
                "round": int(row["round"]), "question": str(row["question"]),
            }
        )
    if len({row["opaque_base_judge_id"] for row in mapping}) != len(mapping):
        raise RuntimeError("opaque Base Judge IDs collided")
    blind_path = args.output_dir / "blind_input.jsonl"
    mapping_path = args.output_dir / "private_mapping.jsonl"
    write_jsonl(blind_path, blind)
    write_jsonl(mapping_path, mapping)

    worker = Path(__file__).with_name("base_judge_worker.py")
    processes = []
    for shard_index, gpu_id in enumerate(gpu_ids):
        command = [
            sys.executable, str(worker), "--model", args.model, "--input", str(blind_path),
            "--output-dir", str(raw_dir), "--shard-index", str(shard_index),
            "--num-shards", str(len(gpu_ids)), "--max-tokens", str(args.max_tokens),
            "--batch-size", str(args.batch_size), "--gpu-memory-utilization",
            str(args.gpu_memory_utilization), "--seed", str(args.seed),
        ]
        if args.resume:
            command.append("--resume")
        environment = os.environ.copy()
        environment["CUDA_VISIBLE_DEVICES"] = gpu_id
        processes.append((gpu_id, subprocess.Popen(command, env=environment)))
    statuses = [(gpu, process.wait()) for gpu, process in processes]
    failures = [(gpu, status) for gpu, status in statuses if status != 0]
    if failures:
        raise RuntimeError(f"Base Judge GPU workers failed: {failures}")

    results = []
    for item in mapping:
        artifact_path = raw_dir / f"{item['opaque_base_judge_id']}.json"
        if not artifact_path.is_file():
            raise RuntimeError(f"missing worker artifact: {artifact_path}")
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        judgment = artifact.get("judgment")
        results.append(
            {
                **item, "status": artifact["status"], "model": artifact["model"],
                "raw_completion": artifact["attempts"][-1]["raw_completion"],
                "attempts": artifact["attempts"], "failure_reason": artifact.get("failure_reason"),
                "judgment": judgment, "label": judgment.get("label") if judgment else None,
                "probability_label_A": judgment.get("probability_label_A") if judgment else None,
                "valid": judgment.get("label") == "A" if judgment else None,
            }
        )
    write_jsonl(args.output_dir / "base_judge_results.jsonl", results)
    atomic_json(
        args.output_dir / "base_judge_manifest.json",
        {
            "model": args.model, "input": str(args.input), "input_sha256": sha256_file(args.input),
            "question_count": len(source), "successful_count": sum(r["status"] == "success" for r in results),
            "final_parse_failure_count": sum(r["status"] == "final_parse_failure" for r in results),
            "generation": {"temperature": 0.0, "top_p": 1.0, "max_tokens": args.max_tokens,
                           "samples_per_question": 1, "deterministic_retries": 1},
            "gpu_ids": gpu_ids, "num_shards": len(gpu_ids), "seed": args.seed,
            "blind_input_fields": ["opaque_base_judge_id", "question"], "software": software_manifest(),
        },
    )


if __name__ == "__main__":
    main()
