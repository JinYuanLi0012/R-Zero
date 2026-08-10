import json
import tempfile
import unittest
from pathlib import Path

from qwen35.rzero.solver_service import publish_service_receipt


class SolverServiceTests(unittest.TestCase):
    def test_service_receipt_is_atomically_published(self):
        with tempfile.TemporaryDirectory() as temporary:
            receipt = Path(temporary) / "service.json"
            publish_service_receipt(receipt, "127.0.0.1", 43123)
            self.assertEqual(
                json.loads(receipt.read_text(encoding="utf-8")),
                {"host": "127.0.0.1", "port": 43123},
            )
            self.assertEqual(list(receipt.parent.glob("*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
