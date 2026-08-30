from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


METHOD = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(METHOD))

from run_pair_judge_v2 import PROMPT_TEMPLATE as V2_PROMPT_TEMPLATE  # noqa: E402
from run_pair_judge_v3_vllm import (  # noqa: E402
    PROMPT_TEMPLATE, STOP_STRINGS, load_generation_config, parse_response_v3,
    runtime_metrics, sampling_options,
)
from score_pair_judge_v3 import analyze, validate_and_join  # noqa: E402


class ParserV3Tests(unittest.TestCase):
    def assert_label(self, response, expected):
        parsed = parse_response_v3(response)
        self.assertEqual(parsed["predicted_label"], expected)
        self.assertEqual(parsed["format_status"], "ok")
        self.assertIsNone(parsed["format_error_reason"])

    def test_prompt_is_unchanged_from_confirmed_v2(self):
        self.assertEqual(PROMPT_TEMPLATE, V2_PROMPT_TEMPLATE)

    def test_trailing_punctuation_and_text_are_accepted(self):
        self.assert_label(r"Reason. \boxed{SAME_TYPE}.", "SAME_TYPE")
        self.assert_label(r"Reason. \boxed{DIFFERENT} -- done afterward", "DIFFERENT")

    def test_text_and_escaped_underscore_variants(self):
        self.assert_label(r"Reason. \boxed{SAME\_TYPE}", "SAME_TYPE")
        self.assert_label(r"Reason. \boxed{\text{SAME_TYPE}}", "SAME_TYPE")
        self.assert_label(r"Reason. \boxed{\text{SAME\_TYPE}}", "SAME_TYPE")
        self.assert_label(r"Reason. \boxed{\text{DIFFERENT}}", "DIFFERENT")

    def test_repeated_same_label_is_accepted(self):
        self.assert_label(
            r"First \boxed{SAME_TYPE}; confirmed \boxed{\text{SAME\_TYPE}}.",
            "SAME_TYPE",
        )

    def test_conflicting_labels_are_format_error(self):
        parsed = parse_response_v3(r"\boxed{SAME_TYPE} then \boxed{DIFFERENT}")
        self.assertEqual(parsed["predicted_label"], "FORMAT_ERROR")
        self.assertEqual(parsed["format_error_reason"], "conflicting_boxed_labels")

    def test_missing_label_never_guesses_from_plain_text(self):
        parsed = parse_response_v3("The answer is SAME_TYPE, but no box was written.")
        self.assertEqual(parsed["predicted_label"], "FORMAT_ERROR")
        self.assertEqual(parsed["format_error_reason"], "missing_boxed_label")


class SamplingAndRuntimeTests(unittest.TestCase):
    def test_vllm_stop_strings_are_complete_and_retained(self):
        options = sampling_options(256, 42)
        self.assertEqual(options["stop"], list(STOP_STRINGS))
        self.assertEqual(options["stop"], [r"\boxed{SAME_TYPE}", r"\boxed{DIFFERENT}"])
        self.assertTrue(options["include_stop_str_in_output"])
        self.assertEqual(options["temperature"], 0.6)
        self.assertEqual(options["top_p"], 0.95)
        self.assertEqual(options["top_k"], 20)
        self.assertEqual(options["presence_penalty"], 1.5)
        self.assertEqual(options["seed"], 42)

    def test_runtime_manifest_fields_and_token_statistics(self):
        runtime = runtime_metrics(2.0, 4.0, 7.0, 2, [10, 20, 30, 40], [1, 2, 3, 4])
        self.assertEqual(runtime["timing_seconds"], {
            "model_load_init": 2.0, "generation_wall": 4.0, "total_wall": 7.0,
        })
        self.assertEqual(runtime["counts"], {"pairs": 2, "prompts": 4, "conditions": 4})
        for field in ("total", "mean", "p50", "p95", "max"):
            self.assertIn(field, runtime["tokens"]["prompt"])
            self.assertIn(field, runtime["tokens"]["generated"])
        self.assertEqual(runtime["tokens"]["prompt"]["total"], 100)
        self.assertEqual(runtime["tokens"]["generated"]["total"], 10)
        self.assertEqual(runtime["throughput"]["conditions_per_second"], 1.0)
        self.assertEqual(runtime["throughput"]["pairs_per_second"], 0.5)
        self.assertEqual(runtime["throughput"]["output_tokens_per_second"], 2.5)

    def test_local_generation_config_and_snapshot_revision_are_recorded(self):
        with tempfile.TemporaryDirectory() as directory:
            snapshot = Path(directory) / "snapshots" / "abc123"
            snapshot.mkdir(parents=True)
            config = {"do_sample": False, "max_new_tokens": 2048}
            (snapshot / "generation_config.json").write_text(
                json.dumps(config), encoding="utf-8"
            )
            payload, config_path, model_path, revision = load_generation_config(
                str(snapshot), None, True
            )
        self.assertEqual(payload, config)
        self.assertTrue(config_path.endswith("generation_config.json"))
        self.assertTrue(model_path.endswith("snapshots/abc123"))
        self.assertEqual(revision, "abc123")


def fixture():
    blind = [
        {"pair_id": "P001", "q1": "a", "q2": "b"},
        {"pair_id": "P002", "q1": "c", "q2": "d"},
    ]
    gold = [
        {"pair_id": "P001", "gold": "SAME_TYPE", "stratum": "same_instance", "risk": "false_negative"},
        {"pair_id": "P002", "gold": "DIFFERENT", "stratum": "same_domain_different_method", "risk": "false_positive"},
    ]
    predictions = []
    for row in gold:
        for order in ("q1_q2", "q2_q1"):
            response = rf"reason \boxed{{{row['gold']}}}."
            predictions.append({
                "pair_id": row["pair_id"], "question_order": order,
                **parse_response_v3(response), "raw_response": response,
                "finish_reason": "stop", "stop_reason": rf"\boxed{{{row['gold']}}}",
                "prompt_token_count": 100, "output_token_count": 10,
            })
    return blind, gold, predictions


class ScorerV3Tests(unittest.TestCase):
    def test_end_to_end_and_parseable_only_are_both_reported(self):
        blind, gold, predictions = fixture()
        response = "No boxed label."
        predictions[1].update({**parse_response_v3(response), "raw_response": response})
        joined = validate_and_join(blind, gold, predictions, 2)
        metrics, errors, disagreements = analyze(joined, ["P001", "P002"])
        order = metrics["conditions"]["q2_q1"]
        self.assertEqual(order["accuracy_end_to_end"], 0.5)
        self.assertEqual(order["parseable_count"], 1)
        self.assertEqual(order["accuracy_parseable_only"], 1.0)
        self.assertEqual(order["format_errors"], 1)
        self.assertEqual(len(errors), 1)
        self.assertEqual(len(disagreements), 1)


if __name__ == "__main__":
    unittest.main()
