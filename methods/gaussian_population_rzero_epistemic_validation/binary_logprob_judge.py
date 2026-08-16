#!/usr/bin/env python3
"""Launch sharded binary few-shot logprob judging and join atomic artifacts."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from binary_logprob_common import (
    EXPERIMENT_VERSION, INVALID_CANDIDATE, VALID_CANDIDATE, VARIANTS, prompt_hash,
)
from common import atomic_json, read_jsonl, sha256_file, software_manifest, stable_int, write_jsonl


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model", default="Qwen/Qwen3-4B-Base")
    parser.add_argument("--gpu-ids", default="0,1,2,3")
    parser.add_argument("--expected-count", type=int, default=600)
    parser.add_argument("--max-analysis-tokens", type=int, default=1024)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.8)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = arguments()
    source = read_jsonl(args.input)
    if len(source) != args.expected_count or len({r["question_id"] for r in source}) != len(source):
        raise RuntimeError("input does not have the expected unique question coverage")
    gpu_ids = [item.strip() for item in args.gpu_ids.split(",") if item.strip()]
    if not gpu_ids:
        raise ValueError("at least one GPU ID is required")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = args.output_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    blind, mapping = [], []
    for row in source:
        opaque = f"l_{stable_int(args.seed, EXPERIMENT_VERSION, row['question_id']):016x}"
        blind.append({"opaque_binary_judge_id": opaque, "question": str(row["question"])})
        mapping.append(
            {
                "opaque_binary_judge_id": opaque, "question_id": row["question_id"],
                "round": int(row["round"]), "question": str(row["question"]),
            }
        )
    if len({row["opaque_binary_judge_id"] for row in mapping}) != len(mapping):
        raise RuntimeError("opaque binary Judge IDs collided")
    blind_path = args.output_dir / "blind_input.jsonl"
    write_jsonl(blind_path, blind)
    write_jsonl(args.output_dir / "private_mapping.jsonl", mapping)

    worker = Path(__file__).with_name("binary_logprob_worker.py")
    processes = []
    for shard_index, gpu_id in enumerate(gpu_ids):
        command = [
            sys.executable, str(worker), "--model", args.model, "--input", str(blind_path),
            "--output-dir", str(raw_dir), "--shard-index", str(shard_index),
            "--num-shards", str(len(gpu_ids)), "--max-analysis-tokens",
            str(args.max_analysis_tokens), "--batch-size", str(args.batch_size),
            "--gpu-memory-utilization", str(args.gpu_memory_utilization), "--seed", str(args.seed),
        ]
        if args.resume:
            command.append("--resume")
        environment = os.environ.copy()
        environment["CUDA_VISIBLE_DEVICES"] = gpu_id
        processes.append((gpu_id, subprocess.Popen(command, env=environment)))
    statuses = [(gpu, process.wait()) for gpu, process in processes]
    failures = [(gpu, status) for gpu, status in statuses if status != 0]
    if failures:
        raise RuntimeError(f"binary logprob Judge workers failed: {failures}")

    results = []
    for item in mapping:
        for variant in VARIANTS:
            artifact_path = raw_dir / variant / f"{item['opaque_binary_judge_id']}.json"
            if not artifact_path.is_file():
                raise RuntimeError(f"missing worker artifact: {artifact_path}")
            artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
            results.append({**item, **artifact})
    write_jsonl(args.output_dir / "binary_logprob_results.jsonl", results)
    atomic_json(
        args.output_dir / "binary_logprob_manifest.json",
        {
            "experiment_version": EXPERIMENT_VERSION, "model": args.model,
            "input": str(args.input), "input_sha256": sha256_file(args.input),
            "question_count": len(source), "result_count": len(results),
            "variants": list(VARIANTS), "prompt_sha256": {v: prompt_hash(v) for v in VARIANTS},
            "generation": {"temperature": 0.0, "top_p": 1.0,
                           "max_analysis_tokens": args.max_analysis_tokens,
                           "analysis_completions_per_question": len(VARIANTS)},
            "scoring": {"method": "sum of candidate prompt-token logprobs",
                        "valid_candidate": VALID_CANDIDATE,
                        "invalid_candidate": INVALID_CANDIDATE,
                        "probability": "two-candidate softmax"},
            "gpu_ids": gpu_ids, "num_shards": len(gpu_ids), "seed": args.seed,
            "blind_input_fields": ["opaque_binary_judge_id", "question"],
            "software": software_manifest(),
        },
    )


if __name__ == "__main__":
    main()
