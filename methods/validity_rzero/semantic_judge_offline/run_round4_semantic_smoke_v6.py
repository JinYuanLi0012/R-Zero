#!/usr/bin/env python3
"""Run the fixed Round-4 2048x128 smoke with the V6 reasoning prompt."""

from __future__ import annotations

from pathlib import Path
import sys

if __package__ in {None, ""}:  # Support the documented direct-script command.
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from methods.validity_rzero.semantic_judge_offline.run_pair_judge_v6_pattern_reasoning import (
    PROMPT_TEMPLATE,
    PROMPT_VERSION,
    build_prompt,
)
from methods.validity_rzero.semantic_judge_offline.run_round4_semantic_smoke import (
    arguments,
    run_smoke,
)


def main() -> None:
    args = arguments(__doc__)
    run_smoke(
        args,
        prompt_version=PROMPT_VERSION,
        prompt_template=PROMPT_TEMPLATE,
        prompt_builder=build_prompt,
        artifact_stem="semantic_smoke_v6_pattern_reasoning",
        experiment="round4_semantic_mc_smoke_2048x128_v6_pattern_reasoning",
        controlled_baseline="round4_semantic_mc_smoke_2048x128_v1",
        only_intended_variable="semantic judge prompt changed to V6 brief reasoning",
        report_title="Round-4 semantic Monte Carlo smoke — V6 brief reasoning",
    )


if __name__ == "__main__":
    main()
