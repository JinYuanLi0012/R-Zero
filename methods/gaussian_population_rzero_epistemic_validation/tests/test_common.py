from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

METHOD_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(METHOD_DIR))

from common import entropy_from_counts, question_hash


class CommonTests(unittest.TestCase):
    def test_entropy_known_distributions(self):
        self.assertEqual(entropy_from_counts([8]), 0.0)
        self.assertAlmostEqual(entropy_from_counts([4, 4]), math.log(2))
        self.assertAlmostEqual(entropy_from_counts([2, 2, 2, 2]), math.log(4))

    def test_question_hash_is_exact_and_stable(self):
        self.assertEqual(question_hash("x + y"), question_hash("x + y"))
        self.assertNotEqual(question_hash("x + y"), question_hash("x  + y"))


if __name__ == "__main__":
    unittest.main()
