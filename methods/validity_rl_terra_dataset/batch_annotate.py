#!/usr/bin/env python3
"""Run blind two-pass annotations through the discounted OpenAI Batch API."""
from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from annotate import (
    ANSWER_PROMPT_VERSION,
    ANSWER_SCHEMA,
    ANSWER_SYSTEM_PROMPT,
    VALIDITY_PROMPT_VERSION,
    VALIDITY_SCHEMA,
    VALIDITY_SYSTEM_PROMPT,
    validate_exact,
)
from common import atomic_json, prompt_hash, question_hash, read_jsonl, write_jsonl


TERMINAL_STATUSES = {"completed", "failed", "expired", "cancelled"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def model_dump(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    raise TypeError(f"cannot serialize {type(value).__name__}")


def pass_settings(pass_name: str) -> tuple[str, str, dict[str, Any], str]:
    if pass_name == "validity":
        return (
            VALIDITY_SYSTEM_PROMPT, VALIDITY_PROMPT_VERSION,
            VALIDITY_SCHEMA, "rzero_question_validity",
        )
    if pass_name == "answer":
        return (
            ANSWER_SYSTEM_PROMPT, ANSWER_PROMPT_VERSION,
            ANSWER_SCHEMA, "rzero_canonical_answer",
        )
    raise ValueError(f"unknown pass: {pass_name}")


def request_body(
    item: dict[str, str], pass_name: str, model: str,
    reasoning_effort: str, max_output_tokens: int,
) -> dict[str, Any]:
    prompt, _, schema, schema_name = pass_settings(pass_name)
    return {
        "model": model,
        "input": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Question ID: {item['id']}\n\n{item['question']}"},
        ],
        "reasoning": {"effort": reasoning_effort},
        "max_output_tokens": max_output_tokens,
        "text": {
            "format": {
                "type": "json_schema", "name": schema_name,
                "strict": True, "schema": schema,
            }
        },
    }


def make_batch_row(
    item: dict[str, str], pass_name: str, attempt: int, model: str,
    reasoning_effort: str, max_output_tokens: int,
) -> dict[str, Any]:
    return {
        "custom_id": f"{pass_name}:{item['id']}:a{attempt}",
        "method": "POST",
        "url": "/v1/responses",
        "body": request_body(item, pass_name, model, reasoning_effort, max_output_tokens),
    }


def extract_output_text(response_body: dict[str, Any]) -> str:
    if isinstance(response_body.get("output_text"), str):
        return response_body["output_text"]
    chunks = []
    for output_item in response_body.get("output", []):
        if output_item.get("type") != "message":
            continue
        for content in output_item.get("content", []):
            if content.get("type") == "output_text" and isinstance(content.get("text"), str):
                chunks.append(content["text"])
    if not chunks:
        raise ValueError("Responses body has no output_text content")
    return "".join(chunks)


def validate_batch_success(line: dict[str, Any], pass_name: str) -> tuple[dict[str, Any], dict[str, Any]]:
    response = line.get("response")
    if not isinstance(response, dict) or response.get("status_code") != 200:
        raise ValueError(f"batch request did not return HTTP 200: {response}")
    body = response.get("body")
    if not isinstance(body, dict):
        raise ValueError("batch response is missing a response body")
    _, _, schema, _ = pass_settings(pass_name)
    parsed = validate_exact(json.loads(extract_output_text(body)), schema, pass_name)
    return parsed, body


def artifact_status(
    pass_name: str, attempts: list[dict[str, Any]], min_verified_confidence: float,
) -> tuple[str, dict[str, Any] | None]:
    parsed_attempts = [attempt["parsed"] for attempt in attempts if "parsed" in attempt]
    if not parsed_attempts:
        return "failed", None
    result = parsed_attempts[-1]
    if pass_name == "validity":
        return "complete", result
    if result["answer_verified"] and result["confidence"] >= min_verified_confidence:
        return "complete", result
    return "uncertain", result


def artifact_for(
    item: dict[str, str], pass_name: str, model: str,
    attempts: list[dict[str, Any]], min_verified_confidence: float,
) -> dict[str, Any]:
    _, prompt_version, _, _ = pass_settings(pass_name)
    status, result = artifact_status(pass_name, attempts, min_verified_confidence)
    return {
        "id": item["id"], "pass": pass_name, "status": status,
        "question_hash": question_hash(item["question"]),
        "prompt_version": prompt_version, "model": model,
        "attempts": attempts, "result": result,
    }


def validate_cached_artifact(
    artifact: dict[str, Any], item: dict[str, str], pass_name: str, model: str,
) -> None:
    _, prompt_version, _, _ = pass_settings(pass_name)
    if (
        artifact.get("id") != item["id"] or artifact.get("pass") != pass_name
        or artifact.get("model") != model or artifact.get("prompt_version") != prompt_version
        or artifact.get("question_hash") != question_hash(item["question"])
    ):
        raise RuntimeError(f"cached {pass_name} artifact configuration mismatch for {item['id']}")


def read_lines_if_present(path: Path) -> list[dict[str, Any]]:
    return read_jsonl(path) if path.is_file() else []


def response_content_text(response: Any) -> str:
    content = getattr(response, "content", None)
    if isinstance(content, bytes):
        return content.decode("utf-8")
    if isinstance(content, str):
        return content
    text = getattr(response, "text", None)
    if callable(text):
        text = text()
    if isinstance(text, str):
        return text
    if hasattr(response, "read"):
        value = response.read()
        return value.decode("utf-8") if isinstance(value, bytes) else str(value)
    raise TypeError("OpenAI file content response has no readable text")


def download_file(client: Any, file_id: str | None, destination: Path) -> None:
    if not file_id or destination.is_file():
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    text = response_content_text(client.files.content(file_id))
    temporary = destination.with_name(f"{destination.name}.tmp-{os.getpid()}")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, destination)


def state_config(
    items: list[dict[str, str]], pass_name: str, model: str,
    reasoning_effort: str, max_output_tokens: int, max_attempts: int,
    min_verified_confidence: float,
) -> dict[str, Any]:
    prompt, prompt_version, _, _ = pass_settings(pass_name)
    return {
        "pass": pass_name, "model": model, "reasoning_effort": reasoning_effort,
        "max_output_tokens": max_output_tokens, "max_attempts": max_attempts,
        "min_verified_confidence": min_verified_confidence,
        "prompt_version": prompt_version, "prompt_sha256": prompt_hash(prompt),
        "item_question_hashes": {
            item["id"]: question_hash(item["question"]) for item in sorted(items, key=lambda row: row["id"])
        },
    }


def load_state(path: Path, config: dict[str, Any]) -> dict[str, Any]:
    if path.is_file():
        state = json.loads(path.read_text(encoding="utf-8"))
        if state.get("config") != config:
            raise RuntimeError(f"cached batch state configuration mismatch: {path}")
        return state
    state = {"config": config, "batches": []}
    atomic_json(path, state)
    return state


def submit_record(client: Any, record: dict[str, Any], state: dict[str, Any], state_path: Path) -> None:
    input_path = Path(record["input_path"])
    if not record.get("input_file_id"):
        print(f"[batch:{state['config']['pass']}] uploading {input_path.name}", flush=True)
        with input_path.open("rb") as handle:
            uploaded = client.files.create(file=handle, purpose="batch")
        record["input_file_id"] = uploaded.id
        atomic_json(state_path, state)
    if not record.get("batch_id"):
        batch = client.batches.create(
            input_file_id=record["input_file_id"], endpoint="/v1/responses",
            completion_window="24h",
            metadata={
                "experiment": "rzero-validity-rl",
                "pass": state["config"]["pass"],
                "sequence": str(record["sequence"]),
            },
        )
        record["batch_id"] = batch.id
        record["submitted_at_utc"] = utc_now()
        record["last_batch_snapshot"] = model_dump(batch)
        atomic_json(state_path, state)
        print(
            f"[batch:{state['config']['pass']}] submitted {batch.id} "
            f"requests={len(record['custom_ids'])}",
            flush=True,
        )


def wait_for_batch(
    client: Any, record: dict[str, Any], state: dict[str, Any],
    state_path: Path, poll_seconds: int,
) -> dict[str, Any]:
    while True:
        batch = client.batches.retrieve(record["batch_id"])
        snapshot = model_dump(batch)
        record["last_batch_snapshot"] = snapshot
        atomic_json(state_path, state)
        counts = snapshot.get("request_counts") or {}
        print(
            f"[batch:{state['config']['pass']}] id={record['batch_id']} "
            f"status={snapshot.get('status')} completed={counts.get('completed', 0)}/"
            f"{counts.get('total', len(record['custom_ids']))} failed={counts.get('failed', 0)}",
            flush=True,
        )
        if snapshot.get("status") in TERMINAL_STATUSES:
            return snapshot
        time.sleep(poll_seconds)


def process_record(
    record: dict[str, Any], items_by_id: dict[str, dict[str, str]], pass_name: str,
    model: str, artifact_dir: Path, min_verified_confidence: float,
) -> None:
    output_by_custom_id = {
        row["custom_id"]: row for row in read_lines_if_present(Path(record["output_path"]))
    }
    error_by_custom_id = {
        row["custom_id"]: row for row in read_lines_if_present(Path(record["error_path"]))
    }
    for custom_id in record["custom_ids"]:
        _, item_id, attempt_text = custom_id.split(":")
        attempt_number = int(attempt_text.removeprefix("a"))
        item = items_by_id[item_id]
        destination = artifact_dir / f"{item_id}.json"
        existing = json.loads(destination.read_text(encoding="utf-8")) if destination.is_file() else None
        if existing:
            validate_cached_artifact(existing, item, pass_name, model)
            attempts = existing["attempts"]
            if any(attempt.get("batch_custom_id") == custom_id for attempt in attempts):
                continue
        else:
            attempts = []
        if custom_id in output_by_custom_id:
            raw_line = output_by_custom_id[custom_id]
            try:
                parsed, raw_response = validate_batch_success(raw_line, pass_name)
                attempt = {
                    "attempt": attempt_number, "batch_custom_id": custom_id,
                    "parsed": parsed, "raw_response": raw_response,
                    "batch_result": raw_line,
                }
            except Exception as error:
                attempt = {
                    "attempt": attempt_number, "batch_custom_id": custom_id,
                    "error_type": type(error).__name__, "error": str(error),
                    "batch_result": raw_line,
                }
        else:
            raw_line = error_by_custom_id.get(custom_id)
            attempt = {
                "attempt": attempt_number, "batch_custom_id": custom_id,
                "error_type": "BatchRequestError",
                "error": str(raw_line.get("error") if raw_line else "missing from batch output and error files"),
                "batch_result": raw_line,
            }
        attempts.append(attempt)
        attempts.sort(key=lambda value: int(value["attempt"]))
        atomic_json(
            destination,
            artifact_for(item, pass_name, model, attempts, min_verified_confidence),
        )


def pending_items(
    items: list[dict[str, str]], pass_name: str, model: str,
    artifact_dir: Path, max_attempts: int,
) -> list[tuple[dict[str, str], int]]:
    pending = []
    for item in items:
        destination = artifact_dir / f"{item['id']}.json"
        if not destination.is_file():
            pending.append((item, 1))
            continue
        artifact = json.loads(destination.read_text(encoding="utf-8"))
        validate_cached_artifact(artifact, item, pass_name, model)
        if artifact["status"] == "complete":
            continue
        next_attempt = len(artifact["attempts"]) + 1
        if next_attempt <= max_attempts:
            pending.append((item, next_attempt))
    return pending


def create_record(
    pending: list[tuple[dict[str, str], int]], pass_name: str, model: str,
    reasoning_effort: str, max_output_tokens: int, pass_dir: Path, sequence: int,
) -> dict[str, Any]:
    rows = [
        make_batch_row(item, pass_name, attempt, model, reasoning_effort, max_output_tokens)
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


def run_batch_pass(
    client: Any, items: list[dict[str, str]], pass_name: str, output_dir: Path,
    model: str, reasoning_effort: str, max_output_tokens: int, max_attempts: int,
    min_verified_confidence: float, poll_seconds: int,
) -> list[dict[str, Any]]:
    pass_dir = output_dir / "batch" / pass_name
    artifact_dir = output_dir / "artifacts" / pass_name
    pass_dir.mkdir(parents=True, exist_ok=True)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    config = state_config(
        items, pass_name, model, reasoning_effort, max_output_tokens,
        max_attempts, min_verified_confidence,
    )
    state_path = pass_dir / "state.json"
    state = load_state(state_path, config)
    items_by_id = {item["id"]: item for item in items}

    while True:
        active = next((record for record in state["batches"] if not record["processed_at_utc"]), None)
        if active is None:
            pending = pending_items(items, pass_name, model, artifact_dir, max_attempts)
            if not pending:
                break
            active = create_record(
                pending, pass_name, model, reasoning_effort, max_output_tokens,
                pass_dir, len(state["batches"]) + 1,
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
        process_record(active, items_by_id, pass_name, model, artifact_dir, min_verified_confidence)
        active["processed_at_utc"] = utc_now()
        active["terminal_status"] = snapshot["status"]
        active["output_file_id"] = snapshot.get("output_file_id")
        active["error_file_id"] = snapshot.get("error_file_id")
        atomic_json(state_path, state)

    results = []
    for item in items:
        artifact = json.loads((artifact_dir / f"{item['id']}.json").read_text(encoding="utf-8"))
        validate_cached_artifact(artifact, item, pass_name, model)
        results.append(artifact)
    counts: dict[str, int] = {}
    for result in results:
        counts[result["status"]] = counts.get(result["status"], 0) + 1
    print(f"[batch:{pass_name}] complete: total={len(results)} statuses={counts}", flush=True)
    return sorted(results, key=lambda row: row["id"])


def summarize_batch_state(output_dir: Path, pass_name: str) -> list[dict[str, Any]]:
    state_path = output_dir / "batch" / pass_name / "state.json"
    if not state_path.is_file():
        return []
    state = json.loads(state_path.read_text(encoding="utf-8"))
    return [{
        "sequence": record["sequence"], "batch_id": record["batch_id"],
        "input_file_id": record["input_file_id"],
        "output_file_id": record.get("output_file_id"),
        "error_file_id": record.get("error_file_id"),
        "request_count": len(record["custom_ids"]),
        "submitted_at_utc": record.get("submitted_at_utc"),
        "processed_at_utc": record.get("processed_at_utc"),
        "terminal_status": record.get("terminal_status"),
    } for record in state["batches"]]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True, help="terra_blind_input.jsonl")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model", default="gpt-5.6-sol")
    parser.add_argument(
        "--reasoning-effort", choices=("low", "medium", "high", "xhigh", "max"), default="high"
    )
    parser.add_argument("--max-output-tokens", type=int, default=16384)
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--min-verified-confidence", type=float, default=0.8)
    parser.add_argument("--poll-seconds", type=int, default=60)
    args = parser.parse_args()
    args.input = args.input.resolve()
    args.output_dir = args.output_dir.resolve()
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is required for Batch annotation")
    if not 0 <= args.min_verified_confidence <= 1:
        raise ValueError("min-verified-confidence must be in [0, 1]")
    if args.poll_seconds < 5:
        raise ValueError("poll-seconds must be at least 5")

    from openai import OpenAI

    items = read_jsonl(args.input)
    if any(set(item) != {"id", "question"} for item in items):
        raise ValueError("blind input rows must contain exactly id and question")
    client = OpenAI()
    validity = run_batch_pass(
        client, items, "validity", args.output_dir, args.model, args.reasoning_effort,
        args.max_output_tokens, args.max_attempts, args.min_verified_confidence, args.poll_seconds,
    )
    item_by_id = {item["id"]: item for item in items}
    valid_items = [
        item_by_id[row["id"]] for row in validity
        if row["status"] == "complete" and row["result"]["label"] == "A"
    ]
    answers = run_batch_pass(
        client, valid_items, "answer", args.output_dir, args.model, args.reasoning_effort,
        args.max_output_tokens, args.max_attempts, args.min_verified_confidence, args.poll_seconds,
    )
    answer_by_id = {row["id"]: row for row in answers}
    write_jsonl(args.output_dir / "terra_raw_results.jsonl", [{
        "id": row["id"], "validity_pass": row,
        "answer_pass": answer_by_id.get(row["id"]),
    } for row in validity])
    atomic_json(args.output_dir / "annotation_manifest.json", {
        "annotation_mode": "openai_batch", "endpoint": "/v1/responses",
        "completion_window": "24h", "model": args.model,
        "reasoning_effort": args.reasoning_effort,
        "max_output_tokens": args.max_output_tokens, "max_attempts": args.max_attempts,
        "min_verified_confidence": args.min_verified_confidence,
        "validity_prompt_version": VALIDITY_PROMPT_VERSION,
        "validity_prompt_sha256": prompt_hash(VALIDITY_SYSTEM_PROMPT),
        "validity_system_prompt": VALIDITY_SYSTEM_PROMPT,
        "answer_prompt_version": ANSWER_PROMPT_VERSION,
        "answer_prompt_sha256": prompt_hash(ANSWER_SYSTEM_PROMPT),
        "answer_system_prompt": ANSWER_SYSTEM_PROMPT,
        "input_count": len(items), "answer_pass_input_count": len(valid_items),
        "validity_batches": summarize_batch_state(args.output_dir, "validity"),
        "answer_batches": summarize_batch_state(args.output_dir, "answer"),
    })


if __name__ == "__main__":
    main()
