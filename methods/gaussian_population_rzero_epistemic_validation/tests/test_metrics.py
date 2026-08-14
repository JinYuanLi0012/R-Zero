from __future__ import annotations

import importlib.util
import math
import sys
import unittest
from pathlib import Path

METHOD_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(METHOD_DIR))

AVAILABLE = all(importlib.util.find_spec(name) for name in ("pyarrow", "mathruler", "stopit"))
if AVAILABLE:
    import aggregate


@unittest.skipUnless(AVAILABLE, "server experiment dependencies are not installed")
class MetricTests(unittest.TestCase):
    @staticmethod
    def records(answers_by_expert):
        return [
            {"expert_index": expert, "sample_index": sample, "extracted_answer": answer}
            for expert, answers in enumerate(answers_by_expert)
            for sample, answer in enumerate(answers)
        ]

    def test_stable_expert_disagreement_has_high_epistemic_entropy(self):
        rows = self.records([["1"] * 8, ["2"] * 8])
        classes, _ = aggregate.cluster_answers(rows)
        metrics = aggregate.metrics_from_classes(rows, classes, 2)
        self.assertEqual(metrics["h_within"], 0.0)
        self.assertAlmostEqual(metrics["u_epi"], math.log(2))

    def test_identical_internal_randomness_has_zero_epistemic_entropy(self):
        rows = self.records([["1", "2"] * 4, ["1", "2"] * 4])
        classes, _ = aggregate.cluster_answers(rows)
        metrics = aggregate.metrics_from_classes(rows, classes, 2)
        self.assertAlmostEqual(metrics["h_total"], metrics["h_within"])
        self.assertAlmostEqual(metrics["u_epi"], 0.0)

    def test_invalid_and_conditional_valid_policies(self):
        rows = self.records([["", "1"], ["", "2"]])
        classes, _ = aggregate.cluster_answers(rows)
        metrics = aggregate.metrics_from_classes(rows, classes, 2)
        self.assertEqual(metrics["invalid_completion_count"], 2)
        self.assertAlmostEqual(metrics["conditional_valid_h_within"], 0.0)
        self.assertAlmostEqual(metrics["conditional_valid_u_epi"], math.log(2))


if __name__ == "__main__":
    unittest.main()
