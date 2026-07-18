from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

METHOD_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(METHOD_DIR))

from pipeline_state import complete_stage, init_state, stage_complete


class PipelineStateTests(unittest.TestCase):
    def test_resume_requires_identical_fingerprint_and_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = root / "state.json"
            marker = root / "round_1" / "_SUCCESS.json"
            artifact = root / "model"
            artifact.mkdir()
            signature = init_state(state, {"K": "10", "sigma": "0.001", "B": "4000"})
            complete_stage(state, marker, "round_1", signature, [artifact], {})
            self.assertTrue(stage_complete(marker, signature, [artifact]))
            artifact.rmdir()
            self.assertFalse(stage_complete(marker, signature, [artifact]))

    def test_changed_population_config_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory) / "state.json"
            init_state(state, {"K": "10"})
            with self.assertRaises(RuntimeError):
                init_state(state, {"K": "11"})


if __name__ == "__main__":
    unittest.main()
