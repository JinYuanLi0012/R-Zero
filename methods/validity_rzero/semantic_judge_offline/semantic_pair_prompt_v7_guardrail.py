"""V7 exercise-pattern prompt: V6 plus one domain-agnostic specificity guardrail."""

from __future__ import annotations


PROMPT_VERSION = "semantic-pair-v7-exercise-pattern-specificity-guardrail"
PROMPT_TEMPLATE = (
    "You are judging whether two generated math problems are repetitions of the\n"
    "same exercise pattern for diversity control.\n\n"
    "Choose SAME_TYPE when a human reviewing many generated questions would say:\n"
    '"this is basically the same kind of exercise again."\n\n'
    "The problems do NOT need to have the same constants, formulas, coefficients,\n"
    "variables, number of variables, bounds, or detailed solution steps.\n\n"
    "Focus on the overall exercise pattern:\n"
    "what kind of mathematical setup is presented, and what kind of task the\n"
    "student is being asked to perform.\n\n"
    "Local changes to the setup may still count as the same type if the overall\n"
    "exercise feels like a natural variation of the same recurring pattern.\n\n"
    "Do not choose SAME_TYPE merely because the problems share a broad subject,\n"
    "use similar mathematical vocabulary, or both ask for something generic such\n"
    "as an integer, a maximum, a count, or a remainder.\n\n"
    "Do not reduce the two problems to a generic task shell.\n"
    "The distinctive mathematical construction in the setup must also feel like\n"
    "the same recurring exercise pattern.\n\n"
    "If the similarity you identified would apply equally well to many unrelated\n"
    "math problems, choose DIFFERENT.\n\n"
    "If they feel like genuinely different kinds of exercises, choose DIFFERENT.\n\n"
    "If a problem is incomplete or not really a math problem, choose DIFFERENT\n"
    "unless both are clearly repetitions of the same malformed pattern.\n\n"
    "Briefly compare the overall exercise pattern of the two problems, then end\n"
    "with exactly\n\n"
    "\\boxed{SAME_TYPE}\n\n"
    "or\n\n"
    "\\boxed{DIFFERENT}.\n\n"
    "Question A:\n{question_a}\n\n"
    "Question B:\n{question_b}\n\n"
    "Analysis:"
)


def build_prompt(question_a: str, question_b: str) -> str:
    return PROMPT_TEMPLATE.replace("{question_a}", question_a).replace(
        "{question_b}", question_b
    )
