#!/usr/bin/env python3
"""Blind GPT reference judging with resumable per-question artifacts."""

from __future__ import annotations

import argparse
import csv
import json
import os
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from common import atomic_json, read_jsonl, stable_int, write_jsonl


LABELS = ["A", "B", "C", "D", "E", "F"]
JUDGE_SCHEMA = {
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
    },
    "required": [
        "goal_restatement", "conditions_complete", "contradictory",
        "multiple_reasonable_interpretations", "solution_exists",
        "unique_or_explicit_grading", "label", "confidence", "issue_types",
        "reasoning_summary", "derived_answer",
    ],
    "additionalProperties": False,
}

SYSTEM_PROMPT = """You are a careful reference judge for generated mathematical and reasoning questions.
You see only the question. Restate its goal, inspect every definition and condition, check for
contradictions and multiple reasonable interpretations, and genuinely attempt a solution. Then classify:
A = self-contained, valid, solvable, and uniquely gradable;
B = meaningful but open-ended or not precisely gradable;
C = missing conditions, multiple answers, or key ambiguity;
D = contradictory or has no solution;
E = malformed, undefined, garbled, or unintelligible;
F = you cannot judge reliably.
Use A only when all strict requirements hold. Keep the reasoning summary concise but concrete."""


def label_consistent(result: dict) -> bool:
    if result["label"] == "A":
        return bool(
            result["conditions_complete"] and not result["contradictory"]
            and not result["multiple_reasonable_interpretations"]
            and result["solution_exists"] and result["unique_or_explicit_grading"]
        )
    if result["label"] == "D":
        return bool(result["contradictory"] or not result["solution_exists"])
    return True


def validate_result(value: dict) -> dict:
    if set(value) != set(JUDGE_SCHEMA["required"]):
        raise ValueError("Judge result has missing or extra fields")
    if value["label"] not in LABELS or not 0 <= float(value["confidence"]) <= 1:
        raise ValueError("Judge returned an invalid label or confidence")
    return value


def call_api(model: str, opaque_id: str, question: str) -> dict:
    from openai import OpenAI

    client = OpenAI()
    response = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Question ID: {opaque_id}\n\n{question}"},
        ],
        text={
            "format": {
                "type": "json_schema", "name": "question_quality_judgment",
                "strict": True, "schema": JUDGE_SCHEMA,
            }
        },
    )
    return validate_result(json.loads(response.output_text))


def load_fixture(path: Path, opaque_id: str) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    value = payload.get(opaque_id, payload.get("default"))
    if value is None:
        raise KeyError(f"fixture has no response for {opaque_id}")
    if "output_text" in value:
        value = json.loads(value["output_text"])
    return validate_result(value)


def judge_one(model: str, item: dict, result_dir: Path, fixture: Path | None) -> dict:
    destination = result_dir / f"{item['opaque_judge_id']}.json"
    if destination.is_file():
        return json.loads(destination.read_text(encoding="utf-8"))
    last_error = None
    for attempt in range(3):
        try:
            result = (
                load_fixture(fixture, item["opaque_judge_id"])
                if fixture else call_api(model, item["opaque_judge_id"], item["question"])
            )
            artifact = {
                "opaque_judge_id": item["opaque_judge_id"],
                "question_hash": item["question_hash"],
                **result,
                "structured_consistent": label_consistent(result),
            }
            atomic_json(destination, artifact)
            return artifact
        except Exception as error:  # API errors and malformed responses use the same bounded retry.
            last_error = error
            status = getattr(error, "status_code", None)
            if attempt == 2 or (status is not None and status != 429 and status < 500):
                break
            time.sleep(2 ** attempt)
    raise RuntimeError(f"Judge failed for {item['opaque_judge_id']}: {last_error}")


def run_pass(items: list[dict], model: str, concurrency: int, directory: Path, fixture: Path | None) -> list[dict]:
    directory.mkdir(parents=True, exist_ok=True)
    results = []
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {
            executor.submit(judge_one, model, item, directory, fixture): item
            for item in items
        }
        for future in as_completed(futures):
            results.append(future.result())
    return sorted(results, key=lambda row: row["opaque_judge_id"])


def stratified_human_sample(rows: list[dict], size: int, seed: int) -> list[dict]:
    groups: dict[tuple[int, str], list[dict]] = {}
    for row in rows:
        groups.setdefault((row["round"], row["label"]), []).append(row)
    for key, values in groups.items():
        random.Random(stable_int(seed, "human", *key)).shuffle(values)
    selected = []
    keys = sorted(groups)
    while len(selected) < min(size, len(rows)):
        progressed = False
        for key in keys:
            if groups[key] and len(selected) < size:
                selected.append(groups[key].pop())
                progressed = True
        if not progressed:
            break
    return selected


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model", default="gpt-5.6-terra")
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--human-review-size", type=int, default=75)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--fixture", type=Path)
    args = parser.parse_args()
    if not args.fixture and not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is required for live judging")

    source_rows = read_jsonl(args.input)
    by_hash = {}
    for row in source_rows:
        by_hash.setdefault(row["question_hash"], row)
    blind = [
        {
            "opaque_judge_id": f"j_{stable_int(args.seed, 'judge', digest):016x}",
            "question_hash": digest,
            "question": row["question"],
        }
        for digest, row in sorted(by_hash.items())
    ]
    write_jsonl(args.output_dir / "blind_input.jsonl", [
        {"opaque_judge_id": row["opaque_judge_id"], "question": row["question"]} for row in blind
    ])
    write_jsonl(args.output_dir / "private_mapping.jsonl", blind)
    judgments = run_pass(blind, args.model, args.concurrency, args.output_dir / "results", args.fixture)
    judgment_by_hash = {row["question_hash"]: row for row in judgments}

    combined = []
    for source in source_rows:
        judgment = judgment_by_hash[source["question_hash"]]
        combined.append(
            {
                "question_id": source["question_id"], "question_hash": source["question_hash"],
                "round": source["round"], "opaque_judge_id": judgment["opaque_judge_id"],
                "label": judgment["label"], "confidence": judgment["confidence"],
                "valid": judgment["label"] == "A", "judgment": judgment,
            }
        )
    write_jsonl(args.output_dir / "judge_results.jsonl", combined)
    human = stratified_human_sample(combined, args.human_review_size, args.seed)
    human_blind = []
    human_key = []
    source_by_id = {row["question_id"]: row for row in source_rows}
    for index, row in enumerate(human):
        review_id = f"h_{index + 1:03d}"
        human_blind.append(
            {"human_review_id": review_id, "question": source_by_id[row["question_id"]]["question"],
             "human_label": "", "human_notes": ""}
        )
        human_key.append({"human_review_id": review_id, "question_id": row["question_id"]})
    write_jsonl(args.output_dir / "human_review_blind.jsonl", human_blind)
    write_jsonl(args.output_dir / "human_review_private_key.jsonl", human_key)
    with (args.output_dir / "human_review_blind.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["human_review_id", "question", "human_label", "human_notes"]
        )
        writer.writeheader()
        writer.writerows(human_blind)
    atomic_json(
        args.output_dir / "judge_manifest.json",
        {"model": args.model, "unique_questions": len(blind), "row_count": len(source_rows),
         "api_calls_per_unique_question": 1, "human_review_count": len(human)},
    )


if __name__ == "__main__":
    main()
