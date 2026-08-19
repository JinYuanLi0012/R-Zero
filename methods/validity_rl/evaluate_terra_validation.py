#!/usr/bin/env python3
"""Deterministic pass@1 evaluation on the held-out Terra validation split."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

import requests
from datasets import load_dataset
from jinja2 import Template
from mathruler.grader import extract_boxed_content, grade_answer
from transformers import AutoTokenizer


DEFAULT_DATASET = "jinyuan222/rzero-validity-rl-terra-v1"
DEFAULT_JUDGE_MODEL = "gpt-5.6-luna"
EXPECTED_VALIDATION_SIZE = 297
MAX_TOKENS = 4096
INVALID = "INVALID"
REQUIRED_COLUMNS = {
    "id",
    "round",
    "question",
    "terra_validity",
    "canonical_final_answer",
    "answer_verified",
    "validity_rl_target",
    "split",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate one model on Terra validation with R-Zero pass@1 settings."
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
    parser.add_argument("--judge-model", default=os.getenv("RECHECK_JUDGE_MODEL", DEFAULT_JUDGE_MODEL))
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
        help="Use local mathruler scores only. This does not match the full R-Zero protocol.",
    )
    parser.add_argument(
        "--allow-existing",
        action="store_true",
        help="Replace results.jsonl and summary.json in an existing output directory.",
    )
    parser.add_argument(
        "--compare-dir",
        type=Path,
        help="Only aggregate child summary.json files into comparison.json and exit.",
    )
    args = parser.parse_args()
    if args.compare_dir is None:
        for name in ("model", "model_label", "output_dir"):
            if getattr(args, name) is None:
                parser.error(f"--{name.replace('_', '-')} is required")
    return args


def normalize_invalid(answer: Any) -> bool:
    return isinstance(answer, str) and answer.strip().casefold() == INVALID.casefold()


def safe_divide(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def validate_rows(rows: Any, split_name: str) -> None:
    missing = REQUIRED_COLUMNS.difference(rows.column_names)
    if missing:
        raise ValueError(f"dataset is missing columns: {sorted(missing)}")
    if split_name != "validation":
        raise ValueError("this evaluator is restricted to the held-out validation split")
    if len(rows) != EXPECTED_VALIDATION_SIZE:
        raise ValueError(
            f"expected {EXPECTED_VALIDATION_SIZE} RL-eligible validation rows, got {len(rows)}"
        )

    seen_ids: set[str] = set()
    for index, row in enumerate(rows):
        row_id = row["id"]
        validity = row["terra_validity"]
        if not row_id or row_id in seen_ids:
            raise ValueError(f"row {index} has a missing or duplicate id: {row_id!r}")
        seen_ids.add(row_id)
        if row["split"] != split_name:
            raise ValueError(f"row {row_id} carries split={row['split']!r}")
        if validity not in {"VALID", "INVALID"}:
            raise ValueError(f"row {row_id} has terra_validity={validity!r}")
        if validity == "VALID":
            if row["answer_verified"] is not True or not row["canonical_final_answer"]:
                raise ValueError(f"VALID row {row_id} lacks a verified canonical answer")
            if row["validity_rl_target"] != row["canonical_final_answer"]:
                raise ValueError(f"VALID row {row_id} has a target/canonical mismatch")
        elif row["validity_rl_target"] != INVALID:
            raise ValueError(f"INVALID row {row_id} has a non-INVALID target")


def build_prompts(rows: Iterable[dict[str, Any]], tokenizer: Any, template_path: Path) -> list[str]:
    template = Template(template_path.read_text(encoding="utf-8").strip())
    messages = [
        [{"role": "user", "content": template.render(content=row["question"]).strip()}]
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
            for chat in messages
        ]
    return [f"user: {chat[0]['content']}\nassistant:" for chat in messages]


def generate_responses(args: argparse.Namespace, rows: Any) -> list[str]:
    import vllm

    tokenizer = AutoTokenizer.from_pretrained(args.model)
    prompts = build_prompts(rows, tokenizer, args.prompt_template)
    model = vllm.LLM(
        model=args.model,
        tokenizer=args.model,
        tensor_parallel_size=args.tensor_parallel_size,
        gpu_memory_utilization=args.gpu_memory_utilization,
    )
    sampling_params = vllm.SamplingParams(
        n=1,
        max_tokens=MAX_TOKENS,
        temperature=0.0,
        stop_token_ids=[tokenizer.eos_token_id],
    )
    outputs = model.generate(prompts, sampling_params=sampling_params, use_tqdm=True)
    responses = [output.outputs[0].text for output in outputs]
    if len(responses) != len(rows):
        raise RuntimeError(f"generated {len(responses)} responses for {len(rows)} rows")
    return responses


class MathAnswerRechecker:
    """R-Zero-style Yes/No API recheck for mathematical equivalence only."""

    def __init__(
        self,
        model: str,
        reasoning_effort: str,
        max_completion_tokens: int,
        timeout: float,
    ) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is required for math answer rechecks; "
                "use --skip-api-recheck only for an explicitly local-only run"
            )
        api_base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        self.url = f"{api_base}/chat/completions"
        self.headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.max_completion_tokens = max_completion_tokens
        self.timeout = timeout
        self.session = requests.Session()

    def check(self, model_response: str, canonical_answer: str) -> tuple[bool, str]:
        prompt = (
            "Decide only whether the mathematical answer given in the model response is "
            "equivalent to the canonical mathematical answer. Do not assess whether the "
            "underlying problem is valid or invalid. Return only Yes or No.\n\n"
            f"Model response: {model_response}\n"
            f"Canonical answer: {canonical_answer}"
        )
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a math answer equivalence checker."},
                {"role": "user", "content": prompt},
            ],
        }
        if self.model.startswith("gpt-5"):
            payload["max_completion_tokens"] = self.max_completion_tokens
            if self.reasoning_effort:
                payload["reasoning_effort"] = self.reasoning_effort
        else:
            payload["temperature"] = 0.0

        response = self.session.post(
            self.url,
            headers=self.headers,
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        verdict = response.json()["choices"][0]["message"]["content"].strip()
        normalized = re.sub(r"[^a-z].*$", "", verdict.casefold())
        if normalized not in {"yes", "no"}:
            raise RuntimeError(f"judge returned neither Yes nor No: {verdict!r}")
        return normalized == "yes", verdict


def score_response(
    row: dict[str, Any],
    response: str,
    rechecker: MathAnswerRechecker | None,
) -> dict[str, Any]:
    extracted = extract_boxed_content(response)
    extracted_answer = extracted.strip() if isinstance(extracted, str) else ""
    pred_invalid = normalize_invalid(extracted_answer)
    terra_validity = row["terra_validity"]
    canonical = row["canonical_final_answer"]
    local_math_correct = False
    api_rechecked = False
    api_math_correct: bool | None = None
    api_verdict: str | None = None
    api_error: str | None = None

    if terra_validity == "INVALID":
        final_correct = pred_invalid
    elif pred_invalid:
        final_correct = False
    else:
        try:
            local_math_correct = bool(extracted_answer) and bool(
                grade_answer(extracted_answer, canonical)
            )
        except Exception as error:
            print(f"Local grader failed for {row['id']}: {error}", file=sys.stderr)
            local_math_correct = False
        final_correct = local_math_correct
        if not local_math_correct and rechecker is not None:
            api_rechecked = True
            try:
                api_math_correct, api_verdict = rechecker.check(response, canonical)
            except Exception as error:
                api_error = str(error)
                api_math_correct = False
                print(f"API recheck failed for {row['id']}: {error}", file=sys.stderr)
            final_correct = api_math_correct

    return {
        "id": row["id"],
        "round": row["round"],
        "terra_validity": terra_validity,
        "canonical_answer": canonical,
        "response": response,
        "extracted_answer": extracted_answer,
        "pred_invalid": pred_invalid,
        "local_math_correct": local_math_correct,
        "api_rechecked": api_rechecked,
        "api_math_correct": api_math_correct,
        "api_verdict": api_verdict,
        "api_error": api_error,
        "final_correct": bool(final_correct),
    }


def metrics_for(results: list[dict[str, Any]]) -> dict[str, Any]:
    valid = [result for result in results if result["terra_validity"] == "VALID"]
    invalid = [result for result in results if result["terra_validity"] == "INVALID"]
    valid_correct = sum(result["final_correct"] for result in valid)
    valid_false_invalid = sum(result["pred_invalid"] for result in valid)
    invalid_correct = sum(result["pred_invalid"] for result in invalid)
    pred_invalid = valid_false_invalid + invalid_correct
    valid_wrong_math_or_other = len(valid) - valid_correct - valid_false_invalid
    return {
        "n": len(results),
        "n_valid": len(valid),
        "n_invalid": len(invalid),
        "overall_accuracy": safe_divide(valid_correct + invalid_correct, len(results)),
        "valid_math_accuracy": safe_divide(valid_correct, len(valid)),
        "invalid_recall": safe_divide(invalid_correct, len(invalid)),
        "invalid_precision": safe_divide(invalid_correct, pred_invalid),
        "false_invalid_rate": safe_divide(valid_false_invalid, len(valid)),
        "counts": {
            "valid_correct_math": valid_correct,
            "valid_wrong_math_or_other": valid_wrong_math_or_other,
            "valid_to_invalid": valid_false_invalid,
            "invalid_to_invalid": invalid_correct,
            "invalid_to_math_or_other": len(invalid) - invalid_correct,
        },
    }


def build_summary(args: argparse.Namespace, results: list[dict[str, Any]]) -> dict[str, Any]:
    by_round: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for result in results:
        by_round[result["round"]].append(result)
    return {
        "model": args.model,
        "model_label": args.model_label,
        "dataset": args.dataset,
        "split": args.split,
        "generation": {
            "n": 1,
            "temperature": 0.0,
            "max_tokens": MAX_TOKENS,
            "stop": "tokenizer.eos_token_id",
        },
        "api_recheck": {
            "enabled": not args.skip_api_recheck,
            "judge_model": args.judge_model if not args.skip_api_recheck else None,
            "scope": "all locally incorrect VALID responses except explicit INVALID predictions",
        },
        "metrics": metrics_for(results),
        "per_round": {
            round_name: metrics_for(round_results)
            for round_name, round_results in sorted(by_round.items())
        },
    }


def print_metrics(summary: dict[str, Any]) -> None:
    metrics = summary["metrics"]
    print(f"\n{summary['model_label']} ({summary['model']})")
    print(f"  n: {metrics['n']} ({metrics['n_valid']} VALID, {metrics['n_invalid']} INVALID)")
    for key in (
        "overall_accuracy",
        "valid_math_accuracy",
        "invalid_recall",
        "invalid_precision",
        "false_invalid_rate",
    ):
        print(f"  {key}: {metrics[key]:.4f}")
    print(f"  counts: {json.dumps(metrics['counts'], sort_keys=True)}")


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
        "protocol": "deterministic pass@1 (n=1, temperature=0.0, max_tokens=4096)",
        "models": [
            {"model": item["model"], "model_label": item["model_label"], **item["metrics"]}
            for item in summaries
        ],
    }
    output = root / "comparison.json"
    output.write_text(json.dumps(comparison, indent=2) + "\n", encoding="utf-8")
    print("\n| Model | Overall | Valid Math | Invalid Recall | Invalid Precision | False Invalid |")
    print("| --- | ---: | ---: | ---: | ---: | ---: |")
    for item in summaries:
        metrics = item["metrics"]
        values = [
            metrics["overall_accuracy"],
            metrics["valid_math_accuracy"],
            metrics["invalid_recall"],
            metrics["invalid_precision"],
            metrics["false_invalid_rate"],
        ]
        print(f"| {item['model_label']} | " + " | ".join(f"{value:.4f}" for value in values) + " |")
    print(f"\nWrote {output}")


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
    print(f"Loaded {len(rows)} RL-eligible rows from {args.dataset}/{args.split}")
    print("Generation protocol: n=1, temperature=0.0, max_tokens=4096")
    rechecker = None
    if not args.skip_api_recheck:
        rechecker = MathAnswerRechecker(
            model=args.judge_model,
            reasoning_effort=args.judge_reasoning_effort,
            max_completion_tokens=args.judge_max_completion_tokens,
            timeout=args.api_timeout,
        )
    responses = generate_responses(args, rows)

    results = []
    with results_path.open("w", encoding="utf-8") as handle:
        for row, response in zip(rows, responses):
            result = score_response(row, response, rechecker)
            results.append(result)
            handle.write(json.dumps(result, ensure_ascii=False) + "\n")
            handle.flush()

    summary = build_summary(args, results)
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print_metrics(summary)
    print(f"Wrote {results_path}")
    print(f"Wrote {summary_path}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        raise SystemExit(130)
