"""Offline-only structured comparison experiment; not the production prompt."""
from .semantic_judge_offline.semantic_pair_prompt_formal import PROMPT_TEMPLATE
from .octothinker_judge_fewshot import controls

VERSION = "octo-three-shot-structural-comparison-v1"
EXAMPLES = [
    ("A triangle has sides 13, 14, 15. Find its inradius.",
     "A triangle has sides 10, 17, 21. Determine the radius of its inscribed circle.",
     "SAME_TYPE",
     "A gives three side lengths and asks for the triangle's inradius. B gives the same kind of data and asks for the same geometric quantity in different wording. Both use the side-length-to-area-to-inradius setup; only numerical parameters change."),
    ("Count length-eight binary strings with exactly three ones.",
     "Count length-eight binary strings with no consecutive ones.",
     "DIFFERENT",
     "A fixes the number of ones, so the structure is choosing their positions. B imposes a local adjacency restriction without fixing the number of ones. The objects and requested count look alike, but the defining constraints produce different exercise patterns."),
    ("Find all integers x such that x squared minus 6x plus 5 is a perfect square.",
     "Find the minimum of x squared minus 6x plus 5 over all real x.",
     "DIFFERENT",
     "A asks which integer inputs make a polynomial a square, a discrete arithmetic constraint. B asks for the smallest real value of a quadratic, an optimization task. Sharing the exact polynomial does not make their targets or mathematical setups the same."),
]


def build_three_shot_prompt(a, b):
    text = PROMPT_TEMPLATE.split("Briefly compare", 1)[0]
    text += ("Classify the exercise patterns; do not solve either problem. In 2-4 concise sentences, "
             "identify A's defining setup and requested task, identify B's, then compare their "
             "specific constraints and targets. Ground each statement in the actual questions. "
             "Do not infer similarity just from a shared topic or the word 'count'. "
             "End with exactly one label: \\boxed{SAME_TYPE} or \\boxed{DIFFERENT}. Then stop.\n\n")
    for i, (qa, qb, label, reason) in enumerate(EXAMPLES, 1):
        text += (f"Example {i}\nQuestion A:\n{qa}\nQuestion B:\n{qb}\n"
                 f"Comparison: {reason} \\boxed{{{label}}}\n\n")
    return text + f"Now classify this pair.\nQuestion A:\n{a}\nQuestion B:\n{b}\nComparison:"


def expanded_controls():
    """Twelve labeled pairs, balanced; none duplicates a demonstration."""
    data = [
        ("Find the remainder when 7 to the power 100 is divided by 13.",
         "Find the remainder when 3 to the power 80 is divided by 11.", "SAME_TYPE"),
        ("Two workers finish a job alone in 6 and 9 hours. How long working together?",
         "Two pipes fill a tank alone in 4 and 10 hours. How long with both open?", "SAME_TYPE"),
        ("Find the center and radius of x^2+y^2-4x+6y-12=0.",
         "Determine the center and radius of x^2+y^2+8x-2y-8=0.", "SAME_TYPE"),
        ("How many onto functions map a five-element set to a three-element set?",
         "How many surjections are there from a seven-element set to a four-element set?", "SAME_TYPE"),
        ("Find the last two digits of 7 to the power 100.",
         "Find how many positive divisors 7 to the power 100 has.", "DIFFERENT"),
        ("A fair die is rolled six times. Find the probability of exactly two sixes.",
         "A fair die is rolled until the first six. Find the expected number of rolls.", "DIFFERENT"),
        ("Find the number of integer lattice points on x^2+y^2=25.",
         "Find the area enclosed by x^2+y^2=25.", "DIFFERENT"),
        ("Find the maximum product of positive real x and y with x+y=12.",
         "Count ordered positive integer pairs x,y with x+y=12.", "DIFFERENT"),
    ]
    return controls() + [{"pair_id": f"extended_control_{i}", "source": "synthetic_control",
                         "expected_label": label, "a": {"question": a}, "b": {"question": b}}
                        for i, (a, b, label) in enumerate(data)]
