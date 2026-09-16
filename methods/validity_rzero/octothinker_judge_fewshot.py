"""Offline-only prompt experiment. Demonstrations and control pairs are disjoint."""
from .semantic_judge_offline.semantic_pair_prompt_formal import PROMPT_TEMPLATE

VERSION = "octo-classification-four-shot-v1"
EXAMPLES = [
    ("Solve 3x + 5 = 20.", "Solve 7y - 2 = 26.", "SAME_TYPE",
     "Both ask for the unknown in a one-variable linear equation; only constants change."),
    ("Find the area of a circle of radius 3.", "Find the circumference of a circle of radius 3.", "DIFFERENT",
     "The shared circle is not enough: one asks for area and the other for boundary length."),
    ("How many arrangements of A, B, C, D have A and B adjacent?",
     "How many arrangements of P, Q, R, S, T have P and Q adjacent?", "SAME_TYPE",
     "Both count permutations under the same two-items-adjacent constraint."),
    ("Find all integers x with x squared equal to 25.",
     "Find the probability of exactly two heads in three fair coin tosses.", "DIFFERENT",
     "Solving an integer equation and counting outcomes of independent trials are distinct tasks."),
]


def build_fewshot_prompt(a, b):
    rules = PROMPT_TEMPLATE.split("Briefly compare", 1)[0]
    text = (rules + "Your task is classification, NOT solving Question A or Question B.\n"
            "Do not calculate their answers, repeat their statements, or add new questions.\n"
            "Write one short sentence comparing the exercise patterns, followed by exactly one final label: "
            "\\boxed{SAME_TYPE} or \\boxed{DIFFERENT}. Then stop.\n\n")
    for i, (qa, qb, label, reason) in enumerate(EXAMPLES, 1):
        text += (f"Example {i}\nQuestion A:\n{qa}\nQuestion B:\n{qb}\n"
                 f"Classification: {reason} \\boxed{{{label}}}\n\n")
    return text + f"Now classify this pair. Do not solve either problem.\nQuestion A:\n{a}\nQuestion B:\n{b}\nClassification:"


def controls():
    data = [
        ("Find the sum of the first 20 terms of an arithmetic sequence with first term 3 and common difference 4.",
         "Find the sum of the first 35 terms of an arithmetic sequence with first term 7 and common difference 2.", "SAME_TYPE"),
        ("From a box containing 5 red and 7 blue balls, draw two without replacement. What is the probability both are red?",
         "From a bag containing 4 green and 9 yellow balls, draw two without replacement. What is the probability both are green?", "SAME_TYPE"),
        ("Find the sum of the first 20 positive integers.",
         "Find the number of positive divisors of 360.", "DIFFERENT"),
        ("Find the number of real roots of x squared minus 5x plus 6 equal to zero.",
         "Find the minimum value of x squared minus 5x plus 6 over all real x.", "DIFFERENT"),
    ]
    return [{"pair_id": f"control_{i}", "source": "synthetic_control", "expected_label": label,
             "a": {"question": a}, "b": {"question": b}} for i, (a, b, label) in enumerate(data)]
