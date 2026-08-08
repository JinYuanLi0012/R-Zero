"""Parsing and answer-equivalence helpers shared by R-Zero stages."""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable


QUESTION_PATTERN = re.compile(r"<question>(.*?)</question>", re.DOTALL)
FORMAT_PATTERN = re.compile(r"<think>.*</think>.*\\boxed\{.*\}.*", re.DOTALL)


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


def answers_equivalent(left: str, right: str, grader: Callable[[str, str], bool]) -> bool:
    if left == right:
        return True
    if "no " in left.lower() and "no " in right.lower():
        return True
    try:
        return bool(grader(left, right) or grader(right, left))
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
