from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


METHOD = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(METHOD))

from run_pair_judge import (  # noqa: E402
    CandidateTask, MAPPINGS, ORDERS, build_prompt, decode_semantic_label,
    looks_nonbase, make_conditions, read_blind, score_tasks,
    validate_tokenization_boundary,
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

    def test_tokenization_boundary_must_be_compositional(self):
        class Tokenizer:
            def __init__(self, joint_ids):
                self.joint_ids = joint_ids

            def encode(self, text, add_special_tokens):
                self.asserted_arguments = (text, add_special_tokens)
                return self.joint_ids

        validate_tokenization_boundary(Tokenizer([1, 2, 3]), "prompt", [1, 2], "A", [3])
        with self.assertRaisesRegex(RuntimeError, "boundary is not compositional"):
            validate_tokenization_boundary(
                Tokenizer([1, 9]), "prompt", [1, 2], "A", [3],
            )

    def test_answer_options_decode_under_both_mappings(self):
        self.assertEqual(decode_semantic_label("A_same", "A"), "SAME_TYPE")
        self.assertEqual(decode_semantic_label("A_same", "B"), "DIFFERENT")
        self.assertEqual(decode_semantic_label("A_different", "A"), "DIFFERENT")
        self.assertEqual(decode_semantic_label("A_different", "B"), "SAME_TYPE")


class FakeMatrix:
    def __init__(self, rows):
        self.rows = rows

    def __setitem__(self, key, value):
        row, column_slice = key
        if isinstance(value, list):
            values = value
        elif hasattr(value, "values"):
            values = value.values
        else:
            start, stop, step = column_slice.indices(len(self.rows[row]))
            values = [value] * len(range(start, stop, step))
        self.rows[row][column_slice] = values


class FakeVector:
    def __init__(self, values):
        self.values = values

    def float(self):
        return self

    def __getitem__(self, index):
        return FakeScalar(self.values[index])


class FakeScalar:
    def __init__(self, value):
        self.value = value

    def item(self):
        return self.value


class FakeLogits:
    def __init__(self, values):
        self.values = values

    def __getitem__(self, key):
        batch, position, vocabulary = key
        assert vocabulary == slice(None)
        return FakeVector(self.values[batch][position])


class FakeTorch:
    long = "long"

    @staticmethod
    def full(shape, fill_value, dtype, device):
        return FakeMatrix([[fill_value] * shape[1] for _ in range(shape[0])])

    @staticmethod
    def zeros(shape, dtype, device):
        return FakeMatrix([[0] * shape[1] for _ in range(shape[0])])

    @staticmethod
    def tensor(values, device):
        return list(values)

    @staticmethod
    def log_softmax(vector, dim):
        import math
        maximum = max(vector.values)
        normalizer = maximum + math.log(sum(math.exp(x - maximum) for x in vector.values))
        return FakeVector([value - normalizer for value in vector.values])


class ScoreTaskTests(unittest.TestCase):
    def test_fixed_logits_use_causal_positions_and_ignore_right_padding(self):
        class Model:
            def __call__(self, input_ids, attention_mask, use_cache):
                self.input_rows = input_ids.rows
                self.mask_rows = attention_mask.rows
                logits = [[[-10.0] * 10 for _ in range(5)] for _ in range(2)]
                logits[0][1][3] = 3.0
                logits[0][3][9] = 50.0  # padded position must never be read
                logits[1][2][7] = 4.0
                logits[1][3][8] = 5.0
                return type("Output", (), {"logits": FakeLogits(logits)})()

        model = Model()
        tasks = [
            CandidateTask(0, "A", [1, 2], [3]),
            CandidateTask(1, "B", [4, 5, 6], [7, 8]),
        ]
        scores = score_tasks(model, FakeTorch, tasks, 0, "cpu", 2)
        self.assertEqual(model.input_rows, [[1, 2, 3, 0, 0], [4, 5, 6, 7, 8]])
        self.assertEqual(model.mask_rows, [[1, 1, 1, 0, 0], [1, 1, 1, 1, 1]])
        self.assertGreater(scores[(0, "A")]["sum"], -0.001)
        self.assertEqual(len(scores[(1, "B")]["token_logprobs"]), 2)
        self.assertGreater(scores[(1, "B")]["sum"], -0.001)


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

    def test_fourth_quadrant_flip_cannot_pass_gate(self):
        blind, gold, predictions = fixture_rows()
        for row in predictions:
            if row["question_order"] == "q2_q1" and row["mapping"] == "A_different":
                row["predicted_label"] = (
                    "DIFFERENT" if row["predicted_label"] == "SAME_TYPE" else "SAME_TYPE"
                )
        joined = validate_and_join(blind, gold, predictions, 4)
        metrics, _, _ = analyze(joined, [row["pair_id"] for row in blind])
        self.assertEqual(metrics["primary"]["accuracy"], 1.0)
        self.assertEqual(
            metrics["stability"]["question_order"]["A_different"]["disagreements"], 4,
        )
        self.assertEqual(
            metrics["stability"]["answer_mapping"]["q2_q1"]["disagreements"], 4,
        )
        self.assertFalse(metrics["predeclared_gate"]["passed"])
        self.assertEqual(metrics["predeclared_gate"]["conclusion"], "unstable")

    def test_rejects_missing_condition(self):
        blind, gold, predictions = fixture_rows()
        with self.assertRaisesRegex(ValueError, "coverage mismatch"):
            validate_and_join(blind, gold, predictions[:-1], 4)


if __name__ == "__main__":
    unittest.main()
