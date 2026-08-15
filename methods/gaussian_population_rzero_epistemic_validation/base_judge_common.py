#!/usr/bin/env python3
"""Shared prompt, parsing, and metric utilities for the frozen Base Judge."""

from __future__ import annotations

import json
import math
from typing import Any, Iterable


LABELS = ["A", "B", "C", "D", "E", "F"]
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

BASE_JUDGE_SCHEMA: dict[str, Any] = {
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
        "probability_label_A": {"type": "number", "minimum": 0, "maximum": 1},
        "issue_types": {"type": "array", "items": {"type": "string"}},
        "reasoning_summary": {"type": "string"},
        "derived_answer": {"type": ["string", "null"]},
    },
    "required": [
        "goal_restatement", "conditions_complete", "contradictory",
        "multiple_reasonable_interpretations", "solution_exists",
        "unique_or_explicit_grading", "label", "confidence",
        "probability_label_A", "issue_types", "reasoning_summary", "derived_answer",
    ],
    "additionalProperties": False,
}


def build_prompt(question: str, retry: bool = False) -> str:
    """Render a prompt containing no experiment metadata beyond the question itself."""
    fields = ", ".join(BASE_JUDGE_SCHEMA["required"])
    retry_note = (
        " Your previous response could not be parsed. Return one JSON object only, with no markdown."
        if retry else " Return one JSON object only, with no markdown."
    )
    return (
        f"{SYSTEM_PROMPT}\n\n"
        "The output must use exactly these fields: " + fields + ". "
        "probability_label_A must be your calibrated probability from 0 to 1 that the strict label is A."
        f"{retry_note}\n\nQuestion:\n{question}"
    )


def validate_judgment(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("judgment is not a JSON object")
    required = set(BASE_JUDGE_SCHEMA["required"])
    if set(value) != required:
        missing, extra = sorted(required - set(value)), sorted(set(value) - required)
        raise ValueError(f"judgment fields differ; missing={missing}, extra={extra}")
    for field in (
        "conditions_complete", "contradictory", "multiple_reasonable_interpretations",
        "solution_exists", "unique_or_explicit_grading",
    ):
        if type(value[field]) is not bool:
            raise ValueError(f"{field} must be boolean")
    if value["label"] not in LABELS:
        raise ValueError("label must be A-F")
    for field in ("confidence", "probability_label_A"):
        if isinstance(value[field], bool):
            raise ValueError(f"{field} must be numeric")
        number = float(value[field])
        if not math.isfinite(number) or not 0 <= number <= 1:
            raise ValueError(f"{field} must be in [0, 1]")
        value[field] = number
    if not isinstance(value["issue_types"], list) or not all(
        isinstance(item, str) for item in value["issue_types"]
    ):
        raise ValueError("issue_types must be a string array")
    for field in ("goal_restatement", "reasoning_summary"):
        if not isinstance(value[field], str):
            raise ValueError(f"{field} must be a string")
    if value["derived_answer"] is not None and not isinstance(value["derived_answer"], str):
        raise ValueError("derived_answer must be a string or null")
    return value


def parse_judgment(text: str) -> dict[str, Any]:
    """Parse direct, fenced, or text-prefixed JSON and apply strict validation."""
    candidate = text.strip()
    if candidate.startswith("```"):
        lines = candidate.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        candidate = "\n".join(lines).strip()
    try:
        return validate_judgment(json.loads(candidate))
    except (json.JSONDecodeError, ValueError) as direct_error:
        decoder = json.JSONDecoder()
        for index, character in enumerate(candidate):
            if character != "{":
                continue
            try:
                value, _ = decoder.raw_decode(candidate[index:])
                return validate_judgment(value)
            except (json.JSONDecodeError, ValueError):
                continue
        raise ValueError(f"no valid judgment JSON found: {direct_error}") from direct_error


def safe_divide(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def binary_metrics(truth: Iterable[bool], predicted: Iterable[bool]) -> dict[str, Any]:
    pairs = list(zip(truth, predicted))
    tp = sum(actual and guess for actual, guess in pairs)
    tn = sum(not actual and not guess for actual, guess in pairs)
    fp = sum(not actual and guess for actual, guess in pairs)
    fn = sum(actual and not guess for actual, guess in pairs)
    valid_precision = safe_divide(tp, tp + fp)
    valid_recall = safe_divide(tp, tp + fn)
    invalid_recall = safe_divide(tn, tn + fp)
    denominator = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    mcc = safe_divide(tp * tn - fp * fn, denominator)
    total = len(pairs)
    observed = safe_divide(tp + tn, total)
    expected = safe_divide((tp + fp) * (tp + fn) + (fn + tn) * (fp + tn), total * total)
    kappa = safe_divide(observed - expected, 1 - expected)
    return {
        "n": total, "tp": tp, "tn": tn, "fp": fp, "fn": fn,
        "accuracy": observed,
        "balanced_accuracy": (valid_recall + invalid_recall) / 2,
        "valid_precision": valid_precision,
        "valid_recall": valid_recall,
        "valid_f1": safe_divide(2 * valid_precision * valid_recall, valid_precision + valid_recall),
        "invalid_recall": invalid_recall, "mcc": mcc, "cohens_kappa": kappa,
    }


def roc_auc(truth: Iterable[bool], scores: Iterable[float]) -> float | None:
    pairs = sorted(zip(scores, truth), key=lambda pair: pair[0])
    positives = sum(label for _, label in pairs)
    negatives = len(pairs) - positives
    if not positives or not negatives:
        return None
    positive_rank_sum = 0.0
    index = 0
    while index < len(pairs):
        end = index + 1
        while end < len(pairs) and pairs[end][0] == pairs[index][0]:
            end += 1
        average_rank = ((index + 1) + end) / 2
        positive_rank_sum += average_rank * sum(label for _, label in pairs[index:end])
        index = end
    return (positive_rank_sum - positives * (positives + 1) / 2) / (positives * negatives)
