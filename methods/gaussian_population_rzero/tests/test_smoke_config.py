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

    @staticmethod
    def load_formal_variables(variables: list[str]) -> list[str]:
        command = (
            f"source {shlex.quote(str(METHOD_DIR / 'config.sh'))}; "
            + "printf '%s\\n' "
            + " ".join(f'"${{{name}}}"' for name in variables)
        )
        return subprocess.run(
            ["bash", "-c", command], check=True, capture_output=True, text=True
        ).stdout.splitlines()

    def test_formal_run_choices_are_committed_in_config(self):
        variables = [
            "QUESTIONER_POPULATION_SIZE",
            "SOLVER_POPULATION_SIZE",
            "QUESTIONER_NOISE_SIGMA",
            "SOLVER_NOISE_SIGMA",
            "VLLM_SERVER_BATCH_SIZE",
            "EVALUATE_EACH_ROUND",
            "EVAL_MATH_ONLY",
            "STORAGE_PATH",
        ]
        self.assertEqual(
            self.load_formal_variables(variables),
            [
                "16",
                "6",
                "0.001",
                "0.001",
                "32",
                "true",
                "1",
                "/engrfs/project/jiaxinh/jinyuan/R-zero-storage",
            ],
        )

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
            ["0,1", "2,3", "0,1,2,3", "2", "512", "5", "128", "2048"],
        )

    def test_smoke_only_shortens_population_and_training_trajectory(self):
        variables = [
            "NUM_ROUNDS",
            "QUESTIONER_POPULATION_SIZE",
            "SOLVER_POPULATION_SIZE",
            "QUESTIONER_MAX_STEPS",
            "QUESTIONER_MERGE_STEP",
            "QUESTIONER_SAVE_FREQ",
            "SOLVER_MAX_STEPS",
            "SOLVER_MERGE_STEP",
            "SOLVER_SAVE_FREQ",
        ]
        self.assertEqual(self.load_variables(variables), ["1", "4", "4"] + ["1"] * 6)

    def test_smoke_preserves_formal_algorithm_settings(self):
        variables = [
            "SOLVER_EXPERT_SAMPLES",
            "SOLVER_LABEL_SAMPLES",
            "QUESTIONER_ROLLOUT_BATCH_SIZE",
            "QUESTIONER_ROLLOUT_N",
            "QUESTIONER_GLOBAL_BATCH_SIZE",
            "SOLVER_ROLLOUT_BATCH_SIZE",
            "SOLVER_ROLLOUT_N",
            "SOLVER_GLOBAL_BATCH_SIZE",
            "DATASET_MIN_SCORE",
            "DATASET_MAX_SCORE",
            "QUESTIONER_NOISE_SIGMA",
            "SOLVER_NOISE_SIGMA",
            "POPULATION_SEED",
        ]
        self.assertEqual(
            self.load_variables(variables),
            ["10", "9", "512", "4", "4", "512", "5", "128", "0.3", "0.8", "0.001", "0.001", "42"],
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

    def test_validation_rejects_zero_vllm_batch_size(self):
        completed = self.validate_with("VLLM_SERVER_BATCH_SIZE=0")
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("VLLM_SERVER_BATCH_SIZE must be >= 1", completed.stderr)


if __name__ == "__main__":
    unittest.main()
