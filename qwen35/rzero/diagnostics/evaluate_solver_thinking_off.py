"""Strict single-variable Solver thinking-off A/B for fixed Questioner candidates."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Callable

from qwen35.rzero.curate_dataset import filter_candidates
from qwen35.rzero.diagnostics.base_questioner import validate_rendered_prompt
from qwen35.rzero.generate_candidates import atomic_json
from qwen35.rzero.pipeline.state import file_hash
from qwen35.rzero.prompts import solver_messages
from qwen35.rzero.rewards.common import majority_vote


def _json_scalar(value: Any) -> str | int | float | bool | None:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def score_responses(
    candidates: list[dict[str, Any]],
    responses: list[Any],
    extract_answer: Callable[[str], str],
    grader: Callable[[str, str], bool],
    max_tokens: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Apply the released extraction, majority-vote and filtering semantics."""

    if len(candidates) != len(responses):
        raise RuntimeError("candidate and response counts differ")
    evidence = []
    scored = []
    for candidate_index, (source_item, response) in enumerate(zip(candidates, responses)):
        rollouts = []
        answers = []
        for rollout_index, output in enumerate(response.outputs):
            extracted = extract_answer(output.text)
            answers.append(extracted)
            finish_reason = str(output.finish_reason) if output.finish_reason is not None else None
            token_count = len(output.token_ids)
            rollouts.append(
                {
                    "rollout_index": rollout_index,
                    "raw_response": output.text,
                    "finish_reason": finish_reason,
                    "stop_reason": _json_scalar(output.stop_reason),
                    "token_count": token_count,
                    "hit_max_tokens": finish_reason == "length" or token_count >= max_tokens,
                    "extracted_answer": extracted,
                }
            )

        majority, count, extracted = majority_vote(answers, grader)
        question = source_item["question"]
        if not extracted:
            disposition = "dropped_no_nonempty_extraction"
        elif "证明" in question or "box" in question.lower() or "text" in majority.lower():
            disposition = "dropped_released_filter"
        else:
            disposition = "scored"
            scored.append(
                {
                    "question": question,
                    "answer": majority,
                    "score": count / len(extracted),
                    "results": extracted,
                }
            )
        evidence.append(
            {
                "candidate_index": candidate_index,
                "question": question,
                "questioner_answer": source_item.get("answer", ""),
                "majority_answer": majority,
                "majority_count": count,
                "results": extracted,
                "result_count": len(extracted),
                "disposition": disposition,
                "rollouts": rollouts,
            }
        )
    return evidence, scored


def build_summary(
    all_candidates: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    scored: list[dict[str, Any]],
    provenance: dict[str, Any],
    minimum: float,
    maximum: float,
    max_tokens: int,
) -> dict[str, Any]:
    rollouts = [rollout for item in evidence for rollout in item["rollouts"]]
    accepted, accepted_count, _ = filter_candidates(
        scored,
        minimum,
        maximum,
        deduplicate_questions=False,
    )
    finish_reasons = Counter(str(item["finish_reason"]) for item in rollouts)
    stop_reasons = Counter(str(item["stop_reason"]) for item in rollouts)
    score_histogram = Counter(round(float(item["score"]), 6) for item in scored)
    result_lengths = Counter(len(item.get("results") or []) for item in scored)
    valid_boxed = sum(item["extracted_answer"] not in {"", "None"} for item in rollouts)
    return {
        "provenance": provenance,
        "total_candidates": len(all_candidates),
        "parseable_candidates": len(evidence),
        "scored_candidates": len(scored),
        "dropped_during_evaluation": len(evidence) - len(scored),
        "total_solver_rollouts": len(rollouts),
        "max_tokens": max_tokens,
        "finish_reasons": dict(sorted(finish_reasons.items())),
        "stop_reasons": dict(sorted(stop_reasons.items())),
        "hit_max_tokens": sum(item["hit_max_tokens"] for item in rollouts),
        "valid_boxed_answers": valid_boxed,
        "valid_boxed_answer_fraction": valid_boxed / len(rollouts) if rollouts else 0.0,
        "missing_box_none_answers": sum(item["extracted_answer"] == "None" for item in rollouts),
        "explicit_empty_box_answers": sum(item["extracted_answer"] == "" for item in rollouts),
        "majority_none": sum(item.get("answer") == "None" for item in scored),
        "difficulty_min": minimum,
        "difficulty_max": maximum,
        "accepted_0.3_to_0.8": accepted_count,
        "accepted_fraction_of_scored": accepted_count / len(scored) if scored else 0.0,
        "accepted_fraction_of_total": accepted_count / len(all_candidates) if all_candidates else 0.0,
        "accepted_questions": [item["question"] for item in accepted],
        "difficulty_histogram": {str(key): value for key, value in sorted(score_histogram.items())},
        "result_lengths": {str(key): value for key, value in sorted(result_lengths.items())},
        "dispositions": dict(sorted(Counter(item["disposition"] for item in evidence).items())),
        "semantics": {
            "deduplication": False,
            "repeat_to_minimum": False,
            "fallback": False,
            "parquet_created": False,
        },
    }


def _existing_complete(
    summary_path: Path,
    evidence_path: Path,
    scored_path: Path,
    expected_provenance: dict[str, Any],
) -> bool:
    if not all(path.is_file() and path.stat().st_size for path in (summary_path, evidence_path, scored_path)):
        return False
    try:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        scored = json.loads(scored_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if summary.get("provenance") != expected_provenance:
        raise RuntimeError("existing Solver thinking-off gate has different inputs; use a new output directory")
    return (
        isinstance(evidence, list)
        and isinstance(scored, list)
        and len(evidence) == summary.get("parseable_candidates")
        and sum(len(item.get("rollouts", [])) for item in evidence) == summary.get("total_solver_rollouts")
        and len(scored) == summary.get("scored_candidates")
    )


def validate_comparison_baseline(
    baseline_path: Path,
    current_provenance: dict[str, Any],
    expected_max_tokens: int,
) -> dict[str, Any]:
    """Prove that a prior completed gate differs only in output budget."""

    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    baseline_provenance = baseline.get("provenance")
    if not isinstance(baseline_provenance, dict):
        raise RuntimeError("comparison baseline is missing provenance")
    if baseline_provenance.get("max_tokens") != expected_max_tokens:
        raise RuntimeError(
            "comparison baseline max_tokens mismatch: "
            f"found {baseline_provenance.get('max_tokens')!r}, expected {expected_max_tokens}"
        )
    invariant_keys = (
        "input_sha256",
        "solver_config_sha256",
        "solver_revision",
        "enable_thinking",
        "samples",
        "seed",
        "temperature",
        "top_p",
        "top_k",
        "stop_semantics",
        "minimum_score",
        "maximum_score",
        "expected_total_candidates",
        "expected_parseable_candidates",
    )
    mismatches = {
        key: (baseline_provenance.get(key), current_provenance.get(key))
        for key in invariant_keys
        if baseline_provenance.get(key) != current_provenance.get(key)
    }
    if mismatches:
        raise RuntimeError(f"comparison baseline is not a single-variable match: {mismatches}")
    expected_rollouts = (
        current_provenance["expected_parseable_candidates"] * current_provenance["samples"]
    )
    expected_counts = {
        "total_candidates": current_provenance["expected_total_candidates"],
        "parseable_candidates": current_provenance["expected_parseable_candidates"],
        "total_solver_rollouts": expected_rollouts,
    }
    count_mismatches = {
        key: (baseline.get(key), expected)
        for key, expected in expected_counts.items()
        if baseline.get(key) != expected
    }
    if count_mismatches:
        raise RuntimeError(f"comparison baseline is incomplete: {count_mismatches}")
    return {
        "summary_path": str(baseline_path.resolve()),
        "summary_sha256": file_hash(baseline_path),
        "max_tokens": expected_max_tokens,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=9)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--top-p", type=float, default=1.0)
    parser.add_argument("--top-k", type=int, default=40)
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--min-score", type=float, default=0.3)
    parser.add_argument("--max-score", type=float, default=0.8)
    parser.add_argument("--expected-total-candidates", type=int, default=64)
    parser.add_argument("--expected-parseable-candidates", type=int, default=60)
    parser.add_argument("--expected-revision", default="1001bb4")
    parser.add_argument("--comparison-baseline", type=Path)
    parser.add_argument("--expected-baseline-max-tokens", type=int, default=4096)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    revision_path = args.model / "RZERO_MODEL_REVISION"
    if not revision_path.is_file():
        raise RuntimeError(f"missing immutable model revision receipt: {revision_path}")
    revision = revision_path.read_text(encoding="utf-8").strip()
    if revision != args.expected_revision:
        raise RuntimeError(f"Solver revision mismatch: found {revision!r}, expected {args.expected_revision!r}")
    all_candidates = json.loads(args.input.read_text(encoding="utf-8"))
    valid = [item for item in all_candidates if item.get("score") == 0]
    if len(all_candidates) != args.expected_total_candidates:
        raise RuntimeError(
            f"fixed candidate batch has {len(all_candidates)} rows, "
            f"expected {args.expected_total_candidates}"
        )
    if len(valid) != args.expected_parseable_candidates:
        raise RuntimeError(
            f"fixed candidate batch has {len(valid)} parseable rows, "
            f"expected {args.expected_parseable_candidates}"
        )
    provenance = {
        "input_path": str(args.input.resolve()),
        "input_sha256": file_hash(args.input),
        "solver_model_path": str(args.model.resolve()),
        "solver_config_sha256": file_hash(args.model / "config.json"),
        "solver_revision": revision,
        "enable_thinking": False,
        "samples": args.samples,
        "seed": args.seed,
        "temperature": args.temperature,
        "top_p": args.top_p,
        "top_k": args.top_k,
        "max_tokens": args.max_tokens,
        "stop_semantics": "tokenizer.eos_token_id_only",
        "minimum_score": args.min_score,
        "maximum_score": args.max_score,
        "expected_total_candidates": args.expected_total_candidates,
        "expected_parseable_candidates": args.expected_parseable_candidates,
    }
    if args.comparison_baseline:
        provenance["comparison_baseline"] = validate_comparison_baseline(
            args.comparison_baseline,
            provenance,
            args.expected_baseline_max_tokens,
        )
    evidence_path = args.output_dir / "raw_rollouts.json"
    scored_path = args.output_dir / "scored_n9.json"
    summary_path = args.output_dir / "summary.json"
    if args.resume and _existing_complete(summary_path, evidence_path, scored_path, provenance):
        print(f"[skip] complete Solver thinking-off gate: {summary_path}")
        return

    from mathruler.grader import extract_boxed_content, grade_answer
    from transformers import AutoTokenizer
    from vllm import LLM, SamplingParams

    tokenizer = AutoTokenizer.from_pretrained(args.model)
    prompts = [
        tokenizer.apply_chat_template(
            solver_messages(item["question"]),
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
        for item in valid
    ]
    if prompts:
        validate_rendered_prompt(prompts[0], False)
    model = LLM(
        model=str(args.model),
        tokenizer=str(args.model),
        gpu_memory_utilization=0.85,
        seed=args.seed,
        language_model_only=True,
    )
    sampling = SamplingParams(
        max_tokens=args.max_tokens,
        temperature=args.temperature,
        top_p=args.top_p,
        top_k=args.top_k,
        n=args.samples,
        stop_token_ids=[tokenizer.eos_token_id],
    )
    responses = model.generate(prompts, sampling_params=sampling, use_tqdm=True) if prompts else []
    evidence, scored = score_responses(valid, responses, extract_boxed_content, grade_answer, args.max_tokens)
    summary = build_summary(
        all_candidates,
        evidence,
        scored,
        provenance,
        args.min_score,
        args.max_score,
        args.max_tokens,
    )
    expected_rollouts = len(valid) * args.samples
    if summary["total_solver_rollouts"] != expected_rollouts:
        raise RuntimeError(
            f"captured {summary['total_solver_rollouts']} Solver rollouts, expected {expected_rollouts}"
        )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    atomic_json(evidence_path, evidence)
    atomic_json(scored_path, scored)
    # Commit marker is written last. A failure before this point is safely rerun.
    atomic_json(summary_path, summary)
    print(f"raw_output={evidence_path}")
    print(f"scored_output={scored_path}")
    print(f"summary_output={summary_path}")


if __name__ == "__main__":
    main()
