"""Offline balanced demonstrations and separate elementary ability checks."""

VERSION = "octo-balanced-four-short-comparison-v1"
EXAMPLES = [
    ("A rectangle has perimeter 30 and length twice its width. Find its area.",
     "A rectangular garden has perimeter 42 and length twice its width. Find its area.",
     "SAME_TYPE", "Both give a rectangle's perimeter and the same length-to-width ratio, and ask for area. Only a numerical parameter and story wording change, so these are variants of the same exercise."),
    ("Count arrangements of six distinct books in which two specified books are adjacent.",
     "Count arrangements of six distinct books in which two specified books are not adjacent.",
     "DIFFERENT", "Both count arrangements of the same objects, but one requires adjacency and the other forbids it. This changes the key constraint, not just a number or name."),
    ("Find all real t satisfying |2t-3|=7.",
     "Find all real u satisfying |5u+1|=9.",
     "SAME_TYPE", "Both ask for real solutions of the absolute value of a linear expression equaling a positive constant. Coefficients and variable names change, but the constraint and requested task stay the same."),
    ("A cube has edge length 5. Find its volume.",
     "A cube has edge length 5. Find its surface area.",
     "DIFFERENT", "Both give the same cube, but one asks for volume and the other for surface area. The requested quantities differ, so the exercises are not the same type."),
]


def build_balanced_prompt(a, b):
    text = (
        "Compare two math exercises, without solving them.\n"
        "Imagine ignoring the particular numbers, variable names, and story wording: do the "
        "problems still have the same key mathematical constraints and ask for the same kind of result?\n"
        "SAME_TYPE means variations of the same exercise: those key constraints and the requested "
        "task match. Changes to numerical parameters, names, or wording ALONE mean SAME_TYPE, not DIFFERENT.\n"
        "DIFFERENT means a key mathematical constraint or the requested task changes. Sharing a "
        "broad topic or the exact formula alone does not mean SAME_TYPE.\n"
        "Write about two short sentences identifying the matching structure or the decisive "
        "difference. Then give exactly one final label: \\boxed{SAME_TYPE} or \\boxed{DIFFERENT}. Stop.\n\n"
    )
    for i, (qa, qb, label, reason) in enumerate(EXAMPLES, 1):
        text += (f"Example {i}\nQuestion A:\n{qa}\nQuestion B:\n{qb}\n"
                 f"Comparison: {reason} \\boxed{{{label}}}\n\n")
    return text + f"Now compare this pair.\nQuestion A:\n{a}\nQuestion B:\n{b}\nComparison:"


def sanity_checks():
    data = [
        ("identical", "Find the greatest common divisor of 48 and 72.",
         "Find the greatest common divisor of 48 and 72.", "SAME_TYPE"),
        ("identical", "How many subsets of size three does a seven-element set have?",
         "How many subsets of size three does a seven-element set have?", "SAME_TYPE"),
        ("numbers_only", "Find the greatest common divisor of 48 and 72.",
         "Find the greatest common divisor of 60 and 90.", "SAME_TYPE"),
        ("numbers_only", "How many subsets of size three does a seven-element set have?",
         "How many subsets of size four does a nine-element set have?", "SAME_TYPE"),
        ("variables_only", "Find all real x satisfying x^3=8.",
         "Find all real y satisfying y^3=8.", "SAME_TYPE"),
        ("variables_only", "Find all positive integers n such that n divides 24.",
         "Find all positive integers k such that k divides 24.", "SAME_TYPE"),
        ("constraint_changed", "Count length-five strings over digits 0 to 9, allowing repeated digits.",
         "Count length-five strings over digits 0 to 9, with no repeated digits.", "DIFFERENT"),
        ("constraint_changed", "Count ordered integer pairs x,y with x+y=10 and x,y strictly positive.",
         "Count ordered integer pairs x,y with x*y=10 and x,y strictly positive.", "DIFFERENT"),
    ]
    return [{"pair_id": f"sanity_{i}", "source": "sanity_check", "sanity_kind": kind,
             "expected_label": label, "a": {"question": a}, "b": {"question": b}}
            for i, (kind, a, b, label) in enumerate(data)]
