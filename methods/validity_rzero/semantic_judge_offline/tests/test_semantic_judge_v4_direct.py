from __future__ import annotations

import sys
import unittest
from pathlib import Path


METHOD = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(METHOD))

from compare_v4_direct import compare  # noqa: E402
from run_pair_judge_v3_vllm import (  # noqa: E402
    DEFAULT_MAX_TOKENS, STOP_STRINGS, parse_response_v3, sampling_options,
)
from run_pair_judge_v4_direct import PROMPT_TEMPLATE, build_prompt, make_conditions  # noqa: E402


class DirectProtocolTests(unittest.TestCase):
    def test_prompt_is_direct_and_contains_no_analysis_request(self):
        prompt = build_prompt("alpha", "beta")
        self.assertEqual(prompt, PROMPT_TEMPLATE.replace("{question_a}", "alpha").replace(
            "{question_b}", "beta"
        ))
        self.assertIn("Do not explain.", prompt)
        self.assertNotIn("Analysis:", prompt)
        self.assertNotIn("brief justification", prompt.lower())
        self.assertTrue(prompt.endswith("Answer:"))
        self.assertNotIn("P001", prompt)

    def test_two_orders_only(self):
        rows = make_conditions([{"pair_id": "P001", "q1": "one", "q2": "two"}])
        self.assertEqual([row.question_order for row in rows], ["q1_q2", "q2_q1"])

    def test_sampling_stop_and_parser_are_shared_with_v3(self):
        options = sampling_options(DEFAULT_MAX_TOKENS, 42)
        self.assertEqual(options["max_tokens"], 1024)
        self.assertEqual(options["stop"], list(STOP_STRINGS))
        self.assertTrue(options["include_stop_str_in_output"])
        self.assertEqual(parse_response_v3(r"\boxed{SAME_TYPE}.")["parsed_label"], "SAME_TYPE")


class ComparisonTests(unittest.TestCase):
    def test_accuracy_format_and_runtime_deltas(self):
        condition = lambda accuracy, formats: {
            "accuracy_end_to_end": accuracy,
            "accuracy_parseable_only": 1.0,
            "format_errors": formats,
            "format_error_rate": formats / 50,
        }
        baseline_metrics = {
            "conditions": {"q1_q2": condition(0.94, 1), "q2_q1": condition(0.82, 4)},
            "order_stability": {"both_orders_parseable": 45},
        }
        direct_metrics = {
            "conditions": {"q1_q2": condition(0.90, 0), "q2_q1": condition(0.88, 1)},
            "order_stability": {"both_orders_parseable": 49},
        }
        manifest = lambda mean, throughput, generation, total: {"runtime": {
            "tokens": {"generated": {"mean": mean}},
            "throughput": {"output_tokens_per_second": throughput, "conditions_per_second": 25},
            "timing_seconds": {"generation_wall": generation, "total_wall": total},
        }}
        result = compare(
            baseline_metrics, direct_metrics,
            manifest(100, 1000, 4, 10), manifest(10, 200, 2, 8),
        )
        self.assertAlmostEqual(
            result["orders"]["q1_q2"]["accuracy_end_to_end"]["delta_direct_minus_baseline"],
            -0.04,
        )
        self.assertEqual(
            result["orders"]["q1_q2"]["format_errors"]["delta_direct_minus_baseline"], -1
        )
        self.assertEqual(
            result["runtime"]["mean_generated_tokens"]["delta_direct_minus_baseline"], -90
        )


if __name__ == "__main__":
    unittest.main()
