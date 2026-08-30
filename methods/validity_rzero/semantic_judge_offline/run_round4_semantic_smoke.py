#!/usr/bin/env python3
"""Run the fixed Round-4 2048x128 semantic-MC feasibility smoke."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
from typing import Any, Callable

if __package__ in {None, ""}:  # Support the documented direct-script command.
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from methods.validity_rzero.semantic_judge_offline.run_pair_judge import (
    atomic_json, atomic_jsonl, git_head, sha256_bytes, sha256_file,
)
from methods.validity_rzero.semantic_judge_offline.run_pair_judge_v2 import (
    PROMPT_TEMPLATE, build_prompt,
)
from methods.validity_rzero.semantic_judge_offline.run_pair_judge_v3_vllm import (
    PROMPT_VERSION, load_generation_config, sampling_options,
)
from methods.validity_rzero.semantic_mc import (
    aggregate_semantic_penalties, build_pair_plan, cache_context,
    sample_candidate_and_panel_indices,
)
from methods.validity_rzero.semantic_mc_gpu import run_gpu_tasks


DEFAULT_INPUT = Path(
    "/engrfs/project/jiaxinh/jinyuan/R-zero-storage/rzero_runs/"
    "qwen3_4b_validity_rzero_clean_formal_r10_initstep15_divlambda5_v1/"
    "datasets/round_4_phase_b.jsonl"
)


def arguments(description: str | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=description or __doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model", default="Qwen/Qwen3-4B-Base")
    parser.add_argument("--expected-count", type=int, default=7440)
    parser.add_argument("--candidate-count", type=int, default=2048)
    parser.add_argument("--panel-count", type=int, default=128)
    parser.add_argument("--candidate-seed", type=int, default=42)
    parser.add_argument("--panel-seed", type=int, default=43)
    parser.add_argument("--sampling-seed", type=int, default=42)
    parser.add_argument("--max-tokens", type=int, default=1024)
    parser.add_argument("--gpu-ids", default="2,3")
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.85)
    parser.add_argument("--worker-batch-size", type=int, default=512)
    parser.add_argument("--local-files-only", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def read_rows(path: Path, expected_count: int) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    if len(rows) != expected_count:
        raise ValueError(f"expected {expected_count} input rows, found {len(rows)}")
    missing = [index for index, row in enumerate(rows) if not str(row.get("question", "")).strip()]
    if missing:
        raise ValueError(f"input rows missing question: first indices {missing[:10]}")
    return rows


def load_cache(path: Path) -> dict[str, dict]:
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8") as handle:
        return {
            row["cache_key"]: row
            for row in (json.loads(line) for line in handle if line.strip())
            if row.get("parsed_label") in {"SAME_TYPE", "DIFFERENT"}
        }


def percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower, upper = math.floor(position), math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] * (upper - position) + ordered[upper] * (position - lower)


def excerpt(text: str, limit: int = 180) -> str:
    compact = " ".join(text.split())
    return compact if len(compact) <= limit else compact[: limit - 1] + "…"


def example_rows(candidate_indices, instances, judgments, aggregates, questions, label, limit=3):
    by_candidate: dict[int, list] = {index: [] for index in candidate_indices}
    for instance in instances:
        if judgments.get(instance.cache_key, {}).get("parsed_label") == label:
            by_candidate[instance.candidate_index].append(instance)
    def repetition_priority(index):
        text = questions[index].lower().replace(" ", "")
        preferred = (
            ("x^y" in text and "y^x" in text and "100" in text),
            ("recurrence" in text or "递推" in text or "a_{n" in text),
            ("perfectsquare" in text or "perfect-square" in text or "完全平方" in text),
            ("extrema" in text or "maximum" in text or "minimum" in text or
             "divisib" in text or "整除" in text),
        )
        return next((len(preferred) - position for position, hit in enumerate(preferred) if hit), 0)

    if label == "SAME_TYPE":
        ordered = sorted(
            candidate_indices,
            key=lambda index: (
                repetition_priority(index),
                float(aggregates[index]["semantic_penalty"]),
                -index,
            ),
            reverse=True,
        )
    else:
        ordered = sorted(
            candidate_indices,
            key=lambda index: (float(aggregates[index]["semantic_penalty"]), index),
        )
    output = []
    seen_questions = set()
    for index in ordered:
        if not by_candidate[index] or questions[index] in seen_questions:
            continue
        reference = by_candidate[index][0].panel_index
        output.append({
            "row_index": index,
            "question": questions[index],
            "reference_row_index": reference,
            "reference_question": questions[reference],
            "semantic_penalty": aggregates[index]["semantic_penalty"],
        })
        seen_questions.add(questions[index])
        if len(output) == limit:
            break
    return output


def write_report(
    path: Path,
    feasibility: dict,
    reward: dict,
    families: list[dict],
    distinct: list[dict],
    *,
    title: str = "Round-4 semantic Monte Carlo smoke",
) -> None:
    lines = [
        f"# {title}", "",
        "## A. Feasibility / integrity", "",
        f"- Total pair instances: {feasibility['total_pair_instances']:,}",
        f"- Unique exact pairs: {feasibility['unique_pairs']:,}",
        f"- Exact-pair cache hits: {feasibility['cache_hits']:,}",
        f"- vLLM worker wall time: {feasibility['vllm_wall_seconds']:.2f} s",
        f"- Unique inference pairs/sec: {feasibility['unique_inference_pairs_per_second']:.3f}",
        f"- Parse success after retry: {feasibility['parse_success_after_retry']:.6%}",
        f"- Parse failure after retry: {feasibility['parse_failure_after_retry']:.6%}", "",
        "## B. Reward signal", "",
        f"- Semantic penalty mean: {reward['mean']:.6f}",
        f"- p50: {reward['p50']:.6f}",
        f"- p90: {reward['p90']:.6f}",
        f"- max: {reward['max']:.6f}", "",
        "### Repetition families observed in this sample", "",
    ]
    for item in families:
        lines.extend([
            f"- Row {item['row_index']} (penalty={item['semantic_penalty']:.6f}): {excerpt(item['question'])}",
            f"  - SAME_TYPE reference row {item['reference_row_index']}: {excerpt(item['reference_question'])}",
        ])
    lines.extend(["", "### Distinct questions observed in this sample", ""])
    for item in distinct:
        lines.extend([
            f"- Row {item['row_index']} (penalty={item['semantic_penalty']:.6f}): {excerpt(item['question'])}",
            f"  - DIFFERENT reference row {item['reference_row_index']}: {excerpt(item['reference_question'])}",
        ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_smoke(
    args: argparse.Namespace,
    *,
    prompt_version: str = PROMPT_VERSION,
    prompt_template: str = PROMPT_TEMPLATE,
    prompt_builder: Callable[[str, str], str] = build_prompt,
    artifact_stem: str = "semantic_smoke",
    experiment: str = "round4_semantic_mc_smoke_2048x128_v1",
    controlled_baseline: str | None = None,
    only_intended_variable: str | None = None,
    report_title: str = "Round-4 semantic Monte Carlo smoke",
) -> None:
    manifest_path = args.output_dir / f"{artifact_stem}_manifest.json"
    per_question_path = args.output_dir / f"{artifact_stem}_per_question.jsonl"
    report_path = args.output_dir / f"{artifact_stem}_report.md"
    cache_path = args.output_dir / f"{artifact_stem}_cache.jsonl"
    if not args.overwrite and any(path.exists() for path in (manifest_path, per_question_path, report_path)):
        raise FileExistsError("semantic smoke output exists; use a new directory or --overwrite")
    rows = read_rows(args.input, args.expected_count)
    candidate_indices, panel_indices = sample_candidate_and_panel_indices(
        len(rows), args.candidate_count, args.panel_count, args.candidate_seed, args.panel_seed
    )
    questions = {index: str(row["question"]) for index, row in enumerate(rows)}
    generation_config, generation_config_path, resolved_model_path, resolved_revision = (
        load_generation_config(args.model, None, args.local_files_only)
    )
    context = cache_context(
        resolved_model_path,
        args.max_tokens,
        args.sampling_seed,
        prompt_version=prompt_version,
        prompt_template=prompt_template,
    )
    instances, tasks = build_pair_plan(
        questions,
        candidate_indices,
        panel_indices,
        context,
        prompt_builder=prompt_builder,
    )
    expected_pairs = args.candidate_count * args.panel_count - args.panel_count
    if len(instances) != expected_pairs:
        raise RuntimeError(f"pair-instance invariant failed: {len(instances)} vs {expected_pairs}")
    cached = load_cache(cache_path)
    judgments = {key: cached[key] for key in tasks.keys() & cached.keys()}
    missing_tasks = [task for key, task in sorted(tasks.items()) if key not in judgments]
    gpu_ids = [value.strip() for value in args.gpu_ids.split(",") if value.strip()]
    fresh, runtime = run_gpu_tasks(
        missing_tasks, resolved_model_path, gpu_ids, args.output_dir / "worker_state",
        max_tokens=args.max_tokens, seed=args.sampling_seed,
        gpu_memory_utilization=args.gpu_memory_utilization, batch_size=args.worker_batch_size,
    )
    judgments.update(fresh)
    atomic_jsonl(cache_path, (
        {"cache_key": key, **judgments[key]}
        for key in sorted(judgments)
        if judgments[key].get("parsed_label") in {"SAME_TYPE", "DIFFERENT"}
    ))
    warnings: list[str] = []
    aggregates = aggregate_semantic_penalties(
        candidate_indices, instances, judgments, warn=warnings.append
    )
    for warning in warnings:
        print(warning)
    output_rows = [
        {
            "row_index": index,
            "question": questions[index],
            **aggregates[index],
        }
        for index in candidate_indices
    ]
    atomic_jsonl(per_question_path, output_rows)
    compared_total = sum(int(item["compared_count"]) for item in aggregates.values())
    penalties = [float(item["semantic_penalty"]) for item in aggregates.values()]
    wall = float(runtime["wall_seconds"])
    feasibility = {
        "total_pair_instances": len(instances),
        "unique_pairs": len(tasks),
        "cache_hits": len(instances) - len(missing_tasks),
        "unique_inference_requests": len(missing_tasks),
        "vllm_wall_seconds": wall,
        "unique_inference_pairs_per_second": len(missing_tasks) / wall if wall else 0.0,
        "parse_success_after_retry": compared_total / len(instances),
        "parse_failure_after_retry": (len(instances) - compared_total) / len(instances),
        "parse_failure_instances_after_retry": len(instances) - compared_total,
    }
    reward = {
        "mean": sum(penalties) / len(penalties),
        "p50": percentile(penalties, 0.50),
        "p90": percentile(penalties, 0.90),
        "max": max(penalties),
    }
    families = example_rows(
        candidate_indices, instances, judgments, aggregates, questions, "SAME_TYPE"
    )
    distinct = example_rows(
        candidate_indices, instances, judgments, aggregates, questions, "DIFFERENT"
    )
    manifest = {
        "experiment": experiment,
        "evaluation_status": "round4_distribution_diagnostic_not_held_out_validation",
        "controlled_baseline": controlled_baseline,
        "only_intended_variable": only_intended_variable,
        "git_head": git_head(),
        "input_path": str(args.input.resolve()),
        "input_sha256": sha256_file(args.input),
        "input_row_count": len(rows),
        "sampled_row_indices": candidate_indices,
        "panel_row_indices": panel_indices,
        "candidate_seed": args.candidate_seed,
        "panel_seed": args.panel_seed,
        "sampling_seed": args.sampling_seed,
        "model_argument": args.model,
        "resolved_model_snapshot": resolved_model_path,
        "resolved_model_revision": resolved_revision,
        "generation_config_path": generation_config_path,
        "generation_config": generation_config,
        "prompt_version": prompt_version,
        "prompt_template": prompt_template,
        "prompt_sha256": sha256_bytes(prompt_template.encode("utf-8")),
        "sampling_config": sampling_options(args.max_tokens, args.sampling_seed),
        "gpu_ids": gpu_ids,
        "pair_protocol": {
            "panel_deduplicated": False,
            "self_skip_key": "same_sample_index_only",
            "different_index_identical_text_is_valid": True,
            "orientation": context["orientation"],
        },
        "feasibility": feasibility,
        "reward_signal": reward,
        "zero_denominator_warnings": warnings,
    }
    atomic_json(manifest_path, manifest)
    write_report(
        report_path,
        feasibility,
        reward,
        families,
        distinct,
        title=report_title,
    )
    print(json.dumps({"feasibility": feasibility, "reward_signal": reward}, indent=2))
    print(f"wrote {manifest_path}")
    print(f"wrote {per_question_path}")
    print(f"wrote {report_path}")


def main() -> None:
    run_smoke(arguments())


if __name__ == "__main__":
    main()
