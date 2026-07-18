"""Shared answer extraction and equivalence helpers."""

from __future__ import annotations

import stopit
from mathruler.grader import extract_boxed_content, grade_answer


@stopit.threading_timeoutable(default=False)
def _grade(left: str, right: str) -> bool:
    return bool(grade_answer(left, right))


def extract_answer(text: str) -> str:
    value = extract_boxed_content(text)
    if isinstance(value, (list, tuple)):
        return str(value[-1]).strip() if value else ""
    return str(value or "").strip()


def answers_equivalent(left: str, right: str, timeout: float = 10.0) -> bool:
    left, right = str(left).strip(), str(right).strip()
    if not left or not right:
        return False
    if left == right or ("no " in left.lower() and "no " in right.lower()):
        return True
    return bool(_grade(left, right, timeout=timeout) or _grade(right, left, timeout=timeout))
