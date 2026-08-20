#!/usr/bin/env python3
"""Compare two-stage and unified majority voting on Terra validation."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from datasets import load_dataset
from mathruler.grader import grade_answer
from transformers import AutoTokenizer

from methods.gaussian_population_rzero.grading import answers_equivalent, extract_answer
from methods.validity_rl.evaluate_terra_validation import (
    DEFAULT_DATASET,
    DEFAULT_JUDGE_MODEL,
    MathAnswerRechecker,
    build_prompts as build_validity_prompts,
    normalize_invalid,
    safe_divide,
    validate_rows,
)


STAGE1_SAMPLES = 8
STAGE2_SAMPLES = 8
ONE_STAGE_SAMPLES = 16
TEMPERATURE = 1.0
TOP_P = 1.0
TOP_K = 40
DEFAULT_MAX_TOKENS = 4096
METHODS = ("two_stage", "one_stage")
METHOD_LABELS = {
    "two_stage": "Two-stage 8+8",
    "one_stage": "One-stage 16",
}
MATH_SYSTEM_PROMPT = r"Please reason step by step, and put your final answer within \boxed{}."


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Simulate two-stage 8+8 and unified 16-rollout Terra voting."
    )
    parser.add_argument("--model")
    parser.add_argument("--model-label")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--split", default="validation")
    parser.add_argument(
        "--prompt-template",
        type=Path,
        default=Path(__file__).with_name("validity_solver.jinja"),
    )
    parser.add_argument("--tensor-parallel-size", type=int, default=1)
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.85)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS)
    parser.add_argument(
        "--judge-model",
        default=os.getenv("RECHECK_JUDGE_MODEL", DEFAULT_JUDGE_MODEL),
    )
    parser.add_argument(
        "--judge-reasoning-effort",
        default=os.getenv("RECHECK_REASONING_EFFORT", "none"),
    )
    parser.add_argument(
        "--judge-max-completion-tokens",
        type=int,
        default=int(os.getenv("RECHECK_MAX_COMPLETION_TOKENS", "8")),
    )
    parser.add_argument("--api-timeout", type=float, default=30.0)
    parser.add_argument(
        "--skip-api-recheck",
        action="store_true",
        help="Use local mathruler only. This is not the formal comparable protocol.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=0,
        help="Number of questions passed to each vLLM generate call; 0 means all.",
    )
    parser.add_argument(
        "--allow-existing",
        action="store_true",
        help="Replace results.jsonl and summary.json in an existing output directory.",
    )
    parser.add_argument(
        "--compare-dir",
        type=Path,
        help="Only aggregate child summary.json files into comparison files and exit.",
    )
    args = parser.parse_args()
    if args.compare_dir is None:
        for name in ("model", "model_label", "output_dir"):
            if getattr(args, name) is None:
                parser.error(f"--{name.replace('_', '-')} is required")
        if args.tensor_parallel_size < 1:
            parser.error("--tensor-parallel-size must be positive")
        if args.max_tokens < 1:
            parser.error("--max-tokens must be positive")
        if args.batch_size < 0:
            parser.error("--batch-size cannot be negative")
    return args


def build_math_prompts(rows: Iterable[dict[str, Any]], tokenizer: Any) -> list[str]:
    chats = [
        [
            {"role": "system", "content": MATH_SYSTEM_PROMPT},
            {"role": "user", "content": str(row["question"])},
        ]
        for row in rows
    ]
    if tokenizer.chat_template:
        return [
            tokenizer.apply_chat_template(
                chat,
                tokenize=False,
                add_generation_prompt=True,
                add_special_tokens=True,
            )
            for chat in chats
        ]
    return [f"system: {chat[0]['content']}\nuser: {chat[1]['content']}" for chat in chats]


def generate_rollouts(
    llm: Any,
    vllm_module: Any,
    tokenizer: Any,
    prompts: list[str],
    samples: int,
    max_tokens: int,
    batch_size: int,
) -> list[list[str]]:
    sampling = vllm_module.SamplingParams(
        n=samples,
        max_tokens=max_tokens,
        temperature=TEMPERATURE,
        top_p=TOP_P,
        top_k=TOP_K,
        stop_token_ids=[tokenizer.eos_token_id],
    )
    if batch_size > 0:
        generated = []
        for start in range(0, len(prompts), batch_size):
            generated.extend(
                llm.generate(
                    prompts[start : start + batch_size],
                    sampling_params=sampling,
                    use_tqdm=True,
                )
            )
    else:
        generated = llm.generate(prompts, sampling_params=sampling, use_tqdm=True)
    if len(generated) != len(prompts):
        raise RuntimeError(f"generated {len(generated)} question outputs for {len(prompts)} prompts")
    responses = []
    for index, output in enumerate(generated):
        values = [candidate.text for candidate in output.outputs]
        if len(values) != samples:
            raise RuntimeError(
                f"question {index} returned {len(values)} rollouts; expected {samples}"
            )
        responses.append(values)
    return responses


def clean_extracted_answer(response: str) -> str:
    answer = extract_answer(response)
    return "" if answer == "None" else answer


def validity_decision(invalid_votes: int, total_votes: int) -> str:
    if invalid_votes * 2 > total_votes:
        return "INVALID"
    if invalid_votes * 2 < total_votes:
        return "VALID"
    return "TIE"


def cluster_math_answers(extracted_outputs: list[str]) -> dict[str, Any]:
    math_outputs = [
        answer for answer in extracted_outputs if answer and not normalize_invalid(answer)
    ]
    representatives: list[str] = []
    counts: list[int] = []
    for answer in math_outputs:
        for index, representative in enumerate(representatives):
            try:
                equivalent = answers_equivalent(answer, representative)
            except Exception as error:
                print(
                    f"Answer clustering failed for {answer!r} vs {representative!r}: {error}",
                    file=sys.stderr,
                )
                equivalent = False
            if equivalent:
                counts[index] += 1
                break
        else:
            representatives.append(answer)
            counts.append(1)

    if not counts:
        return {
            "math_outputs": math_outputs,
            "answer_clusters": [],
            "majority_answer": "",
            "majority_count": 0,
            "math_vote_tied": False,
        }
    majority_count = max(counts)
    majority_index = counts.index(majority_count)
    return {
        "math_outputs": math_outputs,
        "answer_clusters": [
            {"representative": representative, "count": count}
            for representative, count in zip(representatives, counts)
        ],
        "majority_answer": representatives[majority_index],
        "majority_count": majority_count,
        "math_vote_tied": counts.count(majority_count) > 1,
    }


def score_final_math(
    prediction: str,
    row: dict[str, Any],
    rechecker: MathAnswerRechecker | None,
) -> dict[str, Any]:
    local_math_correct = False
    api_rechecked = False
    api_math_correct: bool | None = None
    api_verdict: str | None = None
    api_error: str | None = None
    try:
        local_math_correct = bool(grade_answer(prediction, row["canonical_final_answer"]))
    except Exception as error:
        print(f"Final math grading failed for {row['id']}: {error}", file=sys.stderr)

    if local_math_correct or rechecker is None:
        final_correct = local_math_correct
    else:
        api_rechecked = True
        try:
            api_math_correct, api_verdict = rechecker.check(
                prediction,
                row["canonical_final_answer"],
                question=row["question"],
            )
        except Exception as error:
            api_error = str(error)
            api_math_correct = False
            print(f"API recheck failed for {row['id']}: {error}", file=sys.stderr)
        final_correct = bool(api_math_correct)
    return {
        "local_math_correct": local_math_correct,
        "api_rechecked": api_rechecked,
        "api_math_correct": api_math_correct,
        "api_verdict": api_verdict,
        "api_error": api_error,
        "final_correct": final_correct,
    }


def attach_outcome(
    method_result: dict[str, Any],
    row: dict[str, Any],
    final_type: str,
    prediction: str,
    rechecker: MathAnswerRechecker | None,
) -> dict[str, Any]:
    terra_validity = row["terra_validity"]
    scoring = {
        "local_math_correct": False,
        "api_rechecked": False,
        "api_math_correct": None,
        "api_verdict": None,
        "api_error": None,
    }
    if terra_validity == "INVALID":
        correct = final_type == "INVALID"
    elif final_type == "MATH":
        scoring = score_final_math(prediction, row, rechecker)
        correct = scoring.pop("final_correct")
    else:
        correct = False
    method_result.update(
        {
            "final_prediction_type": final_type,
            "final_prediction": prediction,
            **scoring,
            "correct": correct,
        }
    )
    return method_result


def build_two_stage_result(
    row: dict[str, Any],
    stage1_responses: list[str],
    stage2_responses: list[str] | None,
    rechecker: MathAnswerRechecker | None = None,
) -> dict[str, Any]:
    stage1_outputs = [clean_extracted_answer(response) for response in stage1_responses]
    invalid_votes = sum(normalize_invalid(answer) for answer in stage1_outputs)
    decision = validity_decision(invalid_votes, STAGE1_SAMPLES)
    result: dict[str, Any] = {
        "stage1_outputs": stage1_outputs,
        "stage1_invalid_votes": invalid_votes,
        "stage1_invalid_vote_fraction": invalid_votes / STAGE1_SAMPLES,
        "stage1_decision": decision,
        "stage2_outputs": [],
        "stage2_math_outputs": [],
        "stage2_answer_clusters": [],
        "stage2_majority_count": 0,
        "stage2_math_vote_tied": False,
        "math_vote_tied": False,
    }
    if decision == "INVALID":
        return attach_outcome(result, row, "INVALID", "INVALID", rechecker)
    if decision == "TIE":
        return attach_outcome(result, row, "TIE", "TIE", rechecker)
    if stage2_responses is None:
        raise RuntimeError(f"missing stage-2 responses for VALID decision on {row['id']}")

    stage2_outputs = [clean_extracted_answer(response) for response in stage2_responses]
    clustered = cluster_math_answers(stage2_outputs)
    result.update(
        {
            "stage2_outputs": stage2_outputs,
            "stage2_math_outputs": clustered["math_outputs"],
            "stage2_answer_clusters": clustered["answer_clusters"],
            "stage2_majority_count": clustered["majority_count"],
            "stage2_math_vote_tied": clustered["math_vote_tied"],
            "math_vote_tied": clustered["math_vote_tied"],
        }
    )
    majority = clustered["majority_answer"]
    final_type = "MATH" if majority else "NO_ANSWER"
    return attach_outcome(result, row, final_type, majority, rechecker)


def build_one_stage_result(
    row: dict[str, Any],
    unified_responses: list[str],
    rechecker: MathAnswerRechecker | None = None,
) -> dict[str, Any]:
    extracted_outputs = [clean_extracted_answer(response) for response in unified_responses]
    invalid_votes = sum(normalize_invalid(answer) for answer in extracted_outputs)
    decision = validity_decision(invalid_votes, ONE_STAGE_SAMPLES)
    math_candidates = [answer for answer in extracted_outputs if not normalize_invalid(answer)]
    result: dict[str, Any] = {
        "outputs": extracted_outputs,
        "invalid_votes": invalid_votes,
        "invalid_vote_fraction": invalid_votes / ONE_STAGE_SAMPLES,
        "validity_decision": decision,
        "math_outputs": [],
        "answer_clusters": [],
        "majority_count": 0,
        "math_vote_tied": False,
    }
    if decision == "INVALID":
        return attach_outcome(result, row, "INVALID", "INVALID", rechecker)
    if decision == "TIE":
        return attach_outcome(result, row, "TIE", "TIE", rechecker)

    clustered = cluster_math_answers(math_candidates)
    result.update(
        {
            "math_outputs": clustered["math_outputs"],
            "answer_clusters": clustered["answer_clusters"],
            "majority_count": clustered["majority_count"],
            "math_vote_tied": clustered["math_vote_tied"],
        }
    )
    majority = clustered["majority_answer"]
    final_type = "MATH" if majority else "NO_ANSWER"
    return attach_outcome(result, row, final_type, majority, rechecker)


def vote_histogram(values: Iterable[int], maximum: int) -> dict[str, int]:
    counts = Counter(values)
    return {str(value): counts.get(value, 0) for value in range(maximum + 1)}


def metrics_for(records: list[dict[str, Any]], method: str) -> dict[str, Any]:
    if method not in METHODS:
        raise ValueError(f"unknown method: {method}")
    valid = [record for record in records if record["terra_label"] == "VALID"]
    invalid = [record for record in records if record["terra_label"] == "INVALID"]
    results = [record[method] for record in records]
    valid_results = [record[method] for record in valid]
    invalid_results = [record[method] for record in invalid]
    final_invalid = sum(result["final_prediction_type"] == "INVALID" for result in results)
    true_invalid = sum(result["final_prediction_type"] == "INVALID" for result in invalid_results)
    false_invalid = sum(result["final_prediction_type"] == "INVALID" for result in valid_results)
    valid_math_correct = sum(result["correct"] for result in valid_results)
    ties = sum(result["final_prediction_type"] == "TIE" for result in results)
    vote_key = "stage1_invalid_votes" if method == "two_stage" else "invalid_votes"
    maximum = STAGE1_SAMPLES if method == "two_stage" else ONE_STAGE_SAMPLES
    vote_values = [int(result[vote_key]) for result in results]
    valid_vote_values = [int(result[vote_key]) for result in valid_results]
    invalid_vote_values = [int(result[vote_key]) for result in invalid_results]
    stage2_questions = (
        sum(record["two_stage"]["stage1_decision"] == "VALID" for record in records)
        if method == "two_stage"
        else 0
    )
    generated_rollouts = (
        len(records) * STAGE1_SAMPLES + stage2_questions * STAGE2_SAMPLES
        if method == "two_stage"
        else len(records) * ONE_STAGE_SAMPLES
    )
    return {
        "n": len(records),
        "n_valid": len(valid),
        "n_invalid": len(invalid),
        "final_outcome_accuracy": safe_divide(sum(result["correct"] for result in results), len(results)),
        "valid_math_accuracy": safe_divide(valid_math_correct, len(valid_results)),
        "invalid_recall": safe_divide(true_invalid, len(invalid_results)),
        "invalid_precision": safe_divide(true_invalid, final_invalid),
        "false_invalid_rate": safe_divide(false_invalid, len(valid_results)),
        "tie_rate": safe_divide(ties, len(results)),
        "counts": {
            "correct": sum(result["correct"] for result in results),
            "final_invalid": final_invalid,
            "true_invalid": true_invalid,
            "false_invalid": false_invalid,
            "valid_math_correct": valid_math_correct,
            "local_math_correct": sum(result["local_math_correct"] for result in results),
            "api_rechecked": sum(result["api_rechecked"] for result in results),
            "api_math_correct": sum(result["api_math_correct"] is True for result in results),
            "api_errors": sum(bool(result["api_error"]) for result in results),
            "ties": ties,
            "no_answer": sum(result["final_prediction_type"] == "NO_ANSWER" for result in results),
            "math_vote_ties": sum(result["math_vote_tied"] for result in results),
            "stage2_questions": stage2_questions,
            "generated_rollouts": generated_rollouts,
        },
        "average_rollouts_per_question": safe_divide(generated_rollouts, len(records)),
        "vote_statistics": {
            "average_invalid_votes": safe_divide(sum(vote_values), len(vote_values)),
            "average_invalid_vote_fraction": safe_divide(sum(vote_values), len(vote_values) * maximum),
            "terra_valid_average_invalid_votes": safe_divide(
                sum(valid_vote_values), len(valid_vote_values)
            ),
            "terra_invalid_average_invalid_votes": safe_divide(
                sum(invalid_vote_values), len(invalid_vote_values)
            ),
            "all": vote_histogram(vote_values, maximum),
            "terra_valid": vote_histogram(valid_vote_values, maximum),
            "terra_invalid": vote_histogram(invalid_vote_values, maximum),
        },
    }


def build_summary(args: argparse.Namespace, records: list[dict[str, Any]]) -> dict[str, Any]:
    by_round: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_round[record["round"]].append(record)
    methods = {}
    for method in METHODS:
        methods[method] = {
            "label": METHOD_LABELS[method],
            "overall": metrics_for(records, method),
            "per_round": {
                round_name: metrics_for(round_records, method)
                for round_name, round_records in sorted(by_round.items())
            },
        }
    return {
        "model": args.model,
        "model_label": args.model_label,
        "dataset": args.dataset,
        "split": args.split,
        "sampling": {
            "temperature": TEMPERATURE,
            "top_p": TOP_P,
            "top_k": TOP_K,
            "max_tokens": args.max_tokens,
            "stop": "tokenizer.eos_token_id",
            "seed": args.seed,
        },
        "protocol": {
            "two_stage": {
                "stage1_prompt": "validity_solver.jinja",
                "stage1_rollouts": STAGE1_SAMPLES,
                "stage2_prompt": MATH_SYSTEM_PROMPT,
                "stage2_rollouts": STAGE2_SAMPLES,
                "stage2_condition": "stage1_decision == VALID",
            },
            "one_stage": {
                "prompt": "validity_solver.jinja",
                "rollouts": ONE_STAGE_SAMPLES,
                "math_vote": "exclude INVALID and unusable boxed outputs",
            },
            "validity_ties": "preserved as TIE",
            "math_cluster_ties": "first representative wins, matching R-Zero",
            "final_math_grader": {
                "local_grader": "mathruler.grade_answer",
                "authoritative": (
                    "local mathruler with API fallback for locally incorrect answers"
                    if not args.skip_api_recheck
                    else "local mathruler only (non-formal diagnostic)"
                ),
                "judge_model": args.judge_model if not args.skip_api_recheck else None,
                "reasoning_effort": (
                    args.judge_reasoning_effort if not args.skip_api_recheck else None
                ),
                "max_completion_tokens": (
                    args.judge_max_completion_tokens if not args.skip_api_recheck else None
                ),
                "api_scope": (
                    "Terra VALID with final_prediction_type == MATH and local_math_correct == false"
                ),
                "api_context": "question, canonical answer, and majority prediction",
            },
        },
        "methods": methods,
    }


def metric_cells(metrics: dict[str, Any]) -> list[str]:
    return [
        f"{metrics['final_outcome_accuracy']:.4f}",
        f"{metrics['valid_math_accuracy']:.4f}",
        f"{metrics['invalid_recall']:.4f}",
        f"{metrics['invalid_precision']:.4f}",
        f"{metrics['false_invalid_rate']:.4f}",
        f"{metrics['tie_rate']:.4f}",
    ]


def comparison_markdown(summaries: list[dict[str, Any]]) -> str:
    lines = [
        "# Terra Majority-Vote Simulation",
        "",
        "| Model | Method | Outcome Acc | Valid Math | Invalid Recall | Invalid Precision | False Invalid | Tie |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for summary in summaries:
        for method in METHODS:
            method_summary = summary["methods"][method]
            cells = metric_cells(method_summary["overall"])
            lines.append(
                f"| {summary['model_label']} | {method_summary['label']} | "
                + " | ".join(cells)
                + " |"
            )
    for summary in summaries:
        lines.extend(
            [
                "",
                f"## {summary['model_label']}",
                "",
                "| Round | Method | N | Valid N | Invalid N | Outcome Acc | Valid Math | Invalid Recall | False Invalid |",
                "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        rounds = sorted(
            {
                round_name
                for method in METHODS
                for round_name in summary["methods"][method]["per_round"]
            }
        )
        for round_name in rounds:
            for method in METHODS:
                method_summary = summary["methods"][method]
                metrics = method_summary["per_round"][round_name]
                lines.append(
                    f"| {round_name} | {method_summary['label']} | {metrics['n']} | "
                    f"{metrics['n_valid']} | {metrics['n_invalid']} | "
                    f"{metrics['final_outcome_accuracy']:.4f} | "
                    f"{metrics['valid_math_accuracy']:.4f} | "
                    f"{metrics['invalid_recall']:.4f} | "
                    f"{metrics['false_invalid_rate']:.4f} |"
                )
    return "\n".join(lines) + "\n"


def compare_summaries(root: Path) -> None:
    summaries = []
    for path in root.glob("*/summary.json"):
        with path.open(encoding="utf-8") as handle:
            summaries.append(json.load(handle))
    if not summaries:
        raise RuntimeError(f"no child summary.json files found under {root}")
    order = {"base": 0, "step_5": 1, "step_10": 2, "step_15": 3}
    summaries.sort(key=lambda item: order.get(item["model_label"], 99))
    comparison = {
        "experiment": "Terra majority-vote architecture simulation",
        "models": [
            {
                "model": summary["model"],
                "model_label": summary["model_label"],
                "methods": summary["methods"],
            }
            for summary in summaries
        ],
    }
    json_path = root / "comparison.json"
    markdown_path = root / "comparison.md"
    markdown = comparison_markdown(summaries)
    json_path.write_text(json.dumps(comparison, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(markdown, encoding="utf-8")
    print(markdown)
    print(f"Wrote {json_path}")
    print(f"Wrote {markdown_path}")


def main() -> None:
    args = parse_args()
    if args.compare_dir is not None:
        compare_summaries(args.compare_dir)
        return

    args.output_dir.mkdir(parents=True, exist_ok=True)
    results_path = args.output_dir / "results.jsonl"
    summary_path = args.output_dir / "summary.json"
    if not args.allow_existing and (results_path.exists() or summary_path.exists()):
        raise FileExistsError(
            f"results already exist under {args.output_dir}; use a new tag or --allow-existing"
        )

    rows = load_dataset(args.dataset, "default", split=args.split)
    validate_rows(rows, args.split)
    records = [dict(row) for row in rows]
    print(f"Loaded {len(records)} rows from {args.dataset}/{args.split}")
    print(
        "Sampling: temperature=1.0, top_p=1.0, top_k=40, "
        f"max_tokens={args.max_tokens}, seed={args.seed}"
    )
    rechecker = None
    if not args.skip_api_recheck:
        rechecker = MathAnswerRechecker(
            model=args.judge_model,
            reasoning_effort=args.judge_reasoning_effort,
            max_completion_tokens=args.judge_max_completion_tokens,
            timeout=args.api_timeout,
        )
        print(f"Final math judge: {args.judge_model}")
    else:
        print("Final math judge: local-only diagnostic (API recheck disabled)")

    import vllm

    tokenizer = AutoTokenizer.from_pretrained(args.model)
    llm = vllm.LLM(
        model=args.model,
        tokenizer=args.model,
        tensor_parallel_size=args.tensor_parallel_size,
        gpu_memory_utilization=args.gpu_memory_utilization,
        seed=args.seed,
        enable_prefix_caching=False,
    )
    validity_prompts = build_validity_prompts(records, tokenizer, args.prompt_template)
    print(f"Generating two-stage validity votes ({STAGE1_SAMPLES} per question)")
    stage1_responses = generate_rollouts(
        llm,
        vllm,
        tokenizer,
        validity_prompts,
        STAGE1_SAMPLES,
        args.max_tokens,
        args.batch_size,
    )
    print(f"Generating one-stage unified votes ({ONE_STAGE_SAMPLES} per question)")
    unified_responses = generate_rollouts(
        llm,
        vllm,
        tokenizer,
        validity_prompts,
        ONE_STAGE_SAMPLES,
        args.max_tokens,
        args.batch_size,
    )

    stage1_decisions = []
    for responses in stage1_responses:
        outputs = [clean_extracted_answer(response) for response in responses]
        stage1_decisions.append(
            validity_decision(sum(normalize_invalid(answer) for answer in outputs), STAGE1_SAMPLES)
        )
    stage2_indices = [
        index for index, decision in enumerate(stage1_decisions) if decision == "VALID"
    ]
    stage2_by_index: dict[int, list[str]] = {}
    if stage2_indices:
        stage2_rows = [records[index] for index in stage2_indices]
        math_prompts = build_math_prompts(stage2_rows, tokenizer)
        print(
            f"Generating two-stage math votes for {len(stage2_indices)} VALID decisions "
            f"({STAGE2_SAMPLES} per question)"
        )
        generated_stage2 = generate_rollouts(
            llm,
            vllm,
            tokenizer,
            math_prompts,
            STAGE2_SAMPLES,
            args.max_tokens,
            args.batch_size,
        )
        stage2_by_index = dict(zip(stage2_indices, generated_stage2))

    output_records = []
    with results_path.open("w", encoding="utf-8") as handle:
        for index, row in enumerate(records):
            record = {
                "id": row["id"],
                "round": row["round"],
                "terra_label": row["terra_validity"],
                "terra_source_label": row.get("terra_label"),
                "terra_answer": row["canonical_final_answer"],
                "two_stage": build_two_stage_result(
                    row,
                    stage1_responses[index],
                    stage2_by_index.get(index),
                    rechecker,
                ),
                "one_stage": build_one_stage_result(
                    row, unified_responses[index], rechecker
                ),
            }
            output_records.append(record)
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            handle.flush()

    summary = build_summary(args, output_records)
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Wrote {results_path}")
    print(f"Wrote {summary_path}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        raise SystemExit(130)
