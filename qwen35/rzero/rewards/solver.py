"""Solver reward using the upstream verl custom-reward signature."""

from __future__ import annotations

import re
from typing import Any

from qwen35.rzero.rewards.common import extract_boxed, format_reward


def _grade(predict: str, ground_truth: str) -> float:
    from mathruler.grader import grade_answer

    answers = extract_boxed(predict)
    answer = answers[-1] if answers else ""
    try:
        return 1.0 if grade_answer(answer, ground_truth) else 0.0
    except Exception:
        return 0.0


def compute_score(
    data_source: str | None = None,
    solution_str: str = "",
    ground_truth: str = "",
    extra_info: dict[str, Any] | None = None,
    format_weight: float = 0.1,
    **_: Any,
) -> dict[str, float]:
    del data_source, extra_info
    normalized = re.sub(r"\s*(<|>|/)\s*", r"\1", solution_str)
    format_score = format_reward(normalized)
    accuracy_score = _grade(normalized, ground_truth)
    return {
        "score": (1 - format_weight) * accuracy_score + format_weight * format_score,
        "format": format_score,
        "accuracy": accuracy_score,
    }
