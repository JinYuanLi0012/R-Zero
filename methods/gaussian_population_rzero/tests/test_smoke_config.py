from __future__ import annotations

import os
import shlex
import subprocess
import unittest
from pathlib import Path

METHOD_DIR = Path(__file__).resolve().parents[1]


class SmokeConfigTests(unittest.TestCase):
    def test_smoke_uses_standard_4096_token_lengths(self):
        variables = [
            "QUESTIONER_MAX_RESPONSE_LENGTH",
            "QUESTION_GENERATION_MAX_TOKENS",
            "SOLVER_EXPERT_MAX_TOKENS",
            "SOLVER_LABEL_MAX_TOKENS",
            "SOLVER_MAX_RESPONSE_LENGTH",
        ]
        environment = os.environ.copy()
        for name in variables:
            environment.pop(name, None)
        command = (
            f"source {shlex.quote(str(METHOD_DIR / 'tests/smoke_config.sh'))}; "
            + "printf '%s\\n' "
            + " ".join(f'"${{{name}}}"' for name in variables)
        )
        completed = subprocess.run(
            ["bash", "-c", command],
            check=True,
            capture_output=True,
            text=True,
            env=environment,
        )
        self.assertEqual(completed.stdout.splitlines(), ["4096"] * len(variables))


if __name__ == "__main__":
    unittest.main()
