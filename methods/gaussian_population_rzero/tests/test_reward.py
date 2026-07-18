from __future__ import annotations

import sys
import unittest
from pathlib import Path

METHOD_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(METHOD_DIR))

from reward_math import aggregate_population_payload, difficulty_from_expert_rates, majority_rate


class RewardTests(unittest.TestCase):
    @staticmethod
    def equal(left: str, right: str) -> bool:
        return left == right

    def test_invalid_answers_remain_in_fixed_denominator(self):
        answers = ["A"] * 6 + ["B"] + [""] * 3
        self.assertEqual(majority_rate(answers, 10, self.equal), 0.6)

    def test_confident_disagreeing_experts_still_have_low_difficulty(self):
        # The experts can favor different answers; only their within-expert rates matter.
        mean_rate, difficulty = difficulty_from_expert_rates([0.9, 0.9])
        self.assertAlmostEqual(mean_rate, 0.9)
        self.assertAlmostEqual(difficulty, 0.1)

    def test_mean_is_computed_before_distance_from_half(self):
        mean_rate, difficulty = difficulty_from_expert_rates([0.4, 0.8])
        self.assertAlmostEqual(mean_rate, 0.6)
        self.assertAlmostEqual(difficulty, 0.4)

    def test_population_must_be_complete(self):
        payload = [[{"question_index": 0, "expert_scores": [
            {"expert_index": 0, "num_samples": 10, "majority_rate": 0.8}
        ]}]]
        with self.assertRaises(RuntimeError):
            aggregate_population_payload(
                payload, valid_indices={0}, population_size=2, expected_samples=10
            )

    def test_each_expert_must_return_exact_rollout_count(self):
        payload = [[{"question_index": 0, "expert_scores": [
            {"expert_index": 0, "num_samples": 9, "majority_rate": 0.8}
        ]}]]
        with self.assertRaises(RuntimeError):
            aggregate_population_payload(
                payload, valid_indices={0}, population_size=1, expected_samples=10
            )

    def test_no_cross_expert_answer_field_exists(self):
        payloads = [
            [{"question_index": 0, "expert_scores": [
                {"expert_index": 0, "num_samples": 10, "majority_rate": 0.9}
            ]}],
            [{"question_index": 0, "expert_scores": [
                {"expert_index": 1, "num_samples": 10, "majority_rate": 0.8}
            ]}],
        ]
        rates = aggregate_population_payload(
            payloads, valid_indices={0}, population_size=2, expected_samples=10
        )
        self.assertEqual(rates[0], [0.9, 0.8])


if __name__ == "__main__":
    unittest.main()
