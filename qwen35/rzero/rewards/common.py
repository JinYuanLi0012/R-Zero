"""Parsing and answer-equivalence helpers shared by R-Zero stages."""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable
from functools import lru_cache


QUESTION_PATTERN = re.compile(r"<question>(.*?)</question>", re.DOTALL)
FORMAT_PATTERN = re.compile(r"<think>.*</think>.*\\boxed\{.*\}.*", re.DOTALL)
GRADER_TIMEOUT_SECONDS = 10.0


@lru_cache(maxsize=1)
def _timeoutable_grader():
    """Build the stopit wrapper lazily so parsing-only tooling stays lightweight."""
    import stopit

    @stopit.threading_timeoutable(default=False)
    def invoke(grader: Callable[[str, str], bool], left: str, right: str) -> bool:
        return bool(grader(left, right))

    return invoke


def _grade_answer_with_timeout(
    grader: Callable[[str, str], bool], left: str, right: str, timeout_seconds: float
) -> bool:
    return bool(_timeoutable_grader()(grader, left, right, timeout=timeout_seconds))


def extract_boxed(text: str) -> list[str]:
    """Extract balanced ``\\boxed{...}`` values without assuming flat braces."""
    results: list[str] = []
    prefix = "\\boxed{"
    cursor = 0
    while True:
        start = text.find(prefix, cursor)
        if start < 0:
            return results
        index = start + len(prefix)
        depth = 1
        while index < len(text) and depth:
            if text[index] == "{":
                depth += 1
            elif text[index] == "}":
                depth -= 1
            index += 1
        if depth == 0:
            results.append(text[start + len(prefix) : index - 1])
        cursor = max(index, start + len(prefix))


def parse_questioner_response(text: str) -> dict[str, str]:
    questions = QUESTION_PATTERN.findall(text)
    answers = extract_boxed(text)
    if not questions or not answers:
        return {"question": "", "answer": ""}
    return {"question": questions[-1].strip(), "answer": answers[-1].strip()}


def format_reward(text: str) -> float:
    return 1.0 if FORMAT_PATTERN.fullmatch(text) else 0.0


def answers_equivalent(
    left: str,
    right: str,
    grader: Callable[[str, str], bool],
    timeout_seconds: float = GRADER_TIMEOUT_SECONDS,
) -> bool:
    if left == right:
        return True
    if "no " in left.lower() and "no " in right.lower():
        return True
    try:
        return _grade_answer_with_timeout(grader, left, right, timeout_seconds) or _grade_answer_with_timeout(
            grader, right, left, timeout_seconds
        )
    except Exception:
        return False


def majority_vote(
    answers: Iterable[str], grader: Callable[[str, str], bool]
) -> tuple[str, int, list[str]]:
    valid = [answer for answer in answers if answer]
    counts: dict[str, int] = {}
    for answer in valid:
        for representative in list(counts):
            if answers_equivalent(answer, representative, grader):
                counts[representative] += 1
                break
        else:
            counts[answer] = 1
    if not counts:
        return "", 0, valid
    majority = max(counts, key=counts.get)
    return majority, counts[majority], valid
