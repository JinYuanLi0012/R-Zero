from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "pipeline_state.py"


class PipelineStateTest(unittest.TestCase):
    def test_complete_and_resume_check(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = root / "run_state.json"
            marker = root / "round_1" / "_SUCCESS.json"
            artifact = root / "artifact"
            artifact.mkdir()
            signature = subprocess.check_output(
                [sys.executable, SCRIPT, "init", "--state", state, "--field", "base=x"],
                text=True,
            ).strip()
            subprocess.check_call(
                [
                    sys.executable,
                    SCRIPT,
                    "complete",
                    "--state",
                    state,
                    "--marker",
                    marker,
                    "--stage",
                    "round_1/test",
                    "--fingerprint",
                    signature,
                    "--artifact",
                    artifact,
                    "--meta",
                    "model=x",
                ]
            )
            self.assertEqual(
                subprocess.call(
                    [
                        sys.executable,
                        SCRIPT,
                        "check",
                        "--marker",
                        marker,
                        "--fingerprint",
                        signature,
                        "--require",
                        artifact,
                    ]
                ),
                0,
            )
            payload = json.loads(state.read_text())
            self.assertEqual(payload["stages"]["round_1/test"]["metadata"]["model"], "x")

    def test_changed_config_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state = Path(temporary) / "run_state.json"
            subprocess.check_call(
                [sys.executable, SCRIPT, "init", "--state", state, "--field", "base=x"]
            )
            result = subprocess.run(
                [sys.executable, SCRIPT, "init", "--state", state, "--field", "base=y"],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("different RUN_NAME", result.stderr)


if __name__ == "__main__":
    unittest.main()
