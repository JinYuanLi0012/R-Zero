from __future__ import annotations

import sys
import unittest
from pathlib import Path


METHOD = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(METHOD))

from run_pair_judge_v2 import (  # noqa: E402
    PROMPT_TEMPLATE, build_prompt, generate_responses, make_conditions, parse_response,
)
from score_pair_judge_v2 import analyze, validate_and_join  # noqa: E402


class PromptAndParserTests(unittest.TestCase):
    def test_prompt_is_exact_and_only_substitutes_questions(self):
        prompt = build_prompt("alpha", "beta")
        self.assertEqual(prompt, PROMPT_TEMPLATE.replace("{question_a}", "alpha").replace(
            "{question_b}", "beta"
        ))
        self.assertIn("If the match is not clear, choose DIFFERENT.", prompt)
        self.assertIn(r"exactly \boxed{SAME_TYPE} or \boxed{DIFFERENT}.", prompt)
        self.assertTrue(prompt.endswith("Analysis: "))
        self.assertNotIn("P001", prompt)

    def test_two_orders_and_no_mapping_condition(self):
        conditions = make_conditions([{"pair_id": "P001", "q1": "one", "q2": "two"}])
        self.assertEqual(len(conditions), 2)
        self.assertEqual([row.question_order for row in conditions], ["q1_q2", "q2_q1"])
        self.assertIn("Question A:\none\n", conditions[0].prompt)
        self.assertIn("Question A:\ntwo\n", conditions[1].prompt)
        self.assertTrue(all(row.pair_id not in row.prompt for row in conditions))

    def test_strict_final_boxed_parser(self):
        valid = parse_response(r"Brief reason. \boxed{SAME_TYPE}")
        self.assertEqual(valid["predicted_label"], "SAME_TYPE")
        self.assertIsNone(valid["format_error_reason"])
        self.assertEqual(
            parse_response("SAME_TYPE because they match.")["format_error_reason"],
            "missing_boxed_label",
        )
        self.assertEqual(
            parse_response(r"\boxed{DIFFERENT}. trailing")["format_error_reason"],
            "boxed_label_not_final",
        )
        self.assertEqual(
            parse_response(r"reason \boxed { SAME_TYPE }")["format_error_reason"],
            "missing_boxed_label",
        )
        self.assertEqual(
            parse_response(r"\boxed{SAME_TYPE} then \boxed{SAME_TYPE}")["format_error_reason"],
            "multiple_boxed_labels",
        )
        self.assertEqual(
            parse_response(r"\boxed{SAME_TYPE} then \boxed{DIFFERENT}")["format_error_reason"],
            "conflicting_boxed_labels",
        )

    def test_generation_is_plain_deterministic_completion(self):
        class Tensor:
            def __init__(self, rows):
                self.rows = rows

            def to(self, device):
                self.device = device
                return self

            @property
            def shape(self):
                return (len(self.rows), len(self.rows[0]))

        class Tokenizer:
            pad_token_id = 0
            eos_token_id = 2

            def __call__(self, prompts, **kwargs):
                self.prompts = prompts
                self.call_kwargs = kwargs
                return {
                    "input_ids": Tensor([[0, 11, 12], [21, 22, 23]]),
                    "attention_mask": Tensor([[0, 1, 1], [1, 1, 1]]),
                }

            def decode(self, token_ids, skip_special_tokens):
                self.decode_calls = getattr(self, "decode_calls", []) + [
                    (list(token_ids), skip_special_tokens)
                ]
                return "response:" + ",".join(map(str, token_ids))

        class Model:
            def generate(self, **kwargs):
                self.kwargs = kwargs
                return [[0, 11, 12, 31, 32], [21, 22, 23, 41]]

        conditions = make_conditions([{"pair_id": "P001", "q1": "one", "q2": "two"}])
        tokenizer = Tokenizer()
        model = Model()
        responses = generate_responses(model, tokenizer, None, conditions, "cuda:0", 2, 256)
        self.assertEqual(responses, ["response:31,32", "response:41"])
        self.assertEqual(tokenizer.call_kwargs, {
            "return_tensors": "pt", "padding": True, "add_special_tokens": True,
        })
        self.assertFalse(model.kwargs["do_sample"])
        self.assertEqual(model.kwargs["num_beams"], 1)
        self.assertEqual(model.kwargs["max_new_tokens"], 256)
        self.assertNotIn("temperature", model.kwargs)
        self.assertEqual(tokenizer.decode_calls, [([31, 32], True), ([41], True)])


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
            predictions.append({
                "pair_id": row["pair_id"], "question_order": order,
                "predicted_label": row["gold"], "parsed_label": row["gold"],
                "format_error_reason": None,
                "raw_response": rf"reason \boxed{{{row['gold']}}}",
            })
    return blind, gold, predictions


class ScorerV2Tests(unittest.TestCase):
    def test_perfect_two_order_fixture(self):
        blind, gold, predictions = fixture()
        joined = validate_and_join(blind, gold, predictions, 2)
        metrics, errors, disagreements = analyze(joined, ["P001", "P002"])
        self.assertEqual(metrics["conditions"]["q1_q2"]["accuracy"], 1.0)
        self.assertEqual(metrics["conditions"]["q2_q1"]["accuracy"], 1.0)
        self.assertEqual(metrics["order_stability"]["disagreements"], 0)
        self.assertEqual(errors, [])
        self.assertEqual(disagreements, [])
        self.assertEqual(
            metrics["evaluation_status"], "diagnostic_rerun_not_held_out_validation"
        )

    def test_format_error_and_order_disagreement_are_reported(self):
        blind, gold, predictions = fixture()
        for row in predictions:
            if row["pair_id"] == "P001" and row["question_order"] == "q2_q1":
                row.update({
                    "predicted_label": "FORMAT_ERROR", "parsed_label": None,
                    "format_error_reason": "missing_boxed_label", "raw_response": "unclear",
                })
        joined = validate_and_join(blind, gold, predictions, 2)
        metrics, errors, disagreements = analyze(joined, ["P001", "P002"])
        self.assertEqual(metrics["conditions"]["q2_q1"]["format_errors"], 1)
        self.assertEqual(metrics["conditions"]["q2_q1"]["format_errors_on_same_type"], 1)
        self.assertEqual(metrics["order_stability"]["disagreements"], 1)
        self.assertEqual(metrics["order_stability"]["pairs_with_any_format_error"], 1)
        self.assertEqual(len(errors), 1)
        self.assertEqual(len(disagreements), 1)

    def test_scorer_reparses_raw_response(self):
        blind, gold, predictions = fixture()
        predictions[0]["predicted_label"] = "DIFFERENT"
        with self.assertRaisesRegex(ValueError, "saved parse disagrees"):
            validate_and_join(blind, gold, predictions, 2)


if __name__ == "__main__":
    unittest.main()
