#!/usr/bin/env python3
"""Strict acceptance checks over persisted experiment artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path

import pyarrow.parquet as pq

from common import parse_sigmas, read_jsonl, sigma_key


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--population-size", type=int, default=8)
    parser.add_argument("--samples", type=int, default=8)
    parser.add_argument("--sigmas", default="0,0.0001,0.0003,0.001,0.003")
    args = parser.parse_args()
    if args.population_size != 8 or args.samples != 8:
        raise RuntimeError("formal validation requires M=8 and K=8")
    prepared = read_jsonl(args.run_root / "prepared" / "all_samples.jsonl")
    ids = [row["question_id"] for row in prepared]
    if len(ids) != 600 or len(set(ids)) != 600:
        raise RuntimeError("prepared sample must contain exactly 600 unique row IDs")
    sigmas = parse_sigmas(args.sigmas)
    if sigmas != [0.0, 0.0001, 0.0003, 0.001, 0.003]:
        raise RuntimeError("acceptance requires the five preregistered sigma values")
    expected = args.population_size * args.samples
    observed_completion_total = 0
    for round_index in (1, 2, 3):
        reference_seeds = None
        for sigma in sigmas:
            key = sigma_key(sigma)
            raw_dir = args.run_root / "scores" / f"v{round_index}" / "raw" / f"sigma_{key}"
            raw = []
            paths = sorted(raw_dir.glob("expert_*.parquet"))
            if len(paths) != args.population_size:
                raise RuntimeError(f"expected one atomic shard per expert in {raw_dir}")
            for path in paths:
                raw.extend(pq.read_table(path).to_pylist())
            observed_completion_total += len(raw)
            counts = {}
            seeds = {}
            for row in raw:
                counts[row["question_id"]] = counts.get(row["question_id"], 0) + 1
                seeds.setdefault(row["expert_index"], set()).add(
                    (row["expert_seed"], row["sampling_seed"])
                )
            if len(counts) != 200 or any(value != expected for value in counts.values()):
                raise RuntimeError(f"V{round_index} sigma {sigma} is not a complete 64-response grid")
            if any(len(values) != 1 for values in seeds.values()):
                raise RuntimeError("expert seed changed within a round")
            resolved_seeds = {index: next(iter(values)) for index, values in seeds.items()}
            if reference_seeds is None:
                reference_seeds = resolved_seeds
            elif resolved_seeds != reference_seeds:
                raise RuntimeError("expert or sampling seeds changed across sigma values")
            summary = pq.read_table(
                args.run_root / "scores" / f"v{round_index}" / "summary" / f"sigma_{key}.parquet"
            ).to_pylist()
            if any(row["h_total"] + 1e-12 < row["h_within"] for row in summary):
                raise RuntimeError("H_total is below H_within beyond tolerance")
    judge = read_jsonl(args.run_root / "judge" / "judge_results.jsonl")
    if len(judge) != 600 or any(not row.get("label") for row in judge):
        raise RuntimeError("single-pass Judge results are incomplete")
    expected_total = 600 * len(sigmas) * args.population_size * args.samples
    if observed_completion_total != expected_total:
        raise RuntimeError(
            f"expected {expected_total} formal completions, found {observed_completion_total}"
        )
    print("acceptance checks passed")


if __name__ == "__main__":
    main()
