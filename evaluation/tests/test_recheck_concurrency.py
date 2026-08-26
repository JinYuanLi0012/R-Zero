import os
import threading
import time
import unittest
from unittest.mock import patch

from evaluation.recheck_common import recheck_concurrency, recheck_rows


class RecheckConcurrencyTest(unittest.TestCase):
    def test_parallel_recheck_updates_original_rows_and_contains_failures(self):
        rows = [
            {"score": 1, "answer": "local", "response": "local-correct"},
            {"score": 0, "answer": "a", "response": "rescue"},
            {"score": 0, "answer": "b", "response": "reject"},
            {"score": 0, "answer": "c", "response": "failure"},
        ]
        lock = threading.Lock()
        barrier = threading.Barrier(3)
        active = 0
        max_active = 0
        calls = []

        def judge(answer, response):
            nonlocal active, max_active
            with lock:
                calls.append((answer, response))
                active += 1
                max_active = max(max_active, active)
            barrier.wait(timeout=2)
            time.sleep({"rescue": 0.03, "reject": 0.01, "failure": 0.02}[response])
            with lock:
                active -= 1
            if response == "failure":
                raise RuntimeError("mock API failure")
            return "Yes" if response == "rescue" else "No"

        recheck_rows(rows, judge, 3, "test", show_progress=False)

        self.assertGreater(max_active, 1)
        self.assertCountEqual(
            calls,
            [("a", "rescue"), ("b", "reject"), ("c", "failure")],
        )
        self.assertEqual(rows[0]["score"], 1)
        self.assertEqual(rows[1]["score"], 1)
        self.assertEqual(rows[2]["score"], 0)
        self.assertEqual(rows[3]["score"], 0)

    def test_concurrency_must_be_a_positive_integer(self):
        for value in ("0", "-1", "not-an-int"):
            with self.subTest(value=value), patch.dict(
                os.environ, {"RECHECK_CONCURRENCY": value}
            ):
                with self.assertRaisesRegex(ValueError, "positive integer"):
                    recheck_concurrency()

    def test_default_concurrency_is_32(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(recheck_concurrency(), 32)


if __name__ == "__main__":
    unittest.main()
