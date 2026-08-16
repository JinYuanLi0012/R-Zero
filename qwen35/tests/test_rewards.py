import unittest
from unittest.mock import patch

from qwen35.rzero.rewards.challenger import score_from_solver_results
from qwen35.rzero.rewards.common import answers_equivalent, extract_boxed, majority_vote, parse_questioner_response


class RewardParityTests(unittest.TestCase):
    def test_balanced_box_extraction(self):
        self.assertEqual(extract_boxed(r"work \\boxed{\\frac{1}{2}}"), [r"\\frac{1}{2}"])

    def test_questioner_uses_last_blocks(self):
        parsed = parse_questioner_response(
            r"<question>draft</question> \\boxed{0} <question>final</question> \\boxed{42}"
        )
        self.assertEqual(parsed, {"question": "final", "answer": "42"})

    def test_majority_vote_is_bidirectional(self):
        def grader(left, right):
            return (left, right) == ("0.5", "1/2")

        with patch(
            "qwen35.rzero.rewards.common._grade_answer_with_timeout",
            side_effect=lambda function, left, right, timeout: function(left, right),
        ) as timed_grade:
            answer, count, valid = majority_vote(["1/2", "0.5", "3"], grader)
        self.assertEqual((answer, count, len(valid)), ("1/2", 2, 3))
        self.assertTrue(all(call.args[3] == 10.0 for call in timed_grade.call_args_list))

    def test_grader_timeout_is_a_non_match_in_each_direction(self):
        grader = unittest.mock.Mock()
        with patch(
            "qwen35.rzero.rewards.common._grade_answer_with_timeout", return_value=False
        ) as timed_grade:
            self.assertFalse(answers_equivalent("left", "right", grader))

        self.assertEqual(
            [call.args for call in timed_grade.call_args_list],
            [(grader, "left", "right", 10.0), (grader, "right", "left", 10.0)],
        )

    def test_released_challenger_formula(self):
        parsed = [{"question": "q1", "answer": "a1"}, {"question": "q2", "answer": "a2"}]
        solver = [
            {"question": "q1", "answer": "a1", "score": 0.3},
            {"question": "q2", "answer": "a2", "score": 0.8},
        ]
        scores = score_from_solver_results(parsed, solver, cluster_fn=lambda problems, threshold: [0.25, 0.5])
        self.assertAlmostEqual(scores[0]["score"], min(0.3, 0.7) - 0.25)
        self.assertAlmostEqual(scores[1]["score"], min(0.8, 0.2) - 0.5)


if __name__ == "__main__":
    unittest.main()
