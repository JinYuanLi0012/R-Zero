#!/usr/bin/env python3
"""Resumable Batch judge for majority-answer correctness."""
from __future__ import annotations

import hashlib
import json
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


METHOD_DIR = Path(__file__).resolve().parent
TERRA_DIR = METHOD_DIR.parent / "validity_rl_terra_dataset"
sys.path.insert(0, str(TERRA_DIR))

from batch_annotate import (
    download_file, extract_output_text, load_state, read_lines_if_present,
    submit_record, wait_for_batch,
)
from common import atomic_json, prompt_hash, question_hash, write_jsonl


PROMPT_VERSION = "clean-formal-majority-answer-judge-v1"
SYSTEM_PROMPT = """You are a mathematical answer-equivalence judge.
You receive an opaque question ID, a question, an independently solved and verified canonical answer,
and the majority answer produced by another solver population. Judge the majority answer against the
question and canonical answer by mathematical meaning, not string equality. Equivalent algebraic forms,
units, complete sets, and proof-style requests require semantic comparison. A correct number with missing
required proof, cases, constructions, or explanation can be INCOMPLETE. Do not assume the majority answer
is correct merely because it received multiple votes. Do not revisit question validity unless the supplied
information makes comparison genuinely impossible. Keep reasoning_summary concise and identify the
decisive agreement or discrepancy.

Use CORRECT only when the majority answer fully and correctly answers the question. Use INCORRECT for a
mathematically wrong answer, INCOMPLETE for a materially incomplete answer, NOT_RESPONSIVE for text that
does not answer the request, and UNABLE_TO_VERIFY only when a reliable comparison cannot be made."""

STATUSES = ["CORRECT", "INCORRECT", "INCOMPLETE", "NOT_RESPONSIVE", "UNABLE_TO_VERIFY"]
SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "majority_answer_status": {"type": "string", "enum": STATUSES},
        "mathematically_equivalent": {"type": ["boolean", "null"]},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "reasoning_summary": {"type": "string"},
    },
    "required": [
        "majority_answer_status", "mathematically_equivalent", "confidence",
        "reasoning_summary",
    ],
    "additionalProperties": False,
}


def value_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def validate_result(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != set(SCHEMA["required"]):
        raise ValueError("majority judge response has missing or extra fields")
    status = value["majority_answer_status"]
    equivalent = value["mathematically_equivalent"]
    confidence = value["confidence"]
    if status not in STATUSES:
        raise ValueError("invalid majority_answer_status")
    if not isinstance(equivalent, (bool, type(None))):
        raise ValueError("mathematically_equivalent must be boolean or null")
    if status == "CORRECT" and equivalent is not True:
        raise ValueError("CORRECT requires mathematically_equivalent=true")
    if status in {"INCORRECT", "INCOMPLETE", "NOT_RESPONSIVE"} and equivalent is not False:
        raise ValueError(f"{status} requires mathematically_equivalent=false")
    if status == "UNABLE_TO_VERIFY" and equivalent is not None:
        raise ValueError("UNABLE_TO_VERIFY requires mathematically_equivalent=null")
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
        raise ValueError("confidence must be numeric")
    if not 0 <= float(confidence) <= 1:
        raise ValueError("confidence must be in [0, 1]")
    if not isinstance(value["reasoning_summary"], str):
        raise ValueError("reasoning_summary must be a string")
    return value


def request_body(
    item: dict[str, str], model: str, reasoning_effort: str, max_output_tokens: int,
) -> dict[str, Any]:
    payload = {
        "id": item["id"], "question": item["question"],
        "canonical_final_answer": item["canonical_final_answer"],
        "majority_answer": item["majority_answer"],
    }
    return {
        "model": model,
        "input": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ],
        "reasoning": {"effort": reasoning_effort},
        "max_output_tokens": max_output_tokens,
        "text": {"format": {
            "type": "json_schema", "name": "rzero_majority_answer_judge",
            "strict": True, "schema": SCHEMA,
        }},
    }


def make_batch_row(
    item: dict[str, str], attempt: int, model: str,
    reasoning_effort: str, max_output_tokens: int,
) -> dict[str, Any]:
    return {
        "custom_id": f"majority:{item['id']}:a{attempt}",
        "method": "POST", "url": "/v1/responses",
        "body": request_body(item, model, reasoning_effort, max_output_tokens),
    }


def item_hashes(item: dict[str, str]) -> dict[str, str]:
    return {
        "question": question_hash(item["question"]),
        "canonical": value_hash(item["canonical_final_answer"]),
        "majority": value_hash(item["majority_answer"]),
    }


def state_config(
    items: list[dict[str, str]], model: str, reasoning_effort: str,
    max_output_tokens: int, max_attempts: int, confidence_threshold: float,
) -> dict[str, Any]:
    return {
        "pass": "majority", "model": model, "reasoning_effort": reasoning_effort,
        "max_output_tokens": max_output_tokens, "max_attempts": max_attempts,
        "confidence_threshold": confidence_threshold,
        "prompt_version": PROMPT_VERSION, "prompt_sha256": prompt_hash(SYSTEM_PROMPT),
        "item_hashes": {
            item["id"]: item_hashes(item) for item in sorted(items, key=lambda row: row["id"])
        },
    }


def artifact_status(
    attempts: list[dict[str, Any]], confidence_threshold: float,
) -> tuple[str, dict[str, Any] | None]:
    parsed = [attempt["parsed"] for attempt in attempts if "parsed" in attempt]
    if not parsed:
        return "failed", None
    result = parsed[-1]
    if (
        result["majority_answer_status"] != "UNABLE_TO_VERIFY"
        and result["confidence"] >= confidence_threshold
    ):
        return "complete", result
    return "uncertain", result


def artifact_for(
    item: dict[str, str], model: str, attempts: list[dict[str, Any]],
    confidence_threshold: float,
) -> dict[str, Any]:
    status, result = artifact_status(attempts, confidence_threshold)
    return {
        "id": item["id"], "pass": "majority", "status": status,
        "model": model, "prompt_version": PROMPT_VERSION,
        "input_hashes": item_hashes(item), "attempts": attempts, "result": result,
    }


def validate_cached(artifact: dict[str, Any], item: dict[str, str], model: str) -> None:
    if (
        artifact.get("id") != item["id"] or artifact.get("pass") != "majority"
        or artifact.get("model") != model or artifact.get("prompt_version") != PROMPT_VERSION
        or artifact.get("input_hashes") != item_hashes(item)
    ):
        raise RuntimeError(f"cached majority artifact mismatch for {item['id']}")


def sync_api_call(
    item: dict[str, str], model: str, reasoning_effort: str, max_output_tokens: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Call the Responses API directly for one majority comparison."""
    from openai import OpenAI

    response = OpenAI().responses.create(
        **request_body(item, model, reasoning_effort, max_output_tokens)
    )
    raw = response.model_dump(mode="json")
    return validate_result(json.loads(response.output_text)), raw


def run_one_sync(
    item: dict[str, str], destination: Path, model: str, reasoning_effort: str,
    max_output_tokens: int, max_attempts: int, confidence_threshold: float,
) -> dict[str, Any]:
    attempts: list[dict[str, Any]] = []
    if destination.is_file():
        existing = json.loads(destination.read_text(encoding="utf-8"))
        validate_cached(existing, item, model)
        if existing.get("status") == "complete" or len(existing.get("attempts", [])) >= max_attempts:
            return existing
        attempts = list(existing.get("attempts", []))

    while len(attempts) < max_attempts:
        attempt_number = len(attempts) + 1
        raw = None
        try:
            parsed, raw = sync_api_call(item, model, reasoning_effort, max_output_tokens)
            attempts.append({
                "attempt": attempt_number, "parsed": parsed, "raw_response": raw,
            })
        except Exception as error:
            failed_attempt: dict[str, Any] = {
                "attempt": attempt_number, "error_type": type(error).__name__,
                "error": str(error),
            }
            if raw is not None:
                failed_attempt["raw_response"] = raw
            attempts.append(failed_attempt)

        artifact = artifact_for(item, model, attempts, confidence_threshold)
        atomic_json(destination, artifact)
        if artifact["status"] == "complete":
            return artifact
        if len(attempts) < max_attempts:
            time.sleep(2 ** (attempt_number - 1))
    return artifact_for(item, model, attempts, confidence_threshold)


def run_majority_pass_sync(
    items: list[dict[str, str]], output_dir: Path, model: str,
    reasoning_effort: str, max_output_tokens: int, max_attempts: int,
    confidence_threshold: float, concurrency: int,
) -> list[dict[str, Any]]:
    artifact_dir = output_dir / "artifacts" / "majority"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    if len({item["id"] for item in items}) != len(items):
        raise ValueError("majority inputs contain duplicate IDs")

    total = len(items)
    report_every = max(1, total // 100)
    print(
        f"[terra:majority] starting {total} questions with concurrency={concurrency}",
        flush=True,
    )
    if total == 0:
        print("[terra:majority] complete: 0/0", flush=True)
        return []

    results: list[dict[str, Any]] = []
    status_counts = {"complete": 0, "uncertain": 0, "failed": 0}
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {
            executor.submit(
                run_one_sync, item, artifact_dir / f"{item['id']}.json", model,
                reasoning_effort, max_output_tokens, max_attempts, confidence_threshold,
            ): item
            for item in items
        }
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            status_counts[result["status"]] = status_counts.get(result["status"], 0) + 1
            completed = len(results)
            if completed == total or completed % report_every == 0:
                print(
                    f"[terra:majority] {completed}/{total} ({completed / total:.0%}) "
                    f"complete={status_counts['complete']} "
                    f"uncertain={status_counts['uncertain']} failed={status_counts['failed']}",
                    flush=True,
                )
    return sorted(results, key=lambda row: row["id"])


def pending_items(
    items: list[dict[str, str]], artifact_dir: Path, model: str, max_attempts: int,
) -> list[tuple[dict[str, str], int]]:
    pending = []
    for item in items:
        destination = artifact_dir / f"{item['id']}.json"
        if not destination.is_file():
            pending.append((item, 1))
            continue
        artifact = json.loads(destination.read_text(encoding="utf-8"))
        validate_cached(artifact, item, model)
        if artifact["status"] == "complete":
            continue
        attempt = len(artifact["attempts"]) + 1
        if attempt <= max_attempts:
            pending.append((item, attempt))
    return pending


def create_record(
    pending: list[tuple[dict[str, str], int]], pass_dir: Path, sequence: int,
    model: str, reasoning_effort: str, max_output_tokens: int,
) -> dict[str, Any]:
    rows = [
        make_batch_row(item, attempt, model, reasoning_effort, max_output_tokens)
        for item, attempt in pending
    ]
    input_path = pass_dir / f"input_{sequence:02d}.jsonl"
    write_jsonl(input_path, rows)
    if input_path.stat().st_size > 200 * 1024 * 1024:
        raise RuntimeError(f"batch input exceeds 200 MB: {input_path}")
    return {
        "sequence": sequence, "input_path": str(input_path),
        "output_path": str(pass_dir / f"output_{sequence:02d}.jsonl"),
        "error_path": str(pass_dir / f"errors_{sequence:02d}.jsonl"),
        "custom_ids": [row["custom_id"] for row in rows],
        "input_file_id": None, "batch_id": None, "processed_at_utc": None,
    }


def process_record(
    record: dict[str, Any], items_by_id: dict[str, dict[str, str]],
    artifact_dir: Path, model: str, confidence_threshold: float,
) -> None:
    outputs = {
        row["custom_id"]: row for row in read_lines_if_present(Path(record["output_path"]))
    }
    errors = {
        row["custom_id"]: row for row in read_lines_if_present(Path(record["error_path"]))
    }
    for custom_id in record["custom_ids"]:
        _, item_id, attempt_text = custom_id.split(":")
        attempt_number = int(attempt_text.removeprefix("a"))
        item = items_by_id[item_id]
        destination = artifact_dir / f"{item_id}.json"
        existing = json.loads(destination.read_text(encoding="utf-8")) if destination.is_file() else None
        if existing:
            validate_cached(existing, item, model)
            attempts = existing["attempts"]
            if any(attempt.get("batch_custom_id") == custom_id for attempt in attempts):
                continue
        else:
            attempts = []
        if custom_id in outputs:
            raw_line = outputs[custom_id]
            try:
                response = raw_line.get("response")
                if not isinstance(response, dict) or response.get("status_code") != 200:
                    raise ValueError(f"batch request did not return HTTP 200: {response}")
                body = response.get("body")
                if not isinstance(body, dict):
                    raise ValueError("batch response is missing a response body")
                parsed = validate_result(json.loads(extract_output_text(body)))
                attempt = {
                    "attempt": attempt_number, "batch_custom_id": custom_id,
                    "parsed": parsed, "raw_response": body, "batch_result": raw_line,
                }
            except Exception as error:
                attempt = {
                    "attempt": attempt_number, "batch_custom_id": custom_id,
                    "error_type": type(error).__name__, "error": str(error),
                    "batch_result": raw_line,
                }
        else:
            raw_line = errors.get(custom_id)
            attempt = {
                "attempt": attempt_number, "batch_custom_id": custom_id,
                "error_type": "BatchRequestError",
                "error": str(raw_line.get("error") if raw_line else "missing from batch files"),
                "batch_result": raw_line,
            }
        attempts.append(attempt)
        attempts.sort(key=lambda value: int(value["attempt"]))
        atomic_json(destination, artifact_for(item, model, attempts, confidence_threshold))


def run_majority_pass(
    client: Any, items: list[dict[str, str]], output_dir: Path, model: str,
    reasoning_effort: str, max_output_tokens: int, max_attempts: int,
    confidence_threshold: float, poll_seconds: int,
) -> list[dict[str, Any]]:
    pass_dir = output_dir / "batch" / "majority"
    artifact_dir = output_dir / "artifacts" / "majority"
    pass_dir.mkdir(parents=True, exist_ok=True)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    config = state_config(
        items, model, reasoning_effort, max_output_tokens, max_attempts,
        confidence_threshold,
    )
    state_path = pass_dir / "state.json"
    state = load_state(state_path, config)
    items_by_id = {item["id"]: item for item in items}
    if len(items_by_id) != len(items):
        raise ValueError("majority inputs contain duplicate IDs")

    while True:
        active = next((row for row in state["batches"] if not row["processed_at_utc"]), None)
        if active is None:
            pending = pending_items(items, artifact_dir, model, max_attempts)
            if not pending:
                break
            active = create_record(
                pending, pass_dir, len(state["batches"]) + 1,
                model, reasoning_effort, max_output_tokens,
            )
            state["batches"].append(active)
            atomic_json(state_path, state)
        submit_record(client, active, state, state_path)
        snapshot = wait_for_batch(client, active, state, state_path, poll_seconds)
        if snapshot["status"] in {"failed", "cancelled"}:
            raise RuntimeError(
                f"batch {active['batch_id']} ended with status={snapshot['status']}: "
                f"{snapshot.get('errors')}"
            )
        download_file(client, snapshot.get("output_file_id"), Path(active["output_path"]))
        download_file(client, snapshot.get("error_file_id"), Path(active["error_path"]))
        process_record(active, items_by_id, artifact_dir, model, confidence_threshold)
        active["processed_at_utc"] = datetime.now(timezone.utc).isoformat()
        active["terminal_status"] = snapshot["status"]
        active["output_file_id"] = snapshot.get("output_file_id")
        active["error_file_id"] = snapshot.get("error_file_id")
        atomic_json(state_path, state)

    results = []
    for item in items:
        artifact = json.loads(
            (artifact_dir / f"{item['id']}.json").read_text(encoding="utf-8")
        )
        validate_cached(artifact, item, model)
        results.append(artifact)
    print(
        f"[batch:majority] complete: total={len(results)} "
        f"statuses={dict(Counter(row['status'] for row in results))}",
        flush=True,
    )
    return sorted(results, key=lambda row: row["id"])
