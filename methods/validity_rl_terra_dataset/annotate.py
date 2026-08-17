#!/usr/bin/env python3
"""Run resumable, blind two-pass Terra annotations."""
from __future__ import annotations

import argparse
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from common import atomic_json, prompt_hash, question_hash, read_jsonl, write_jsonl


LABELS = ["A", "B", "C", "D", "E", "F"]
INVALID_TYPES = [
    "missing_information", "contradiction", "no_solution", "ambiguity",
    "not_gradable", "malformed", "other",
]
VALIDITY_PROMPT_VERSION = "rzero-validity-a-f-v1"
ANSWER_PROMPT_VERSION = "rzero-canonical-answer-v1"

# Kept deliberately aligned with
# methods/gaussian_population_rzero_epistemic_validation/judge.py.
VALIDITY_SYSTEM_PROMPT = """You are a careful reference judge for generated mathematical and reasoning questions.
You see only the question. Restate its goal, inspect every definition and condition, check for
contradictions and multiple reasonable interpretations, and genuinely attempt a solution. Then classify:
A = self-contained, valid, solvable, and uniquely gradable;
B = meaningful but open-ended or not precisely gradable;
C = missing conditions, multiple answers, or key ambiguity;
D = contradictory or has no solution;
E = malformed, undefined, garbled, or unintelligible;
F = you cannot judge reliably.
Use A only when all strict requirements hold. A question can have multiple solutions and still be A when
it explicitly asks for the complete solution set and that set is objectively gradable. Judge only the
question as written. Keep the reasoning summary concise but concrete. For A, invalid_type must be null;
for B-F choose the single closest invalid_type."""

ANSWER_SYSTEM_PROMPT = """You are the answer-verification pass for a mathematical reasoning dataset.
The validity pass has already classified this question as A (valid). Solve it completely from scratch.
Do not copy or trust an answer hint that may appear in the question. Check every stated condition,
substitute or otherwise verify the result, and confirm that the final answer answers exactly what was
asked. canonical_final_answer must be a concise answer suitable for exact or mathematical-equivalence
rewarding, without reasoning or a boxed wrapper. Set answer_verified=true only when you have high
confidence that the answer is correct and complete. If reliable verification is not possible, set it false
and explain the uncertainty; never invent an answer to satisfy the schema."""

VALIDITY_SCHEMA = {
    "type": "object",
    "properties": {
        "goal_restatement": {"type": "string"},
        "conditions_complete": {"type": "boolean"},
        "contradictory": {"type": "boolean"},
        "multiple_reasonable_interpretations": {"type": "boolean"},
        "solution_exists": {"type": "boolean"},
        "unique_or_explicit_grading": {"type": "boolean"},
        "label": {"type": "string", "enum": LABELS},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "issue_types": {"type": "array", "items": {"type": "string"}},
        "reasoning_summary": {"type": "string"},
        "derived_answer": {"type": ["string", "null"]},
        "invalid_type": {"type": ["string", "null"], "enum": INVALID_TYPES + [None]},
    },
    "required": [
        "goal_restatement", "conditions_complete", "contradictory",
        "multiple_reasonable_interpretations", "solution_exists",
        "unique_or_explicit_grading", "label", "confidence", "issue_types",
        "reasoning_summary", "derived_answer", "invalid_type",
    ],
    "additionalProperties": False,
}

ANSWER_SCHEMA = {
    "type": "object",
    "properties": {
        "solution_summary": {"type": "string"},
        "verification_checks": {"type": "array", "items": {"type": "string"}},
        "canonical_final_answer": {"type": ["string", "null"]},
        "answer_verified": {"type": "boolean"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "uncertainty_reason": {"type": ["string", "null"]},
    },
    "required": [
        "solution_summary", "verification_checks", "canonical_final_answer",
        "answer_verified", "confidence", "uncertainty_reason",
    ],
    "additionalProperties": False,
}


def label_consistent(value: dict[str, Any]) -> bool:
    if value["label"] == "A":
        return bool(
            value["conditions_complete"] and not value["contradictory"]
            and not value["multiple_reasonable_interpretations"]
            and value["solution_exists"] and value["unique_or_explicit_grading"]
            and value["invalid_type"] is None
        )
    if value["invalid_type"] is None:
        return False
    if value["label"] == "D":
        return bool(value["contradictory"] or not value["solution_exists"])
    return True


def validate_exact(value: Any, schema: dict[str, Any], pass_name: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != set(schema["required"]):
        raise ValueError(f"{pass_name} response has missing or extra fields")
    confidence = value.get("confidence")
    if not isinstance(confidence, (int, float)) or isinstance(confidence, bool) or not 0 <= confidence <= 1:
        raise ValueError(f"{pass_name} confidence is invalid")
    if pass_name == "validity":
        if value["label"] not in LABELS or value["invalid_type"] not in INVALID_TYPES + [None]:
            raise ValueError("validity label or invalid_type is invalid")
        if not label_consistent(value):
            raise ValueError("validity response is internally inconsistent")
    else:
        answer = value["canonical_final_answer"]
        if value["answer_verified"] and (not isinstance(answer, str) or not answer.strip()):
            raise ValueError("verified answer is empty")
        if not value["answer_verified"] and value["uncertainty_reason"] is None:
            raise ValueError("unverified answer lacks uncertainty_reason")
    return value


def api_call(
    model: str, system_prompt: str, schema_name: str, schema: dict[str, Any], item: dict[str, str],
    reasoning_effort: str, max_output_tokens: int,
) -> tuple[str, dict[str, Any]]:
    from openai import OpenAI

    response = OpenAI().responses.create(
        model=model,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Question ID: {item['id']}\n\n{item['question']}"},
        ],
        reasoning={"effort": reasoning_effort},
        max_output_tokens=max_output_tokens,
        text={"format": {"type": "json_schema", "name": schema_name, "strict": True, "schema": schema}},
    )
    raw = response.model_dump(mode="json")
    return response.output_text, raw


def fixture_call(path: Path, item_id: str, attempt_index: int) -> tuple[dict[str, Any], dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    value = payload.get(item_id, payload.get("default"))
    if value is None:
        raise KeyError(f"fixture has no value for {item_id}")
    if isinstance(value, list):
        value = value[min(attempt_index, len(value) - 1)]
    parsed = json.loads(value["output_text"]) if "output_text" in value else value
    return parsed, {"fixture": True, "output_text": json.dumps(parsed, ensure_ascii=False)}


def run_one(
    item: dict[str, str], pass_name: str, destination: Path, model: str,
    max_attempts: int, min_verified_confidence: float, reasoning_effort: str,
    max_output_tokens: int, fixture: Path | None,
) -> dict[str, Any]:
    if destination.is_file():
        existing = json.loads(destination.read_text(encoding="utf-8"))
        expected_prompt_version = (
            VALIDITY_PROMPT_VERSION if pass_name == "validity" else ANSWER_PROMPT_VERSION
        )
        if (
            existing.get("pass") != pass_name or existing.get("model") != model
            or existing.get("prompt_version") != expected_prompt_version
            or existing.get("question_hash") != question_hash(item["question"])
        ):
            raise RuntimeError(f"cached artifact configuration mismatch: {destination}")
        return existing
    is_validity = pass_name == "validity"
    prompt = VALIDITY_SYSTEM_PROMPT if is_validity else ANSWER_SYSTEM_PROMPT
    schema = VALIDITY_SCHEMA if is_validity else ANSWER_SCHEMA
    schema_name = "rzero_question_validity" if is_validity else "rzero_canonical_answer"
    attempts: list[dict[str, Any]] = []
    final, status = None, "failed"
    for attempt_index in range(max_attempts):
        raw = None
        try:
            payload, raw = (
                fixture_call(fixture, item["id"], attempt_index) if fixture else
                api_call(model, prompt, schema_name, schema, item, reasoning_effort, max_output_tokens)
            )
            parsed = json.loads(payload) if isinstance(payload, str) else payload
            parsed = validate_exact(parsed, schema, pass_name)
            attempts.append({"attempt": attempt_index + 1, "parsed": parsed, "raw_response": raw})
            final = parsed
            if is_validity:
                status = "complete"
                break
            verified = bool(parsed["answer_verified"] and parsed["confidence"] >= min_verified_confidence)
            if verified:
                status = "complete"
                break
            status = "uncertain"
        except Exception as error:
            failed_attempt = {
                "attempt": attempt_index + 1,
                "error_type": type(error).__name__, "error": str(error),
            }
            if raw is not None:
                failed_attempt["raw_response"] = raw
            attempts.append(failed_attempt)
        if attempt_index + 1 < max_attempts and not fixture:
            time.sleep(2 ** attempt_index)
    artifact = {
        "id": item["id"], "pass": pass_name, "status": status,
        "question_hash": question_hash(item["question"]),
        "prompt_version": VALIDITY_PROMPT_VERSION if is_validity else ANSWER_PROMPT_VERSION,
        "model": model, "attempts": attempts, "result": final,
    }
    atomic_json(destination, artifact)
    return artifact


def run_many(
    items: list[dict[str, str]], pass_name: str, artifact_dir: Path, model: str,
    concurrency: int, max_attempts: int, min_verified_confidence: float,
    reasoning_effort: str, max_output_tokens: int, fixture: Path | None,
) -> list[dict[str, Any]]:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    results = []
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {
            executor.submit(
                run_one, item, pass_name, artifact_dir / f"{item['id']}.json", model,
                max_attempts, min_verified_confidence, reasoning_effort, max_output_tokens, fixture,
            ): item for item in items
        }
        for future in as_completed(futures):
            results.append(future.result())
    return sorted(results, key=lambda row: row["id"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True, help="terra_blind_input.jsonl")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model", default="gpt-5.6")
    parser.add_argument("--reasoning-effort", choices=("low", "medium", "high"), default="high")
    parser.add_argument("--max-output-tokens", type=int, default=16384)
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--min-verified-confidence", type=float, default=0.8)
    parser.add_argument("--validity-fixture", type=Path)
    parser.add_argument("--answer-fixture", type=Path)
    args = parser.parse_args()
    if not args.validity_fixture and not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is required for live annotation")
    if not 0 <= args.min_verified_confidence <= 1:
        raise ValueError("min-verified-confidence must be in [0, 1]")

    items = read_jsonl(args.input)
    if any(set(item) != {"id", "question"} for item in items):
        raise ValueError("blind input rows must contain exactly id and question")
    validity = run_many(
        items, "validity", args.output_dir / "artifacts" / "validity", args.model,
        args.concurrency, args.max_attempts, args.min_verified_confidence,
        args.reasoning_effort, args.max_output_tokens, args.validity_fixture,
    )
    item_by_id = {item["id"]: item for item in items}
    valid_items = [
        item_by_id[row["id"]] for row in validity
        if row["status"] == "complete" and row["result"]["label"] == "A"
    ]
    answers = run_many(
        valid_items, "answer", args.output_dir / "artifacts" / "answer", args.model,
        args.concurrency, args.max_attempts, args.min_verified_confidence,
        args.reasoning_effort, args.max_output_tokens, args.answer_fixture,
    )
    answer_by_id = {row["id"]: row for row in answers}
    combined = [{
        "id": row["id"], "validity_pass": row,
        "answer_pass": answer_by_id.get(row["id"]),
    } for row in validity]
    write_jsonl(args.output_dir / "terra_raw_results.jsonl", combined)
    atomic_json(args.output_dir / "annotation_manifest.json", {
        "model": args.model, "reasoning_effort": args.reasoning_effort,
        "max_output_tokens": args.max_output_tokens, "max_attempts": args.max_attempts,
        "min_verified_confidence": args.min_verified_confidence,
        "validity_prompt_version": VALIDITY_PROMPT_VERSION,
        "validity_prompt_sha256": prompt_hash(VALIDITY_SYSTEM_PROMPT),
        "validity_system_prompt": VALIDITY_SYSTEM_PROMPT,
        "answer_prompt_version": ANSWER_PROMPT_VERSION,
        "answer_prompt_sha256": prompt_hash(ANSWER_SYSTEM_PROMPT),
        "answer_system_prompt": ANSWER_SYSTEM_PROMPT,
        "input_count": len(items), "answer_pass_input_count": len(valid_items),
    })


if __name__ == "__main__":
    main()
