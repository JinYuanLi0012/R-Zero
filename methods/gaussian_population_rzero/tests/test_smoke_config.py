from __future__ import annotations

import os
import shlex
import subprocess
import unittest
from pathlib import Path

METHOD_DIR = Path(__file__).resolve().parents[1]


class SmokeConfigTests(unittest.TestCase):
    @staticmethod
    def load_variables(variables: list[str]) -> list[str]:
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
        return completed.stdout.splitlines()

    @staticmethod
    def validate_with(overrides: str) -> subprocess.CompletedProcess[str]:
        command = (
            f"set -a; source {shlex.quote(str(METHOD_DIR / 'tests/smoke_config.sh'))}; "
            f"{overrides}; python3 {shlex.quote(str(METHOD_DIR / 'validate_config.py'))}"
        )
        return subprocess.run(["bash", "-c", command], capture_output=True, text=True)

    def test_smoke_uses_standard_4096_token_lengths(self):
        variables = [
            "QUESTIONER_MAX_RESPONSE_LENGTH",
            "QUESTION_GENERATION_MAX_TOKENS",
            "SOLVER_EXPERT_MAX_TOKENS",
            "SOLVER_LABEL_MAX_TOKENS",
            "SOLVER_MAX_RESPONSE_LENGTH",
        ]
        self.assertEqual(self.load_variables(variables), ["4096"] * len(variables))

    def test_smoke_preserves_standard_stage_gpu_layout(self):
        variables = [
            "QUESTIONER_TRAIN_GPU_IDS",
            "SOLVER_EXPERT_GPU_IDS",
            "QUESTION_GENERATION_GPU_IDS",
            "CENTER_ROLLOUT_TENSOR_PARALLEL_SIZE",
            "SOLVER_ROLLOUT_BATCH_SIZE",
            "SOLVER_ROLLOUT_N",
            "SOLVER_GLOBAL_BATCH_SIZE",
            "QUESTION_TOTAL_BUDGET",
        ]
        self.assertEqual(
            self.load_variables(variables),
            ["0,1", "2,3", "0,1,2,3", "2", "4", "5", "4", "32"],
        )

    def test_validation_rejects_a_rollout_batch_smaller_than_four_gpu_world(self):
        completed = self.validate_with(
            "SOLVER_ROLLOUT_BATCH_SIZE=1; SOLVER_GLOBAL_BATCH_SIZE=1"
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("must be divisible by its GPU count", completed.stderr)

    def test_validation_rejects_an_undersized_effective_grpo_batch(self):
        completed = self.validate_with("SOLVER_GLOBAL_BATCH_SIZE=1; SOLVER_ROLLOUT_N=2")
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("effective Solver GRPO batch", completed.stderr)


if __name__ == "__main__":
    unittest.main()
