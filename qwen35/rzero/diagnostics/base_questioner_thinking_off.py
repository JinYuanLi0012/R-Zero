"""Probe whether forced Qwen3.5 thinking triggers Base Questioner collapse.

This is diagnostic-only.  It restores the released R-Zero Questioner prompt
and changes only the official chat template's ``enable_thinking`` setting.
"""

from __future__ import annotations

from qwen35.rzero.diagnostics.base_questioner import build_parser, run_diagnostic
from qwen35.rzero.prompts import QUESTIONER_MESSAGES


def main() -> None:
    args = build_parser(default_samples=32).parse_args()
    run_diagnostic(
        args,
        QUESTIONER_MESSAGES,
        "qwen35_base_questioner_thinking_off_raw_32.json",
        "qwen35_base_questioner_thinking_off_summary.json",
        "released_rzero_thinking_off",
        enable_thinking=False,
    )


if __name__ == "__main__":
    main()
