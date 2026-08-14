from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

METHOD_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(METHOD_DIR))

AVAILABLE = all(
    importlib.util.find_spec(name)
    for name in ("numpy", "pandas", "scipy", "sklearn", "matplotlib", "pyarrow")
)
if AVAILABLE:
    import pandas as pd
    from analyze import match_round, paired_statistics


@unittest.skipUnless(AVAILABLE, "server analysis dependencies are not installed")
class AnalysisTests(unittest.TestCase):
    def test_matching_and_bootstrap_are_deterministic(self):
        frame = pd.DataFrame([
            {
                "question_id": f"v2:{index}:hash", "round": 2,
                "u_epi": index / 200, "h_total": 0.5 + (index % 5) * 0.001,
                "original_difficulty": 0.4 + (index % 3) * 0.001,
                "question_length": 100 + index % 7, "valid": index >= 150,
            }
            for index in range(200)
        ])
        pairs, relaxed = match_round(frame)
        self.assertFalse(relaxed)
        self.assertEqual(len(pairs), 50)
        first = paired_statistics(pairs, 1000, 42)
        second = paired_statistics(pairs, 1000, 42)
        self.assertEqual(first, second)
        self.assertEqual(first["difference_pp"], 100.0)


if __name__ == "__main__":
    unittest.main()
