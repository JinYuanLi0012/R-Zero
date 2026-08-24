"""Single-variable Base Questioner prompt diagnostic.

The official Qwen3.5 thinking template remains enabled.  Only the released
prompt's explicit request to think about designing the problem is removed.
"""

from __future__ import annotations

from qwen35.rzero.diagnostics.base_questioner import build_parser, run_diagnostic


QUESTIONER_NO_EXPLICIT_META_THINKING_MESSAGES = [
    {
        "role": "system",
        "content": (
            "You are an expert competition-math problem setter.\n"
            "Design a brand-new, non-trivial problem. "
            "The problem could come from any field of mathematics, including but not limited to algebra, geometry, "
            "number theory, combinatorics, prealgebra, probability, statistics, and calculus. "
            "Aim for a difficulty such that fewer than 30 % of advanced high-school students could solve it. "
            "Avoid re-using textbook clichés or famous contest problems.\n"
            "Output **exactly** the following two blocks:\n\n"
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


def main() -> None:
    args = build_parser(default_samples=64).parse_args()
    run_diagnostic(
        args,
        QUESTIONER_NO_EXPLICIT_META_THINKING_MESSAGES,
        "qwen35_base_questioner_no_meta_raw_64.json",
        "qwen35_base_questioner_no_meta_summary.json",
        "no_explicit_meta_thinking",
    )


if __name__ == "__main__":
    main()
