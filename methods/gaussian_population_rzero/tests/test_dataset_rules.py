from __future__ import annotations

import sys
import unittest
from pathlib import Path

METHOD_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(METHOD_DIR))

from dataset_rules import is_solver_training_record


class DatasetRuleTests(unittest.TestCase):
    def test_exact_none_matches_standard_rzero_filter(self):
        record = {"question": "valid", "answer": "None", "score": 0.5}
        self.assertFalse(is_solver_training_record(record, min_score=0.3, max_score=0.8))

    def test_filter_does_not_add_broader_none_normalization(self):
        record = {"question": "valid", "answer": r"\text{None}", "score": 0.5}
        self.assertTrue(is_solver_training_record(record, min_score=0.3, max_score=0.8))

    def test_score_question_and_empty_answer_rules(self):
        eligible = {"question": "valid", "answer": "42", "score": 0.5}
        self.assertTrue(is_solver_training_record(eligible, min_score=0.3, max_score=0.8))
        self.assertFalse(
            is_solver_training_record({**eligible, "score": 0.9}, min_score=0.3, max_score=0.8)
        )
        self.assertFalse(
            is_solver_training_record({**eligible, "question": " "}, min_score=0.3, max_score=0.8)
        )
        self.assertFalse(
            is_solver_training_record({**eligible, "answer": " "}, min_score=0.3, max_score=0.8)
        )


if __name__ == "__main__":
    unittest.main()
