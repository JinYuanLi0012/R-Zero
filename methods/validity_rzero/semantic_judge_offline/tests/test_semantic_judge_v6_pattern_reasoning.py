from __future__ import annotations

import sys
import unittest
from pathlib import Path


METHOD = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(METHOD))

from run_pair_judge_v3_vllm import (  # noqa: E402
    DEFAULT_MAX_TOKENS, STOP_STRINGS, parse_response_v3, sampling_options,
)
from run_pair_judge_v5_pattern import PROMPT_TEMPLATE as V5_PROMPT_TEMPLATE  # noqa: E402
from run_pair_judge_v6_pattern_reasoning import (  # noqa: E402
    PROMPT_TEMPLATE, PROMPT_VERSION, build_prompt, make_conditions,
)


class PatternReasoningPromptTests(unittest.TestCase):
    def test_only_response_instruction_changes_from_v5(self):
        semantic_definition = V5_PROMPT_TEMPLATE.split("Output exactly", 1)[0]
        self.assertEqual(
            PROMPT_TEMPLATE.split("Briefly compare", 1)[0], semantic_definition
        )
        prompt = build_prompt("alpha", "beta")
        self.assertEqual(PROMPT_VERSION, "semantic-pair-v6-exercise-pattern-brief-reasoning")
        self.assertIn("Briefly compare the overall exercise pattern", prompt)
        self.assertIn("\\boxed{SAME_TYPE}\n\nor\n\n\\boxed{DIFFERENT}.", prompt)
        self.assertNotIn("Do not explain.", prompt)
        self.assertTrue(prompt.endswith("Analysis:"))

    def test_only_two_orders_and_no_pair_id_in_prompt(self):
        rows = make_conditions([{"pair_id": "P001", "q1": "one", "q2": "two"}])
        self.assertEqual([row.question_order for row in rows], ["q1_q2", "q2_q1"])
        self.assertTrue(all("P001" not in row.prompt for row in rows))

    def test_generation_and_parser_contract_are_unchanged(self):
        options = sampling_options(DEFAULT_MAX_TOKENS, 42)
        self.assertEqual(DEFAULT_MAX_TOKENS, 1024)
        self.assertEqual(options["stop"], list(STOP_STRINGS))
        self.assertTrue(options["include_stop_str_in_output"])
        self.assertEqual(options["temperature"], 0.6)
        self.assertEqual(options["top_p"], 0.95)
        self.assertEqual(options["top_k"], 20)
        self.assertEqual(options["presence_penalty"], 1.5)
        self.assertEqual(options["seed"], 42)
        parsed = parse_response_v3("Short comparison. " + r"\boxed{SAME\_TYPE}.")
        self.assertEqual(parsed["parsed_label"], "SAME_TYPE")


if __name__ == "__main__":
    unittest.main()
