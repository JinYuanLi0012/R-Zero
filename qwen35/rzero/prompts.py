"""Prompt text copied from the released R-Zero implementation."""

QUESTIONER_MESSAGES = [
    {
        "role": "system",
        "content": (
            "You are an expert competition-math problem setter.\n"
            "FIRST, in your private scratch-pad, think step-by-step to design a brand-new, non-trivial problem. "
            "The problem could come from any field of mathematics, including but not limited to algebra, geometry, "
            "number theory, combinatorics, prealgebra, probability, statistics, and calculus. "
            "Aim for a difficulty such that fewer than 30 % of advanced high-school students could solve it. "
            "Avoid re-using textbook clichés or famous contest problems.\n"
            "THEN, without revealing any of your private thoughts, output **exactly** the following two blocks:\n\n"
            "<question>\n{The full problem statement on one or more lines}\n</question>\n\n"
            "\\boxed{final_answer}\n\n"
            "Do NOT output anything else—no explanations, no extra markup."
        ),
    },
    {
        "role": "user",
        "content": "Generate one new, challenging reasoning question now. Remember to format the output exactly as instructed.",
    },
]

SOLVER_SYSTEM_PROMPT = "Please reason step by step, and put your final answer within \\boxed{}."


def solver_messages(problem: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SOLVER_SYSTEM_PROMPT},
        {"role": "user", "content": problem},
    ]
