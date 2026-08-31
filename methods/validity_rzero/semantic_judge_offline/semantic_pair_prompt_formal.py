"""Formal recurring-exercise prompt for online semantic-MC diversity."""

PROMPT_VERSION = "semantic-pair-formal-recurring-exercise-v1"
PROMPT_TEMPLATE = (
    "You are judging whether two generated math problems are repetitions of the\n"
    "same recurring exercise pattern.\n\n"
    "Choose SAME_TYPE when the two problems have essentially the same distinctive\n"
    "mathematical setup and ask the same kind of task, so that they feel like\n"
    "variations of the same exercise.\n\n"
    "Differences in constants, coefficients, variables, formulas, bounds, or other\n"
    "local details do not by themselves make the problems different.\n\n"
    "Do not choose SAME_TYPE merely because the problems share a broad topic,\n"
    "similar wording, presentation style.\n\n"
    "If the common pattern is not clear and specific, choose DIFFERENT.\n\n"
    "Briefly compare the exercise pattern of the two problems, then end with exactly\n\n"
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
