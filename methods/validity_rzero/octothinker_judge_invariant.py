"""Final offline instruction-only revision; preserves B's demonstrations."""
from .octothinker_judge_fewshot import EXAMPLES

VERSION = "octo-invariant-instructions-v1"


def build_invariant_prompt(a, b):
    text = (
        "Classify whether two math questions are variants of the SAME EXERCISE TEMPLATE. "
        "Do not solve them and do not compare their numerical answers.\n\n"
        "Decision rules:\n"
        "1. Identify what each question actually asks to find, and the defining mathematical "
        "relations or constraints it gives. Read A and B separately; do not attribute B's task to A.\n"
        "2. Treat variable names, object names, story wording, units, coefficients, counts, "
        "and numerical parameter values as replaceable slots. Changing these slots alone is "
        "SAME_TYPE, even if the resulting answers differ. Identical questions and consistent "
        "renamings are SAME_TYPE. A different equation's coefficients do not by themselves "
        "make a different equation type.\n"
        "3. If both have the same defining constraints and request the same kind of result "
        "after those replacements, choose SAME_TYPE. Equivalent mathematical wording or a "
        "different story can express the same structure.\n"
        "4. Choose DIFFERENT when the defining relation, structural constraint, or requested "
        "quantity differs beyond those replacements. Sharing a broad topic alone is insufficient. "
        "Preserve distinctions such as sum versus product, with versus without replacement, "
        "allowed versus forbidden adjacency, counting versus optimization, and area versus length.\n\n"
        "Output one or two short comparison sentences, then exactly one final label: "
        "\\boxed{SAME_TYPE} or \\boxed{DIFFERENT}. For SAME_TYPE state the shared template. "
        "For DIFFERENT name the actual structural or target difference in the supplied text; "
        "a changed number or name is not a sufficient reason. Do not invent an area, perimeter, "
        "role assignment, or other requirement absent from the questions. Stop after the label.\n\n"
    )
    for i, (qa, qb, label, reason) in enumerate(EXAMPLES, 1):
        text += (f"Example {i}\nQuestion A:\n{qa}\nQuestion B:\n{qb}\n"
                 f"Classification: {reason} \\boxed{{{label}}}\n\n")
    return text + f"Now classify this pair. Do not solve either problem.\nQuestion A:\n{a}\nQuestion B:\n{b}\nClassification:"
