#!/usr/bin/env python3
"""Blind, resumable Sol deep review for consistency-audit suspects."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from answer_consistency_audit import atomic_text, collection_hash, value_hash
from batch_annotate import (
    download_file,
    extract_output_text,
    load_state,
    read_lines_if_present,
    submit_record,
    wait_for_batch,
)
from common import atomic_json, prompt_hash, question_hash, read_jsonl, write_jsonl


PROMPT_VERSION = "suspect-deep-review-v1"
SYSTEM_PROMPT = """You are the independent deep reviewer for a mathematical answer dataset.
You receive only an opaque question ID, the question, a prior derived answer (possibly missing),
and a canonical answer (possibly missing). None is authoritative.

Solve the question independently from first principles. Verify what the question actually asks,
whether it is clear and valid, and whether your independently derived answer is complete and
responsive. Then assess the canonical answer and compare your answer separately with the derived
and canonical answers by mathematical meaning, not string equality. Do not assume agreement means
correctness. If ambiguity can change the answer, or reliable verification is not possible, say so.

Recommend KEEP_CANONICAL only when the canonical answer is independently confirmed. Recommend
REPLACE_CANONICAL only when the canonical answer is wrong or missing and your replacement is
reliably verified. Recommend EXCLUDE for a materially ambiguous or invalid question. Recommend
HUMAN_REVIEW for unresolved conflicts or uncertainty. Keep reasoning_summary concise but include
the decisive mathematical check. When recommending REPLACE_CANONICAL, set replacement_answer to
exactly the independently_derived_answer; otherwise set replacement_answer to null. The caller will
apply a stricter deterministic policy and will not automatically trust your recommendation."""

QUESTION_STATUSES = ["CLEAR", "AMBIGUOUS", "INVALID", "UNABLE_TO_VERIFY"]
CANONICAL_STATUSES = [
    "CORRECT", "INCORRECT", "INCOMPLETE", "NOT_RESPONSIVE", "MISSING",
    "UNABLE_TO_VERIFY",
]
RELATIONS = ["AGREE", "EQUIVALENT", "CONFLICT", "NOT_COMPARABLE", "MISSING"]
THREE_WAY = [
    "ALL_AGREE", "CANONICAL_ONLY_DIFFERS", "DERIVED_ONLY_DIFFERS", "ALL_CONFLICT",
    "PARTIAL_OR_MISSING", "NOT_COMPARABLE",
]
MODEL_ACTIONS = ["KEEP_CANONICAL", "REPLACE_CANONICAL", "EXCLUDE", "HUMAN_REVIEW"]
FINAL_ACTIONS = ["KEEP_CANONICAL", "REPLACEMENT_CANDIDATE", "EXCLUDE", "HUMAN_REVIEW"]

REVIEW_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "question_status": {"type": "string", "enum": QUESTION_STATUSES},
        "independently_derived_answer": {"type": ["string", "null"]},
        "independent_answer_verified": {"type": "boolean"},
        "independent_answer_matches_request": {"type": ["boolean", "null"]},
        "canonical_status": {"type": "string", "enum": CANONICAL_STATUSES},
        "canonical_matches_request": {"type": ["boolean", "null"]},
        "derived_sol_relation": {"type": "string", "enum": RELATIONS},
        "canonical_sol_relation": {"type": "string", "enum": RELATIONS},
        "three_way_relation": {"type": "string", "enum": THREE_WAY},
        "recommended_action": {"type": "string", "enum": MODEL_ACTIONS},
        "replacement_answer": {"type": ["string", "null"]},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "reasoning_summary": {"type": "string"},
    },
    "required": [
        "question_status", "independently_derived_answer", "independent_answer_verified",
        "independent_answer_matches_request", "canonical_status", "canonical_matches_request",
        "derived_sol_relation", "canonical_sol_relation", "three_way_relation",
        "recommended_action", "replacement_answer", "confidence", "reasoning_summary",
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
    """One Batch request failed before a parseable model response was available."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def validate_result(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != set(REVIEW_SCHEMA["required"]):
        raise ValueError("deep-review result has missing or extra fields")
    if value["question_status"] not in QUESTION_STATUSES:
        raise ValueError("invalid question_status")
    if value["canonical_status"] not in CANONICAL_STATUSES:
        raise ValueError("invalid canonical_status")
    if value["derived_sol_relation"] not in RELATIONS:
        raise ValueError("invalid derived_sol_relation")
    if value["canonical_sol_relation"] not in RELATIONS:
        raise ValueError("invalid canonical_sol_relation")
    if value["three_way_relation"] not in THREE_WAY:
        raise ValueError("invalid three_way_relation")
    if value["recommended_action"] not in MODEL_ACTIONS:
        raise ValueError("invalid recommended_action")
    for key in ("independent_answer_verified",):
        if not isinstance(value[key], bool):
            raise ValueError(f"{key} must be boolean")
    for key in ("independent_answer_matches_request", "canonical_matches_request"):
        if not isinstance(value[key], (bool, type(None))):
            raise ValueError(f"{key} must be boolean or null")
    for key in ("independently_derived_answer", "replacement_answer"):
        if not isinstance(value[key], (str, type(None))):
            raise ValueError(f"{key} must be string or null")
    confidence = value["confidence"]
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
        raise ValueError("confidence must be numeric")
    if not 0 <= float(confidence) <= 1:
        raise ValueError("confidence must be in [0, 1]")
    if not isinstance(value["reasoning_summary"], str):
        raise ValueError("reasoning_summary must be a string")
    return value


def load_inputs(
    audit_dir: Path, output_dir: Path, expected_count: int | None = 113,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    suspects = read_jsonl(audit_dir / "suspect.jsonl")
    if expected_count is not None and len(suspects) != expected_count:
        raise ValueError(f"expected {expected_count} suspects, found {len(suspects)}")
    by_id = {row["id"]: row for row in suspects}
    if len(by_id) != len(suspects):
        raise ValueError("suspect.jsonl contains duplicate IDs")
    if any(row.get("disposition") != "SUSPECT" for row in suspects):
        raise ValueError("suspect.jsonl contains a non-SUSPECT row")

    blind = []
    for row in suspects:
        question = row.get("question")
        derived = row.get("derived_answer")
        canonical = row.get("canonical_final_answer")
        if not isinstance(question, str) or not question.strip():
            raise ValueError(f"missing question for {row['id']}")
        if derived is not None and not isinstance(derived, str):
            raise ValueError(f"derived answer must be string or null for {row['id']}")
        if canonical is not None and not isinstance(canonical, str):
            raise ValueError(f"canonical answer must be string or null for {row['id']}")
        blind.append({
            "id": row["id"], "question": question,
            "derived_answer": derived, "canonical_final_answer": canonical,
        })
    blind.sort(key=lambda row: row["id"])
    write_jsonl(output_dir / "deep_review_input.jsonl", blind)
    return blind, by_id


def request_body(
    item: dict[str, Any], model: str, reasoning_effort: str, max_output_tokens: int,
) -> dict[str, Any]:
    return {
        "model": model,
        "input": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(item, ensure_ascii=False)},
        ],
        "reasoning": {"effort": reasoning_effort},
        "max_output_tokens": max_output_tokens,
        "text": {"format": {
            "type": "json_schema", "name": "rzero_suspect_deep_review",
            "strict": True, "schema": REVIEW_SCHEMA,
        }},
    }


def make_batch_row(
    item: dict[str, Any], attempt: int, model: str,
    reasoning_effort: str, max_output_tokens: int,
) -> dict[str, Any]:
    return {
        "custom_id": f"deep-review:{item['id']}:a{attempt}",
        "method": "POST", "url": "/v1/responses",
        "body": request_body(item, model, reasoning_effort, max_output_tokens),
    }


def state_config(
    items: list[dict[str, Any]], model: str, reasoning_effort: str,
    max_output_tokens: int, max_attempts: int, confidence_threshold: float,
) -> dict[str, Any]:
    sorted_items = sorted(items, key=lambda row: row["id"])
    config = {
        "pass": "deep_review", "model": model, "reasoning_effort": reasoning_effort,
        "max_output_tokens": max_output_tokens, "max_attempts": max_attempts,
        "confidence_threshold": confidence_threshold,
        "prompt_version": PROMPT_VERSION, "prompt_sha256": prompt_hash(SYSTEM_PROMPT),
        "reviewed_ids": [row["id"] for row in sorted_items],
        "reviewed_id_set_sha256": collection_hash([row["id"] for row in sorted_items]),
        "item_hashes": {
            row["id"]: {
                "question_sha256": question_hash(row["question"]),
                "derived_answer_sha256": value_hash(row["derived_answer"]),
                "canonical_answer_sha256": value_hash(row["canonical_final_answer"]),
            }
            for row in sorted_items
        },
    }
    payload = json.dumps(config, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    config["config_sha256"] = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return config


def validate_artifact(
    artifact: dict[str, Any], item: dict[str, Any], config: dict[str, Any],
) -> None:
    if (
        artifact.get("id") != item["id"]
        or artifact.get("model") != config["model"]
        or artifact.get("prompt_version") != PROMPT_VERSION
        or artifact.get("config_sha256") != config["config_sha256"]
        or artifact.get("input_hashes") != config["item_hashes"][item["id"]]
    ):
        raise RuntimeError(f"cached deep-review artifact mismatch for {item['id']}")


def artifact_for(
    item: dict[str, Any], config: dict[str, Any], attempts: list[dict[str, Any]],
) -> dict[str, Any]:
    parsed = [attempt["parsed"] for attempt in attempts if "parsed" in attempt]
    return {
        "id": item["id"], "pass": "deep_review",
        "status": "complete" if parsed else "failed",
        "input_hashes": config["item_hashes"][item["id"]],
        "config_sha256": config["config_sha256"],
        "prompt_version": PROMPT_VERSION, "model": config["model"],
        "attempts": attempts, "result": parsed[-1] if parsed else None,
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
        validate_artifact(artifact, item, config)
        if artifact["status"] == "complete":
            continue
        attempt = len(artifact["attempts"]) + 1
        if attempt <= config["max_attempts"]:
            pending.append((item, attempt))
    return pending


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
    if len(rows) > 50_000 or input_path.stat().st_size > 200 * 1024 * 1024:
        raise RuntimeError("Batch input exceeds an OpenAI Batch limit")
    return {
        "sequence": sequence, "input_path": str(input_path),
        "output_path": str(batch_dir / f"output_{sequence:02d}.jsonl"),
        "error_path": str(batch_dir / f"errors_{sequence:02d}.jsonl"),
        "custom_ids": [row["custom_id"] for row in rows],
        "input_file_id": None, "batch_id": None, "processed_at_utc": None,
    }


def process_record(
    record: dict[str, Any], items_by_id: dict[str, dict[str, Any]],
    config: dict[str, Any], artifact_dir: Path,
) -> None:
    outputs = {
        row["custom_id"]: row for row in read_lines_if_present(Path(record["output_path"]))
    }
    errors = {
        row["custom_id"]: row for row in read_lines_if_present(Path(record["error_path"]))
    }
    for custom_id in record["custom_ids"]:
        prefix, item_id, attempt_text = custom_id.split(":")
        if prefix != "deep-review":
            raise ValueError(f"unexpected custom_id: {custom_id}")
        attempt_number = int(attempt_text.removeprefix("a"))
        item = items_by_id[item_id]
        path = artifact_dir / f"{item_id}.json"
        existing = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None
        attempts = existing["attempts"] if existing else []
        if existing:
            validate_artifact(existing, item, config)
        if any(row.get("batch_custom_id") == custom_id for row in attempts):
            continue

        raw_line = outputs.get(custom_id)
        if raw_line is not None:
            try:
                response = raw_line.get("response")
                if not isinstance(response, dict) or response.get("status_code") != 200:
                    raise BatchRequestError(f"batch request did not return HTTP 200: {response}")
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
                "error": str(raw_line.get("error") if raw_line else
                             "missing from batch output and error files"),
                "batch_result": raw_line,
            }
        attempts.append(attempt)
        attempts.sort(key=lambda row: int(row["attempt"]))
        atomic_json(path, artifact_for(item, config, attempts))


def run_batch_review(
    client: Any, items: list[dict[str, Any]], output_dir: Path, model: str,
    reasoning_effort: str, max_output_tokens: int, max_attempts: int,
    confidence_threshold: float, poll_seconds: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    batch_dir, artifact_dir = output_dir / "batch", output_dir / "artifacts"
    batch_dir.mkdir(parents=True, exist_ok=True)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    config = state_config(
        items, model, reasoning_effort, max_output_tokens, max_attempts, confidence_threshold,
    )
    state_path = batch_dir / "state.json"
    state = load_state(state_path, config)
    items_by_id = {row["id"]: row for row in items}
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
        validate_artifact(artifact, item, config)
        artifacts.append(artifact)
    counts = Counter(row["status"] for row in artifacts)
    print(f"[batch:deep_review] complete: total={len(artifacts)} statuses={dict(counts)}", flush=True)
    return sorted(artifacts, key=lambda row: row["id"]), config


def deterministic_action(
    artifact: dict[str, Any], confidence_threshold: float,
    source_row: dict[str, Any] | None = None,
) -> tuple[str, list[str]]:
    if artifact["status"] != "complete" or artifact.get("result") is None:
        error_types = {row.get("error_type") for row in artifact["attempts"]}
        reasons = ["REQUEST_FAILURE"] if "BatchRequestError" in error_types else []
        if error_types - {"BatchRequestError", None} or not reasons:
            reasons.append("PARSE_FAILURE")
        return "HUMAN_REVIEW", reasons

    result = artifact["result"]
    if float(result["confidence"]) < confidence_threshold:
        return "HUMAN_REVIEW", ["LOW_CONFIDENCE"]
    if result["question_status"] == "AMBIGUOUS":
        return "EXCLUDE", ["QUESTION_AMBIGUOUS"]
    if result["question_status"] == "INVALID":
        return "EXCLUDE", ["QUESTION_INVALID"]
    if result["question_status"] != "CLEAR":
        return "HUMAN_REVIEW", ["QUESTION_UNABLE_TO_VERIFY"]

    independent_answer = result["independently_derived_answer"]
    independent_reliable = bool(
        result["independent_answer_verified"]
        and result["independent_answer_matches_request"] is True
        and isinstance(independent_answer, str) and independent_answer.strip()
    )
    canonical_confirmed = bool(
        result["canonical_status"] == "CORRECT"
        and result["canonical_matches_request"] is True
        and result["canonical_sol_relation"] in {"AGREE", "EQUIVALENT"}
        and result["derived_sol_relation"] != "CONFLICT"
        and independent_reliable
    )
    if canonical_confirmed:
        if result["recommended_action"] == "KEEP_CANONICAL":
            return "KEEP_CANONICAL", []
        return "HUMAN_REVIEW", ["MODEL_RECOMMENDATION_CONFLICTS_WITH_KEEP_POLICY"]

    canonical_rejected = result["canonical_status"] in {
        "INCORRECT", "INCOMPLETE", "NOT_RESPONSIVE", "MISSING",
    }
    derived_corroborates_sol = result["derived_sol_relation"] in {"AGREE", "EQUIVALENT"}
    canonical_differs = result["canonical_sol_relation"] in {"CONFLICT", "MISSING"}
    replacement = result["replacement_answer"]
    replacement_matches_sol = bool(
        isinstance(replacement, str) and isinstance(independent_answer, str)
        and replacement.strip() == independent_answer.strip()
    )
    screening = (source_row or {}).get("audit_result") or {}
    screening_preferred = screening.get("preferred_final_answer")
    screening_answer_conflict = bool(
        isinstance(screening_preferred, str) and screening_preferred.strip()
        and isinstance(independent_answer, str)
        and screening_preferred.strip() != independent_answer.strip()
    )
    if (
        canonical_rejected and independent_reliable and derived_corroborates_sol
        and canonical_differs and replacement_matches_sol
        and result["recommended_action"] == "REPLACE_CANONICAL"
        and not screening_answer_conflict
    ):
        return "REPLACEMENT_CANDIDATE", ["CANONICAL_REJECTED", "DERIVED_CORROBORATES_SOL"]

    reasons = []
    if not independent_reliable:
        reasons.append("INDEPENDENT_ANSWER_NOT_RELIABLE")
    if result["canonical_sol_relation"] == "CONFLICT":
        reasons.append("CANONICAL_SOL_CONFLICT")
    if result["derived_sol_relation"] == "CONFLICT":
        reasons.append("DERIVED_SOL_CONFLICT")
    if canonical_rejected:
        reasons.append("CANONICAL_REJECTED_WITHOUT_CORROBORATED_REPLACEMENT")
    if result["recommended_action"] == "REPLACE_CANONICAL":
        reasons.append("MODEL_RECOMMENDED_REPLACEMENT_NOT_POLICY_APPROVED")
    if screening_answer_conflict:
        reasons.append("SCREENING_PREFERRED_ANSWER_CONFLICTS_WITH_SOL")
    return "HUMAN_REVIEW", reasons or ["POLICY_REQUIRES_HUMAN_REVIEW"]


def build_results(
    artifacts: list[dict[str, Any]], source_by_id: dict[str, dict[str, Any]],
    confidence_threshold: float,
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    results = []
    groups = {action: [] for action in FINAL_ACTIONS}
    for artifact in artifacts:
        source = source_by_id[artifact["id"]]
        action, reasons = deterministic_action(artifact, confidence_threshold, source)
        row = {
            **source,
            "deep_review_status": artifact["status"],
            "deep_review_result": artifact.get("result"),
            "final_action": action, "decision_reasons": reasons,
            "deep_review_attempts": artifact["attempts"],
        }
        results.append(row)
        groups[action].append(row)
    return sorted(results, key=lambda row: row["id"]), groups


def make_statistics(results: list[dict[str, Any]]) -> dict[str, Any]:
    parsed = [row for row in results if row["deep_review_result"] is not None]
    action_counts = Counter(row["final_action"] for row in results)
    model_actions = Counter(row["deep_review_result"]["recommended_action"] for row in parsed)
    by_round: dict[str, Counter[str]] = defaultdict(Counter)
    by_split: dict[str, Counter[str]] = defaultdict(Counter)
    for row in results:
        by_round[str(row.get("round"))][row["final_action"]] += 1
        by_split[str(row.get("split"))][row["final_action"]] += 1
    error_types = [
        attempt.get("error_type")
        for row in results for attempt in row.get("deep_review_attempts", [])
        if attempt.get("error_type")
    ]
    return {
        "total_suspects": len(results), "parsed": len(parsed),
        "final_action_counts": {action: action_counts[action] for action in FINAL_ACTIONS},
        "model_recommended_action_counts": dict(sorted(model_actions.items())),
        "question_status_counts": dict(sorted(Counter(
            row["deep_review_result"]["question_status"] for row in parsed
        ).items())),
        "canonical_status_counts": dict(sorted(Counter(
            row["deep_review_result"]["canonical_status"] for row in parsed
        ).items())),
        "canonical_sol_relation_counts": dict(sorted(Counter(
            row["deep_review_result"]["canonical_sol_relation"] for row in parsed
        ).items())),
        "derived_sol_relation_counts": dict(sorted(Counter(
            row["deep_review_result"]["derived_sol_relation"] for row in parsed
        ).items())),
        "decision_reason_counts": dict(sorted(Counter(
            reason for row in results for reason in row["decision_reasons"]
        ).items())),
        "attempt_error_counts": dict(sorted(Counter(error_types).items())),
        "retry_count": sum(
            max(0, len(row.get("deep_review_attempts", [])) - 1) for row in results
        ),
        "by_round": {key: dict(value) for key, value in sorted(by_round.items())},
        "by_split": {key: dict(value) for key, value in sorted(by_split.items())},
        "focus_ids": {
            item_id: next(({
                "final_action": row["final_action"],
                "decision_reasons": row["decision_reasons"],
                "deep_review_result": row["deep_review_result"],
            } for row in results if row["id"] == item_id), None)
            for item_id in KNOWN_FOCUS_IDS
        },
        "accounting_check": sum(action_counts.values()) == len(results),
    }


def render_report(stats: dict[str, Any]) -> str:
    lines = [
        "# R-Zero suspect deep-review report", "", "## Accounting", "",
        f"- Total suspects reviewed: {stats['total_suspects']}",
        f"- Successfully parsed: {stats['parsed']}",
        f"- Retries: {stats['retry_count']}", "",
        "| Deterministic action | Count |", "|---|---:|",
    ]
    for action in FINAL_ACTIONS:
        lines.append(f"| {action} | {stats['final_action_counts'][action]} |")
    for title, key in (
        ("Question status", "question_status_counts"),
        ("Canonical status", "canonical_status_counts"),
        ("Canonical/Sol relation", "canonical_sol_relation_counts"),
        ("Derived/Sol relation", "derived_sol_relation_counts"),
        ("Model recommendations", "model_recommended_action_counts"),
        ("Decision reasons", "decision_reason_counts"),
        ("Attempt errors", "attempt_error_counts"),
    ):
        lines.extend(["", f"## {title}", ""])
        lines.extend(f"- {name}: {count}" for name, count in stats[key].items())
        if not stats[key]:
            lines.append("- None")
    lines.extend(["", "## Known focus IDs", ""])
    for item_id, value in stats["focus_ids"].items():
        if value is None:
            lines.append(f"- `{item_id}`: not present")
            continue
        result = value["deep_review_result"] or {}
        summary = result.get("reasoning_summary", "No parseable Sol result.")
        reasons = ", ".join(value["decision_reasons"]) or "none"
        lines.append(f"- `{item_id}`: {value['final_action']}; reasons={reasons}; {summary}")
    for title, key in (("By round", "by_round"), ("By split", "by_split")):
        lines.extend(["", f"## {title}", "", "| Group | Actions |", "|---|---|"])
        for group, counts in stats[key].items():
            detail = ", ".join(f"{action}={count}" for action, count in sorted(counts.items()))
            lines.append(f"| {group} | {detail} |")
    lines.extend([
        "", "## Safety boundary", "",
        "Replacement candidates are review artifacts, not automatic edits. This program did not",
        "modify train/validation data, overwrite canonical answers, upload Hugging Face data, or",
        "start GRPO.", "",
    ])
    return "\n".join(lines)


def write_outputs(
    output_dir: Path, audit_dir: Path, results: list[dict[str, Any]],
    groups: dict[str, list[dict[str, Any]]], stats: dict[str, Any], config: dict[str, Any],
) -> None:
    write_jsonl(output_dir / "deep_review_results.jsonl", results)
    write_jsonl(output_dir / "keep.jsonl", groups["KEEP_CANONICAL"])
    write_jsonl(output_dir / "replacement_candidates.jsonl", groups["REPLACEMENT_CANDIDATE"])
    write_jsonl(output_dir / "exclude.jsonl", groups["EXCLUDE"])
    write_jsonl(output_dir / "human_review.jsonl", groups["HUMAN_REVIEW"])
    atomic_json(output_dir / "analysis" / "statistics.json", stats)
    atomic_text(output_dir / "analysis" / "report.md", render_report(stats))
    state = json.loads((output_dir / "batch" / "state.json").read_text(encoding="utf-8"))
    batches = [{
        "sequence": row["sequence"], "batch_id": row["batch_id"],
        "input_file_id": row["input_file_id"],
        "output_file_id": row.get("output_file_id"), "error_file_id": row.get("error_file_id"),
        "request_count": len(row["custom_ids"]),
        "submitted_at_utc": row.get("submitted_at_utc"),
        "processed_at_utc": row.get("processed_at_utc"),
        "terminal_status": row.get("terminal_status"),
    } for row in state["batches"]]
    atomic_json(output_dir / "manifest.json", {
        "created_at_utc": utc_now(), "source_consistency_audit_dir": str(audit_dir),
        "endpoint": "/v1/responses", "completion_window": "24h",
        "deep_review_config": config, "batches": batches,
        "counts": stats["final_action_counts"], "total_suspects": stats["total_suspects"],
    })


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("audit_dir", type=Path, help="completed consistency-audit output directory")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model", default=os.environ.get("DEEP_REVIEW_MODEL", "gpt-5.6-sol"))
    parser.add_argument(
        "--reasoning-effort", choices=("low", "medium", "high", "xhigh", "max"),
        default=os.environ.get("DEEP_REVIEW_REASONING_EFFORT", "high"),
    )
    parser.add_argument(
        "--max-output-tokens", type=int,
        default=int(os.environ.get("DEEP_REVIEW_MAX_OUTPUT_TOKENS", "16384")),
    )
    parser.add_argument(
        "--max-attempts", type=int,
        default=int(os.environ.get("DEEP_REVIEW_MAX_ATTEMPTS", "3")),
    )
    parser.add_argument(
        "--confidence-threshold", type=float,
        default=float(os.environ.get("DEEP_REVIEW_CONFIDENCE_THRESHOLD", "0.9")),
    )
    parser.add_argument(
        "--poll-seconds", type=int,
        default=int(os.environ.get("DEEP_REVIEW_POLL_SECONDS", "60")),
    )
    args = parser.parse_args()
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is required for the Sol deep-review Batch")
    if not 0 <= args.confidence_threshold <= 1:
        raise ValueError("confidence-threshold must be in [0, 1]")
    if args.max_attempts < 1 or args.max_output_tokens < 1:
        raise ValueError("max-attempts and max-output-tokens must be positive")
    if args.poll_seconds < 5:
        raise ValueError("poll-seconds must be at least 5")

    audit_dir, output_dir = args.audit_dir.resolve(), args.output_dir.resolve()
    blind, source_by_id = load_inputs(audit_dir, output_dir)
    from openai import OpenAI
    artifacts, config = run_batch_review(
        OpenAI(), blind, output_dir, args.model, args.reasoning_effort,
        args.max_output_tokens, args.max_attempts, args.confidence_threshold, args.poll_seconds,
    )
    results, groups = build_results(artifacts, source_by_id, args.confidence_threshold)
    stats = make_statistics(results)
    if len(results) != 113 or not stats["accounting_check"]:
        raise RuntimeError("deep-review accounting failed")
    write_outputs(output_dir, audit_dir, results, groups, stats, config)
    print(
        f"[deep-review] total={len(results)} actions={stats['final_action_counts']} "
        f"report={output_dir / 'analysis/report.md'}",
        flush=True,
    )


if __name__ == "__main__":
    main()
