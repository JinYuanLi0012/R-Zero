from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


METHOD = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(METHOD))

from run_pair_judge import (  # noqa: E402
    MAPPINGS, ORDERS, build_prompt, looks_nonbase, make_conditions, read_blind,
)
from score_pair_judge import analyze, validate_and_join  # noqa: E402


class BlindRunnerTests(unittest.TestCase):
    def test_prompt_contains_questions_but_not_pair_metadata(self):
        prompt = build_prompt("Question alpha", "Question beta", "A_same")
        self.assertIn("Question alpha", prompt)
        self.assertIn("Question beta", prompt)
        self.assertNotIn("P001", prompt)
        self.assertIn("A. SAME_TYPE\nB. DIFFERENT", prompt)
        reversed_mapping = build_prompt("Question alpha", "Question beta", "A_different")
        self.assertIn("A. DIFFERENT\nB. SAME_TYPE", reversed_mapping)

    def test_conditions_have_fixed_four_way_coverage(self):
        conditions = make_conditions([{"pair_id": "P001", "q1": "one", "q2": "two"}])
        self.assertEqual(len(conditions), 4)
        self.assertEqual(
            [(row.question_order, row.mapping) for row in conditions],
            [(order, mapping) for order in ORDERS for mapping in MAPPINGS],
        )
        self.assertEqual(conditions[0].pair_id, "P001")
        self.assertNotIn("P001", conditions[0].prompt)

    def test_blind_reader_rejects_gold(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "not_blind.jsonl"
            path.write_text(
                json.dumps({"pair_id": "P001", "q1": "x", "q2": "y", "gold": "DIFFERENT"})
                + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "forbidden gold"):
                read_blind(path, 1)

    def test_nonbase_path_guard(self):
        self.assertTrue(looks_nonbase("/models/global_step_15/actor/huggingface"))
        self.assertTrue(looks_nonbase("Qwen/Qwen3-4B-Instruct"))
        self.assertFalse(looks_nonbase("Qwen/Qwen3-4B-Base"))


def fixture_rows():
    blind = [
        {"pair_id": "P001", "q1": "q1a", "q2": "q1b"},
        {"pair_id": "P002", "q1": "q2a", "q2": "q2b"},
        {"pair_id": "P003", "q1": "q3a", "q2": "q3b"},
        {"pair_id": "P004", "q1": "q4a", "q2": "q4b"},
    ]
    gold = [
        {"pair_id": "P001", "gold": "SAME_TYPE", "stratum": "same_instance", "risk": "false_negative"},
        {"pair_id": "P002", "gold": "SAME_TYPE", "stratum": "same_template", "risk": "false_negative"},
        {"pair_id": "P003", "gold": "DIFFERENT", "stratum": "same_domain_different_method", "risk": "false_positive"},
        {"pair_id": "P004", "gold": "DIFFERENT", "stratum": "shared_prime_surface", "risk": "false_positive"},
    ]
    predictions = []
    gold_by_id = {row["pair_id"]: row["gold"] for row in gold}
    for row in blind:
        for order in ORDERS:
            for mapping in MAPPINGS:
                label = gold_by_id[row["pair_id"]]
                predictions.append({
                    "pair_id": row["pair_id"], "question_order": order,
                    "mapping": mapping, "predicted_label": label,
                    "score_a": -0.1, "score_b": -1.0,
                })
    return blind, gold, predictions


class ScorerTests(unittest.TestCase):
    def test_perfect_fixture_passes_and_has_all_strata(self):
        blind, gold, predictions = fixture_rows()
        joined = validate_and_join(blind, gold, predictions, 4)
        metrics, errors, disagreements = analyze(joined, [row["pair_id"] for row in blind])
        self.assertEqual(metrics["primary"]["accuracy"], 1.0)
        self.assertEqual(metrics["primary"]["false_negatives"], 0)
        self.assertEqual(metrics["primary"]["false_positives"], 0)
        self.assertTrue(metrics["predeclared_gate"]["passed"])
        self.assertEqual(errors, [])
        self.assertEqual(disagreements, [])
        self.assertEqual(
            set(metrics["conditions"]["q1_q2__A_same"]["strata"]),
            {row["stratum"] for row in gold},
        )

    def test_detects_order_and_mapping_instability(self):
        blind, gold, predictions = fixture_rows()
        for row in predictions:
            if row["pair_id"] == "P001" and row["question_order"] == "q2_q1":
                row["predicted_label"] = "DIFFERENT"
            if row["pair_id"] == "P003" and row["mapping"] == "A_different":
                row["predicted_label"] = "SAME_TYPE"
        joined = validate_and_join(blind, gold, predictions, 4)
        metrics, errors, disagreements = analyze(joined, [row["pair_id"] for row in blind])
        self.assertEqual(
            metrics["stability"]["question_order"]["A_same"]["disagreements"], 1,
        )
        self.assertEqual(
            metrics["stability"]["answer_mapping"]["q1_q2"]["disagreements"], 1,
        )
        self.assertGreaterEqual(len(errors), 2)
        self.assertGreaterEqual(len(disagreements), 2)

    def test_rejects_missing_condition(self):
        blind, gold, predictions = fixture_rows()
        with self.assertRaisesRegex(ValueError, "coverage mismatch"):
            validate_and_join(blind, gold, predictions[:-1], 4)


if __name__ == "__main__":
    unittest.main()
