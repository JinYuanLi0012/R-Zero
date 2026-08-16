#!/usr/bin/env python3
"""Prompts and pure utilities for the binary few-shot logprob Judge."""

from __future__ import annotations

import hashlib
import math
from typing import Any


EXPERIMENT_VERSION = "binary-fewshot-logprob-v1"
VARIANTS = ("direct", "solver_first")
VALID_CANDIDATE = " VALID"
INVALID_CANDIDATE = " INVALID"

DEFINITION = """Classify whether a mathematical problem is valid exactly as written.
VALID: The conditions are sufficient and consistent, a solution exists, and the complete answer is objectively gradable. A problem may have multiple solutions and still be VALID when it asks for all of them.
INVALID: Information is missing or ambiguous, the conditions are contradictory, no requested solution exists, the problem is malformed, or the answer cannot be objectively graded."""

DIRECT_EXAMPLES = """Example 1
Question: What is 2 + 3?
Analysis: The question is complete, consistent, and has one clear answer.
Verdict: VALID

Example 2
Question: A triangle has side lengths 1, 1, and 3. Find its area.
Analysis: These lengths cannot form a triangle, so the stated object does not exist.
Verdict: INVALID

Example 3
Question: Let x be a real number. Find x.
Analysis: There is not enough information to determine x.
Verdict: INVALID

Example 4
Question: Solve x^2 = 4 over the real numbers.
Analysis: The problem is complete and the full answer x = -2 or x = 2 is objectively checkable.
Verdict: VALID"""

SOLVER_FIRST_EXAMPLES = """Example 1
Question: What is 2 + 3?
Analysis: Solving gives 5. All required information is present and the answer is objectively checkable.
Verdict: VALID

Example 2
Question: A triangle has side lengths 1, 1, and 3. Find its area.
Analysis: Before computing an area, check existence. The triangle inequality fails because 1 + 1 is not greater than 3, so no such triangle exists.
Verdict: INVALID

Example 3
Question: Let x be a real number. Find x.
Analysis: Attempting to solve reveals no equation or other constraint on x, so infinitely many unrelated values remain possible.
Verdict: INVALID

Example 4
Question: Solve x^2 = 4 over the real numbers.
Analysis: Factoring gives (x - 2)(x + 2) = 0, hence the complete answer is x = -2 or x = 2. Multiple listed solutions do not make a find-all problem ambiguous.
Verdict: VALID"""


def build_prompt(question: str, variant: str) -> str:
    if variant not in VARIANTS:
        raise ValueError(f"unknown prompt variant: {variant}")
    if variant == "direct":
        instruction = """Analyze the target problem carefully. Check whether its conditions are sufficient, whether a requested solution actually exists, and whether the complete answer is objectively gradable. Continue with one concise Analysis paragraph. Do not write the Verdict yet."""
        examples = DIRECT_EXAMPLES
    else:
        instruction = """Solve the target problem carefully first. While solving, explicitly check for missing information, contradictions, impossibility, or multiple reasonable interpretations. Continue with one concise Analysis paragraph. Do not write the Verdict yet."""
        examples = SOLVER_FIRST_EXAMPLES
    return f"{DEFINITION}\n\n{instruction}\n\n{examples}\n\nTarget\nQuestion: {question}\nAnalysis:"


def prompt_hash(variant: str) -> str:
    return hashlib.sha256(build_prompt("__QUESTION__", variant).encode("utf-8")).hexdigest()


def paired_probability(logprob_valid: float, logprob_invalid: float) -> float:
    if not math.isfinite(logprob_valid) or not math.isfinite(logprob_invalid):
        raise ValueError("candidate logprobs must be finite")
    maximum = max(logprob_valid, logprob_invalid)
    valid_weight = math.exp(logprob_valid - maximum)
    invalid_weight = math.exp(logprob_invalid - maximum)
    return valid_weight / (valid_weight + invalid_weight)


def selected_token_logprob(entry: Any, token_id: int) -> float:
    """Read the selected prompt token from vLLM's int-keyed Logprob mapping."""
    if entry is None:
        raise ValueError("prompt logprob entry is missing")
    value = entry.get(token_id)
    if value is None:
        value = entry.get(str(token_id))
    if value is None:
        raise ValueError(f"prompt logprob does not contain selected token {token_id}")
    result = float(getattr(value, "logprob", value))
    if not math.isfinite(result):
        raise ValueError("selected token logprob is not finite")
    return result


def candidate_logprob(output: Any, candidate_start: int, candidate_ids: list[int]) -> float:
    prompt_logprobs = output.prompt_logprobs
    if prompt_logprobs is None or len(prompt_logprobs) != len(output.prompt_token_ids):
        raise ValueError("vLLM did not return complete prompt logprobs")
    if list(output.prompt_token_ids[candidate_start:]) != list(candidate_ids):
        raise ValueError("scored prompt does not end in the expected candidate tokens")
    return sum(
        selected_token_logprob(prompt_logprobs[candidate_start + offset], token_id)
        for offset, token_id in enumerate(candidate_ids)
    )
