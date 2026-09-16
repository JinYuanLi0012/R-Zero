"""Offline open-length comparison, using B's exact four question pairs."""
from .octothinker_judge_fewshot import EXAMPLES
from .semantic_judge_offline.semantic_pair_prompt_formal import PROMPT_TEMPLATE

VERSION = "octo-open-analysis-four-shot-v1"
ANALYSES = [
    "Question A asks for the unknown in a linear equation with one variable. Question B also "
    "asks for the unknown in a linear equation with one variable. In both, a constant multiple "
    "of the unknown plus a constant equals a specified value, so isolating the unknown is the "
    "same mathematical task. The coefficients, constant terms, and variable names differ, "
    "but these are parameters of the same exercise template. Different numerical solutions "
    "would not change that comparison. The defining structure and requested result match.",
    "Both questions describe a circle with the same radius, so their given geometric objects "
    "match. However, A asks for the area inside the circle, whereas B asks for the length of "
    "its boundary. Those are different geometric quantities, not two choices of a numerical "
    "parameter in the same task. The shared circle and radius are therefore insufficient "
    "to make these variants of the same exercise. The requested result is the decisive difference.",
    "A counts arrangements of four distinct objects subject to two specified objects being "
    "adjacent. B counts arrangements of five distinct objects with exactly the same kind "
    "of adjacency requirement. In either case the designated pair can be treated as a block, "
    "with two internal orders, while the remaining objects are arranged around it. Changing "
    "the total number of objects changes the numerical count but not the defining constraint "
    "or the counting task. Thus the different letters and set sizes are parameters of a "
    "shared exercise template.",
    "A asks for integers whose square has a specified value; its defining condition is an "
    "algebraic equation over the integers. B asks for a probability in a fixed sequence of "
    "independent fair coin tosses, with a constraint on how many heads occur. It involves "
    "a random experiment and an event, neither of which occurs in A. Replacing constants "
    "or renaming variables cannot turn finding integer roots into finding this probability. "
    "Their mathematical setups and requested tasks differ.",
]


def build_open_analysis_prompt(a, b):
    text = PROMPT_TEMPLATE.split("Briefly compare", 1)[0]
    text += (
        "Analyze the pair before deciding. Use as much explanation as you need; there is no "
        "required number of sentences or fixed analysis format. Compare what each question "
        "asks for and the constraints that define its exercise pattern. You may discuss the "
        "relevant mathematical approach when helpful; fully solving either problem is not "
        "required. Your final answer is the exercise-type classification, not the numerical "
        "answers to the questions. End with exactly one label, \\boxed{SAME_TYPE} or "
        "\\boxed{DIFFERENT}, and then stop.\n\n"
    )
    for i, ((qa, qb, label, _), analysis) in enumerate(zip(EXAMPLES, ANALYSES), 1):
        text += (f"Example {i}\nQuestion A:\n{qa}\nQuestion B:\n{qb}\n"
                 f"Analysis: {analysis}\nConclusion: \\boxed{{{label}}}\n\n")
    return text + f"Now compare this pair.\nQuestion A:\n{a}\nQuestion B:\n{b}\nAnalysis:"
