#!/usr/bin/env python3
"""Blind, resumable third-pass audit of Terra VALID canonical answers."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from batch_annotate import (
    download_file,
    extract_output_text,
    load_state,
    read_lines_if_present,
    submit_record,
    wait_for_batch,
)
from common import atomic_json, prompt_hash, question_hash, read_jsonl, write_jsonl


AUDIT_PROMPT_VERSION = "answer-consistency-v1"
AUDIT_SYSTEM_PROMPT = """You are an independent mathematical answer consistency auditor.
You receive an opaque question ID, the question, a Pass 1 derived answer (which may be missing),
and a Pass 2 canonical answer. Neither answer is authoritative.

Read the question carefully and identify exactly what it asks. Independently do the mathematical
checks needed to decide whether the canonical answer is correct, complete, and responsive. Decide
whether an ambiguity in the question could change the answer. Compare the two supplied answers by
mathematical meaning, not merely by string equality: different strings can be equivalent, and equal
strings are not proof of correctness. If reliable verification is not possible, say so explicitly.
Keep reasoning_summary concise and concrete; do not provide a long proof.

Relation meanings:
- AGREE: same answer and meaning.
- EQUIVALENT: different presentation but mathematically equivalent.
- CONFLICT: incompatible answers.
- NOT_COMPARABLE: their forms or scopes do not permit a reliable direct comparison.
- MISSING: the derived answer is absent.
Set needs_deep_review whenever there is a correctness concern, material ambiguity, conflict, or
insufficient basis for a high-confidence screening decision."""

QUESTION_STATUSES = ["CLEAR", "AMBIGUOUS", "INVALID", "UNABLE_TO_VERIFY"]
ANSWER_STATUSES = ["CORRECT", "INCORRECT", "INCOMPLETE", "NOT_RESPONSIVE", "UNABLE_TO_VERIFY"]
DERIVED_STATUSES = [
    "CORRECT", "INCORRECT", "INCOMPLETE", "NOT_RESPONSIVE", "MISSING", "UNABLE_TO_VERIFY",
]
RELATIONS = ["AGREE", "EQUIVALENT", "CONFLICT", "NOT_COMPARABLE", "MISSING"]

AUDIT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "goal_summary": {"type": "string"},
        "question_status": {"type": "string", "enum": QUESTION_STATUSES},
        "canonical_status": {"type": "string", "enum": ANSWER_STATUSES},
        "derived_status": {"type": "string", "enum": DERIVED_STATUSES},
        "derived_canonical_relation": {"type": "string", "enum": RELATIONS},
        "canonical_matches_request": {"type": ["boolean", "null"]},
        "preferred_final_answer": {"type": ["string", "null"]},
        "needs_deep_review": {"type": "boolean"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "reasoning_summary": {"type": "string"},
    },
    "required": [
        "goal_summary", "question_status", "canonical_status", "derived_status",
        "derived_canonical_relation", "canonical_matches_request", "preferred_final_answer",
        "needs_deep_review", "confidence", "reasoning_summary",
    ],
    "additionalProperties": False,
}

KNOWN_FOCUS_IDS = [
    "q_9d467f06bc671812",
    "q_a073cdfc87f5455c",
    "q_9356873fdf7ae8bd",
    "q_45c2e20cb950ff2c",
    "q_cffc2b221abb1276",
]


class BatchRequestError(ValueError):
    """One request failed before a parseable model response was available."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def value_hash(value: str | None) -> str:
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def collection_hash(values: list[str]) -> str:
    payload = json.dumps(sorted(values), ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def atomic_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.tmp-{os.getpid()}")
    temporary.write_text(value, encoding="utf-8")
    os.replace(temporary, path)


def validate_audit_result(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != set(AUDIT_SCHEMA["required"]):
        raise ValueError("audit result has missing or extra fields")
    if value["question_status"] not in QUESTION_STATUSES:
        raise ValueError("invalid question_status")
    if value["canonical_status"] not in ANSWER_STATUSES:
        raise ValueError("invalid canonical_status")
    if value["derived_status"] not in DERIVED_STATUSES:
        raise ValueError("invalid derived_status")
    if value["derived_canonical_relation"] not in RELATIONS:
        raise ValueError("invalid derived_canonical_relation")
    if not isinstance(value["canonical_matches_request"], (bool, type(None))):
        raise ValueError("canonical_matches_request must be boolean or null")
    if not isinstance(value["preferred_final_answer"], (str, type(None))):
        raise ValueError("preferred_final_answer must be string or null")
    if not isinstance(value["needs_deep_review"], bool):
        raise ValueError("needs_deep_review must be boolean")
    confidence = value["confidence"]
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
        raise ValueError("confidence must be numeric")
    if not 0 <= float(confidence) <= 1:
        raise ValueError("confidence must be in [0, 1]")
    for key in ("goal_summary", "reasoning_summary"):
        if not isinstance(value[key], str):
            raise ValueError(f"{key} must be a string")
    return value


def request_body(
    item: dict[str, Any], model: str, reasoning_effort: str, max_output_tokens: int,
) -> dict[str, Any]:
    user_payload = {
        "id": item["id"],
        "question": item["question"],
        "derived_answer": item["derived_answer"],
        "canonical_final_answer": item["canonical_final_answer"],
    }
    return {
        "model": model,
        "input": [
            {"role": "system", "content": AUDIT_SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
        ],
        "reasoning": {"effort": reasoning_effort},
        "max_output_tokens": max_output_tokens,
        "text": {"format": {
            "type": "json_schema", "name": "rzero_answer_consistency_audit",
            "strict": True, "schema": AUDIT_SCHEMA,
        }},
    }


def make_batch_row(
    item: dict[str, Any], attempt: int, model: str,
    reasoning_effort: str, max_output_tokens: int,
) -> dict[str, Any]:
    return {
        "custom_id": f"consistency:{item['id']}:a{attempt}",
        "method": "POST", "url": "/v1/responses",
        "body": request_body(item, model, reasoning_effort, max_output_tokens),
    }


def _unique_by_id(rows: list[dict[str, Any]], name: str) -> dict[str, dict[str, Any]]:
    result = {row["id"]: row for row in rows}
    if len(result) != len(rows):
        raise ValueError(f"{name} contains duplicate IDs")
    return result


def prepare_audit_inputs(
    source_dir: Path, output_dir: Path,
    expected_raw: int | None = 2300,
    expected_valid: int | None = 983,
    expected_verified: int | None = 973,
    expected_unverified: int | None = 10,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, dict[str, Any]]]:
    raw = read_jsonl(source_dir / "terra_raw_results.jsonl")
    sampled = read_jsonl(source_dir / "sampled_questions.jsonl")
    raw_by_id = _unique_by_id(raw, "terra_raw_results")
    sampled_by_id = _unique_by_id(sampled, "sampled_questions")
    if set(raw_by_id) != set(sampled_by_id):
        raise ValueError("terra_raw_results/sample questions ID sets differ")

    valid: list[dict[str, Any]] = []
    verified: list[dict[str, Any]] = []
    unverified: list[dict[str, Any]] = []
    private_by_id: dict[str, dict[str, Any]] = {}
    for item_id, annotation in raw_by_id.items():
        validity_pass = annotation.get("validity_pass") or {}
        validity_result = validity_pass.get("result") or {}
        if validity_pass.get("status") != "complete" or validity_result.get("label") != "A":
            continue
        source = sampled_by_id[item_id]
        derived = validity_result.get("derived_answer")
        if derived is not None and not isinstance(derived, str):
            raise ValueError(f"derived_answer must be string or null for {item_id}")
        answer_pass = annotation.get("answer_pass") or {}
        answer_result = answer_pass.get("result") or {}
        canonical = answer_result.get("canonical_final_answer")
        base = {
            "id": item_id, "question": source["question"],
            "derived_answer": derived, "canonical_final_answer": canonical,
        }
        private_by_id[item_id] = {
            **base, "round": source["round"], "split": source["split"],
            "source_answer_status": answer_pass.get("status"),
            "source_answer_verified": answer_result.get("answer_verified"),
            "source_answer_confidence": answer_result.get("confidence"),
        }
        valid.append(base)
        if (
            answer_pass.get("status") == "complete"
            and answer_result.get("answer_verified") is True
            and isinstance(canonical, str) and canonical.strip()
        ):
            verified.append(base)
        else:
            unverified.append({
                **private_by_id[item_id], "disposition": "SUSPECT",
                "suspect_reasons": ["PREEXISTING_UNVERIFIED"],
                "audit_status": "PREEXISTING_UNVERIFIED", "audit_result": None,
            })

    actual = (len(raw), len(valid), len(verified), len(unverified))
    expected = (expected_raw, expected_valid, expected_verified, expected_unverified)
    labels = ("raw results", "A/VALID", "verified canonical", "preexisting unverified")
    for label, wanted, got in zip(labels, expected, actual):
        if wanted is not None and wanted != got:
            raise ValueError(f"expected {wanted} {label}, found {got}")

    verified.sort(key=lambda row: row["id"])
    unverified.sort(key=lambda row: row["id"])
    # This file is the exact payload-level data allowed to reach the audit model.
    write_jsonl(output_dir / "audit_input.jsonl", verified)
    write_jsonl(output_dir / "preexisting_unverified.jsonl", unverified)
    return verified, unverified, private_by_id


def state_config(
    items: list[dict[str, Any]], model: str, reasoning_effort: str,
    max_output_tokens: int, max_attempts: int, confidence_threshold: float,
) -> dict[str, Any]:
    sorted_items = sorted(items, key=lambda row: row["id"])
    config = {
        "pass": "consistency", "model": model, "reasoning_effort": reasoning_effort,
        "max_output_tokens": max_output_tokens, "max_attempts": max_attempts,
        "confidence_threshold": confidence_threshold,
        "prompt_version": AUDIT_PROMPT_VERSION,
        "prompt_sha256": prompt_hash(AUDIT_SYSTEM_PROMPT),
        "audited_ids": [item["id"] for item in sorted_items],
        "audited_id_set_sha256": collection_hash([item["id"] for item in sorted_items]),
        "item_hashes": {
            item["id"]: {
                "question_sha256": question_hash(item["question"]),
                "derived_answer_sha256": value_hash(item["derived_answer"]),
                "canonical_answer_sha256": value_hash(item["canonical_final_answer"]),
            }
            for item in sorted_items
        },
    }
    serialized = json.dumps(config, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    config["config_sha256"] = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    return config


def validate_cached_artifact(
    artifact: dict[str, Any], item: dict[str, Any], config: dict[str, Any],
) -> None:
    expected_hashes = config["item_hashes"][item["id"]]
    if (
        artifact.get("id") != item["id"]
        or artifact.get("model") != config["model"]
        or artifact.get("prompt_version") != AUDIT_PROMPT_VERSION
        or artifact.get("config_sha256") != config["config_sha256"]
        or artifact.get("input_hashes") != expected_hashes
    ):
        raise RuntimeError(f"cached consistency artifact configuration mismatch for {item['id']}")


def artifact_for(
    item: dict[str, Any], config: dict[str, Any], attempts: list[dict[str, Any]],
) -> dict[str, Any]:
    parsed = [attempt["parsed"] for attempt in attempts if "parsed" in attempt]
    return {
        "id": item["id"], "pass": "consistency",
        "status": "complete" if parsed else "failed",
        "input_hashes": config["item_hashes"][item["id"]],
        "config_sha256": config["config_sha256"],
        "prompt_version": AUDIT_PROMPT_VERSION, "model": config["model"],
        "attempts": attempts, "result": parsed[-1] if parsed else None,
    }


def create_record(
    pending: list[tuple[dict[str, Any], int]], config: dict[str, Any],
    batch_dir: Path, sequence: int,
) -> dict[str, Any]:
    rows = [
        make_batch_row(item, attempt, config["model"], config["reasoning_effort"],
                       config["max_output_tokens"])
        for item, attempt in pending
    ]
    input_path = batch_dir / f"input_{sequence:02d}.jsonl"
    write_jsonl(input_path, rows)
    if len(rows) > 50_000:
        raise RuntimeError(f"batch input exceeds 50,000 requests: {len(rows)}")
    if input_path.stat().st_size > 200 * 1024 * 1024:
        raise RuntimeError(f"batch input exceeds 200 MB: {input_path}")
    return {
        "sequence": sequence, "input_path": str(input_path),
        "output_path": str(batch_dir / f"output_{sequence:02d}.jsonl"),
        "error_path": str(batch_dir / f"errors_{sequence:02d}.jsonl"),
        "custom_ids": [row["custom_id"] for row in rows],
        "input_file_id": None, "batch_id": None, "processed_at_utc": None,
    }


def pending_items(
    items: list[dict[str, Any]], config: dict[str, Any], artifact_dir: Path,
) -> list[tuple[dict[str, Any], int]]:
    pending = []
    for item in items:
        path = artifact_dir / f"{item['id']}.json"
        if not path.is_file():
            pending.append((item, 1))
            continue
        artifact = json.loads(path.read_text(encoding="utf-8"))
        validate_cached_artifact(artifact, item, config)
        if artifact["status"] == "complete":
            continue
        next_attempt = len(artifact["attempts"]) + 1
        if next_attempt <= config["max_attempts"]:
            pending.append((item, next_attempt))
    return pending


def process_record(
    record: dict[str, Any], items_by_id: dict[str, dict[str, Any]],
    config: dict[str, Any], artifact_dir: Path,
) -> None:
    output_by_id = {
        row["custom_id"]: row for row in read_lines_if_present(Path(record["output_path"]))
    }
    error_by_id = {
        row["custom_id"]: row for row in read_lines_if_present(Path(record["error_path"]))
    }
    for custom_id in record["custom_ids"]:
        prefix, item_id, attempt_text = custom_id.split(":")
        if prefix != "consistency":
            raise ValueError(f"unexpected custom_id: {custom_id}")
        attempt_number = int(attempt_text.removeprefix("a"))
        item = items_by_id[item_id]
        destination = artifact_dir / f"{item_id}.json"
        existing = json.loads(destination.read_text(encoding="utf-8")) if destination.is_file() else None
        if existing:
            validate_cached_artifact(existing, item, config)
            attempts = existing["attempts"]
            if any(attempt.get("batch_custom_id") == custom_id for attempt in attempts):
                continue
        else:
            attempts = []
        if custom_id in output_by_id:
            raw_line = output_by_id[custom_id]
            try:
                response = raw_line.get("response")
                if not isinstance(response, dict) or response.get("status_code") != 200:
                    raise BatchRequestError(f"batch request did not return HTTP 200: {response}")
                body = response.get("body")
                if not isinstance(body, dict):
                    raise ValueError("batch response is missing a response body")
                parsed = validate_audit_result(json.loads(extract_output_text(body)))
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
            raw_line = error_by_id.get(custom_id)
            attempt = {
                "attempt": attempt_number, "batch_custom_id": custom_id,
                "error_type": "BatchRequestError",
                "error": str(raw_line.get("error") if raw_line else
                             "missing from batch output and error files"),
                "batch_result": raw_line,
            }
        attempts.append(attempt)
        attempts.sort(key=lambda value: int(value["attempt"]))
        atomic_json(destination, artifact_for(item, config, attempts))


def run_batch_audit(
    client: Any, items: list[dict[str, Any]], output_dir: Path, model: str,
    reasoning_effort: str, max_output_tokens: int, max_attempts: int,
    confidence_threshold: float, poll_seconds: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    batch_dir = output_dir / "batch"
    artifact_dir = output_dir / "artifacts"
    batch_dir.mkdir(parents=True, exist_ok=True)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    config = state_config(
        items, model, reasoning_effort, max_output_tokens, max_attempts, confidence_threshold,
    )
    state_path = batch_dir / "state.json"
    state = load_state(state_path, config)
    items_by_id = {item["id"]: item for item in items}
    while True:
        active = next((row for row in state["batches"] if not row["processed_at_utc"]), None)
        if active is None:
            pending = pending_items(items, config, artifact_dir)
            if not pending:
                break
            active = create_record(pending, config, batch_dir, len(state["batches"]) + 1)
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
        process_record(active, items_by_id, config, artifact_dir)
        active.update({
            "processed_at_utc": utc_now(), "terminal_status": snapshot["status"],
            "output_file_id": snapshot.get("output_file_id"),
            "error_file_id": snapshot.get("error_file_id"),
        })
        atomic_json(state_path, state)

    artifacts = []
    for item in items:
        artifact = json.loads((artifact_dir / f"{item['id']}.json").read_text(encoding="utf-8"))
        validate_cached_artifact(artifact, item, config)
        artifacts.append(artifact)
    counts = Counter(row["status"] for row in artifacts)
    print(f"[batch:consistency] complete: total={len(artifacts)} statuses={dict(counts)}", flush=True)
    return sorted(artifacts, key=lambda row: row["id"]), config


def suspect_reasons(
    artifact: dict[str, Any], confidence_threshold: float,
) -> list[str]:
    if artifact["status"] != "complete" or artifact.get("result") is None:
        error_types = {attempt.get("error_type") for attempt in artifact["attempts"]}
        reasons = []
        if "BatchRequestError" in error_types:
            reasons.append("REQUEST_FAILURE")
        if error_types - {"BatchRequestError", None} or not reasons:
            reasons.append("PARSE_FAILURE")
        return reasons
    result = artifact["result"]
    reasons = []
    if result["question_status"] != "CLEAR":
        reasons.append(f"QUESTION_{result['question_status']}")
    if result["canonical_status"] != "CORRECT":
        reasons.append(f"CANONICAL_{result['canonical_status']}")
    if result["canonical_matches_request"] is not True:
        reasons.append("CANONICAL_DOES_NOT_MATCH_REQUEST")
    if result["derived_canonical_relation"] == "CONFLICT":
        reasons.append("DERIVED_CANONICAL_CONFLICT")
    if result["needs_deep_review"]:
        reasons.append("MODEL_REQUESTED_DEEP_REVIEW")
    if float(result["confidence"]) < confidence_threshold:
        reasons.append("LOW_CONFIDENCE")
    return reasons


def build_results(
    artifacts: list[dict[str, Any]], private_by_id: dict[str, dict[str, Any]],
    unverified: list[dict[str, Any]], confidence_threshold: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    results = []
    for artifact in artifacts:
        reasons = suspect_reasons(artifact, confidence_threshold)
        results.append({
            **private_by_id[artifact["id"]],
            "audit_status": artifact["status"], "audit_result": artifact.get("result"),
            "disposition": "PASS" if not reasons else "SUSPECT",
            "suspect_reasons": reasons, "attempts": artifact["attempts"],
        })
    results.extend(unverified)
    results.sort(key=lambda row: row["id"])
    passed = [row for row in results if row["disposition"] == "PASS"]
    suspect = [row for row in results if row["disposition"] == "SUSPECT"]
    return results, passed, suspect


def _outcome_table(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, int]]:
    grouped: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        grouped[str(row[key])][row["disposition"]] += 1
    return {
        group: {"PASS": counts["PASS"], "SUSPECT": counts["SUSPECT"]}
        for group, counts in sorted(grouped.items())
    }


def make_statistics(
    results: list[dict[str, Any]], submitted_count: int,
) -> dict[str, Any]:
    passed = sum(row["disposition"] == "PASS" for row in results)
    suspect = len(results) - passed
    audited_results = [row for row in results if row["audit_result"] is not None]
    attempts = [row for row in results if row.get("attempts")]
    stats = {
        "total_valid": len(results), "submitted_to_consistency_api": submitted_count,
        "preexisting_unverified": sum(
            "PREEXISTING_UNVERIFIED" in row["suspect_reasons"] for row in results
        ),
        "pass": passed, "pass_rate": passed / len(results) if results else None,
        "suspect": suspect, "suspect_rate": suspect / len(results) if results else None,
        "parse_failures": sum("PARSE_FAILURE" in row["suspect_reasons"] for row in results),
        "request_failures": sum("REQUEST_FAILURE" in row["suspect_reasons"] for row in results),
        "retry_count": sum(max(0, len(row["attempts"]) - 1) for row in attempts),
        "question_status_counts": dict(sorted(Counter(
            row["audit_result"]["question_status"] for row in audited_results
        ).items())),
        "canonical_status_counts": dict(sorted(Counter(
            row["audit_result"]["canonical_status"] for row in audited_results
        ).items())),
        "relation_counts": dict(sorted(Counter(
            row["audit_result"]["derived_canonical_relation"] for row in audited_results
        ).items())),
        "suspect_reason_counts": dict(sorted(Counter(
            reason for row in results for reason in row["suspect_reasons"]
        ).items())),
        "by_round": _outcome_table(results, "round"),
        "by_split": _outcome_table(results, "split"),
        "focus_ids": {
            item_id: next(({
                "disposition": row["disposition"],
                "suspect_reasons": row["suspect_reasons"],
                "audit_result": row["audit_result"],
            } for row in results if row["id"] == item_id), None)
            for item_id in KNOWN_FOCUS_IDS
        },
        "accounting_check": {
            "pass_plus_suspect_equals_total": passed + suspect == len(results),
            "submitted_plus_preexisting_equals_total": submitted_count + sum(
                "PREEXISTING_UNVERIFIED" in row["suspect_reasons"] for row in results
            ) == len(results),
        },
    }
    return stats


def render_report(stats: dict[str, Any]) -> str:
    total = stats["total_valid"]
    lines = [
        "# R-Zero VALID-answer consistency audit", "", "## Accounting", "",
        f"- Total VALID: {total}",
        f"- Submitted to consistency API: {stats['submitted_to_consistency_api']}",
        f"- Preexisting unverified: {stats['preexisting_unverified']}",
        f"- PASS: {stats['pass']} ({stats['pass_rate']:.2%})" if total else "- PASS: 0",
        f"- SUSPECT: {stats['suspect']} ({stats['suspect_rate']:.2%})" if total else "- SUSPECT: 0",
        f"- Parse failures: {stats['parse_failures']}",
        f"- Request failures: {stats['request_failures']}",
        f"- Retries: {stats['retry_count']}", "",
    ]
    for title, key in (
        ("Question status", "question_status_counts"),
        ("Canonical status", "canonical_status_counts"),
        ("Derived/canonical relation", "relation_counts"),
        ("Suspect reasons", "suspect_reason_counts"),
    ):
        lines.extend([f"## {title}", ""])
        if stats[key]:
            lines.extend(f"- {name}: {count}" for name, count in stats[key].items())
        else:
            lines.append("- None")
        lines.append("")
    for title, key in (("By round", "by_round"), ("By split", "by_split")):
        lines.extend([f"## {title}", "", "| Group | PASS | SUSPECT |", "|---|---:|---:|"])
        for group, counts in stats[key].items():
            lines.append(f"| {group} | {counts['PASS']} | {counts['SUSPECT']} |")
        lines.append("")
    lines.extend(["## Known focus IDs (post-audit sanity check only)", ""])
    for item_id, value in stats["focus_ids"].items():
        if value is None:
            lines.append(f"- `{item_id}`: not present")
        else:
            result = value["audit_result"] or {}
            summary = result.get("reasoning_summary", "preexisting unverified")
            reasons = ", ".join(value["suspect_reasons"]) or "none"
            lines.append(
                f"- `{item_id}`: {value['disposition']}; reasons={reasons}; {summary}"
            )
    lines.extend([
        "", "## Next stage", "",
        f"Deep review is needed for {stats['suspect']} SUSPECT samples. This screening stage did not",
        "change canonical answers, filter the dataset, call Sol, vote, upload data, or start GRPO.", "",
    ])
    return "\n".join(lines)


def write_outputs(
    output_dir: Path, results: list[dict[str, Any]], passed: list[dict[str, Any]],
    suspect: list[dict[str, Any]], stats: dict[str, Any], config: dict[str, Any],
    source_dir: Path,
) -> None:
    write_jsonl(output_dir / "audit_results.jsonl", results)
    write_jsonl(output_dir / "passed.jsonl", passed)
    write_jsonl(output_dir / "suspect.jsonl", suspect)
    atomic_json(output_dir / "analysis" / "statistics.json", stats)
    atomic_text(output_dir / "analysis" / "report.md", render_report(stats))
    state = json.loads((output_dir / "batch" / "state.json").read_text(encoding="utf-8"))
    batch_runs = [{
        "sequence": record["sequence"], "batch_id": record["batch_id"],
        "input_file_id": record["input_file_id"],
        "output_file_id": record.get("output_file_id"),
        "error_file_id": record.get("error_file_id"),
        "request_count": len(record["custom_ids"]),
        "submitted_at_utc": record.get("submitted_at_utc"),
        "processed_at_utc": record.get("processed_at_utc"),
        "terminal_status": record.get("terminal_status"),
    } for record in state["batches"]]
    atomic_json(output_dir / "manifest.json", {
        "created_at_utc": utc_now(), "source_dir": str(source_dir),
        "endpoint": "/v1/responses", "completion_window": "24h",
        "audit_config": config, "batch_runs": batch_runs,
        "counts": {
            "total_valid": stats["total_valid"],
            "submitted": stats["submitted_to_consistency_api"],
            "preexisting_unverified": stats["preexisting_unverified"],
            "pass": stats["pass"], "suspect": stats["suspect"],
        },
    })


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_dir", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model", default=os.environ.get("CONSISTENCY_MODEL", "gpt-5.6-luna"))
    parser.add_argument(
        "--reasoning-effort", choices=("low", "medium", "high", "xhigh", "max"),
        default=os.environ.get("CONSISTENCY_REASONING_EFFORT", "high"),
    )
    parser.add_argument(
        "--max-output-tokens", type=int,
        default=int(os.environ.get("CONSISTENCY_MAX_OUTPUT_TOKENS", "8192")),
    )
    parser.add_argument(
        "--max-attempts", type=int,
        default=int(os.environ.get("CONSISTENCY_MAX_ATTEMPTS", "3")),
    )
    parser.add_argument(
        "--confidence-threshold", type=float,
        default=float(os.environ.get("CONSISTENCY_CONFIDENCE_THRESHOLD", "0.8")),
    )
    parser.add_argument(
        "--poll-seconds", type=int,
        default=int(os.environ.get("BATCH_POLL_SECONDS", "60")),
    )
    args = parser.parse_args()
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is required for the consistency Batch audit")
    if not 0 <= args.confidence_threshold <= 1:
        raise ValueError("confidence-threshold must be in [0, 1]")
    if args.max_attempts < 1:
        raise ValueError("max-attempts must be positive")
    if args.poll_seconds < 5:
        raise ValueError("poll-seconds must be at least 5")
    source_dir = args.source_dir.resolve()
    output_dir = args.output_dir.resolve()
    verified, unverified, private_by_id = prepare_audit_inputs(source_dir, output_dir)
    from openai import OpenAI
    artifacts, config = run_batch_audit(
        OpenAI(), verified, output_dir, args.model, args.reasoning_effort,
        args.max_output_tokens, args.max_attempts, args.confidence_threshold, args.poll_seconds,
    )
    results, passed, suspect = build_results(
        artifacts, private_by_id, unverified, args.confidence_threshold,
    )
    stats = make_statistics(results, len(verified))
    if not all(stats["accounting_check"].values()):
        raise RuntimeError(f"audit accounting failed: {stats['accounting_check']}")
    write_outputs(output_dir, results, passed, suspect, stats, config, source_dir)
    print(
        f"[consistency] PASS={stats['pass']} SUSPECT={stats['suspect']} "
        f"total={stats['total_valid']} report={output_dir / 'analysis/report.md'}",
        flush=True,
    )


if __name__ == "__main__":
    main()
