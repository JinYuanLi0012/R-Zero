from __future__ import annotations

import sys
import unittest
from pathlib import Path

METHOD_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(METHOD_DIR))

from reward_math import (
    aggregate_center_payload,
    aggregate_population_payload,
    difficulty_from_expert_rates,
    majority_rate,
    split_records,
)


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

    def test_center_records_are_disjointly_sharded(self):
        records = [{"question_index": index} for index in range(7)]
        shards = split_records(records, 3)
        self.assertEqual([len(shard) for shard in shards], [3, 2, 2])
        self.assertEqual(
            [item["question_index"] for shard in shards for item in shard], list(range(7))
        )

    def test_center_feedback_requires_exactly_one_result_per_question(self):
        payloads = [
            [{"question_index": 0, "num_samples": 10, "majority_rate": 0.6}],
            [{"question_index": 1, "num_samples": 10, "majority_rate": 0.4}],
        ]
        self.assertEqual(
            aggregate_center_payload(
                payloads, valid_indices={0, 1}, expected_samples=10
            ),
            {0: 0.6, 1: 0.4},
        )

    def test_center_feedback_rejects_duplicate_or_missing_results(self):
        duplicate = [[
            {"question_index": 0, "num_samples": 10, "majority_rate": 0.5},
            {"question_index": 0, "num_samples": 10, "majority_rate": 0.5},
        ]]
        with self.assertRaises(RuntimeError):
            aggregate_center_payload(duplicate, valid_indices={0}, expected_samples=10)
        with self.assertRaises(RuntimeError):
            aggregate_center_payload([], valid_indices={0}, expected_samples=10)

    def test_single_center_rate_uses_original_rzero_difficulty(self):
        mean_rate, difficulty = difficulty_from_expert_rates([0.6])
        self.assertAlmostEqual(mean_rate, 0.6)
        self.assertAlmostEqual(difficulty, 0.4)


if __name__ == "__main__":
    unittest.main()
