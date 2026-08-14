from __future__ import annotations

import sys
import tempfile
import unittest
import importlib.util
from pathlib import Path

METHOD_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(METHOD_DIR))

from prepare import locate_arrow, stratified_sample

ARROW_AVAILABLE = all(importlib.util.find_spec(name) for name in ("datasets", "pyarrow"))
if ARROW_AVAILABLE:
    import pyarrow as pa
    from prepare import load_round


class PrepareTests(unittest.TestCase):
    def test_locate_exact_train_arrow_ignores_cache_arrow(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            nested = root / "a" / "b"
            nested.mkdir(parents=True)
            expected = nested / "dataset_solver_v1-train.arrow"
            expected.touch()
            (nested / "cache-deadbeef.arrow").touch()
            self.assertEqual(locate_arrow(root, "dataset_solver_v1"), expected)

    def test_stratified_sample_is_exact_and_reproducible(self):
        rows = [
            {"question_id": f"v1:{index}:hash", "original_difficulty": (index % 9) / 20}
            for index in range(900)
        ]
        first = stratified_sample(rows, 1, 42)
        second = stratified_sample(rows, 1, 42)
        self.assertEqual(first, second)
        self.assertEqual(len(first), 200)
        counts = {name: sum(row["stratum"] == name for row in first) for name in ("high", "mid", "low")}
        self.assertEqual(counts, {"high": 80, "mid": 60, "low": 60})

    @unittest.skipUnless(ARROW_AVAILABLE, "server Arrow dependencies are not installed")
    def test_arrow_row_count_and_schema_are_strict(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.arrow"
            table = pa.Table.from_pylist([{"problem": "1+1?", "answer": "2", "score": 7 / 9}])
            with path.open("wb") as handle:
                with pa.ipc.new_stream(handle, table.schema) as writer:
                    writer.write_table(table)
            rows = load_round(path, 1, 1, "center")
            self.assertEqual(len(rows), 1)
            with self.assertRaises(RuntimeError):
                load_round(path, 1, 2, "center")


if __name__ == "__main__":
    unittest.main()
