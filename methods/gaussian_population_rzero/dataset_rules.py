"""Dependency-free Solver dataset filtering aligned with standard R-Zero."""

from __future__ import annotations


def is_solver_training_record(
    item: dict[str, object], *, min_score: float, max_score: float
) -> bool:
    """Apply the standard score, question, and exact majority-answer filters."""
    score = float(item.get("score", -1))
    question = str(item.get("question", "")).strip()
    answer = str(item.get("answer", "")).strip()
    return min_score <= score <= max_score and bool(question) and answer not in {"", "None"}
