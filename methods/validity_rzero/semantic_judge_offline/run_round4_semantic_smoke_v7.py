#!/usr/bin/env python3
"""Run the fixed Round-4 2048x128 smoke with the V7 specificity guardrail."""

from __future__ import annotations

from pathlib import Path
import sys

if __package__ in {None, ""}:  # Support the documented direct-script command.
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from methods.validity_rzero.semantic_judge_offline.run_round4_semantic_smoke import (
    arguments,
    run_smoke,
)
from methods.validity_rzero.semantic_judge_offline.semantic_pair_prompt_v7_guardrail import (
    PROMPT_TEMPLATE,
    PROMPT_VERSION,
    build_prompt,
)


def main() -> None:
    args = arguments(__doc__)
    run_smoke(
        args,
        prompt_version=PROMPT_VERSION,
        prompt_template=PROMPT_TEMPLATE,
        prompt_builder=build_prompt,
        artifact_stem="semantic_smoke_v7_pattern_guardrail",
        experiment="round4_semantic_mc_smoke_2048x128_v7_pattern_guardrail",
        controlled_baseline="round4_semantic_mc_smoke_2048x128_v6_pattern_reasoning",
        only_intended_variable=(
            "V7 domain-agnostic specificity guardrail added to the frozen V6 prompt"
        ),
        report_title="Round-4 semantic Monte Carlo smoke — V7 specificity guardrail",
        pair_orientation="candidate_then_reference_v1",
        inference_order="candidate_grouped_panel_order_v1",
    )


if __name__ == "__main__":
    main()
