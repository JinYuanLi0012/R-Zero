from __future__ import annotations

import unittest
from pathlib import Path


METHOD_DIR = Path(__file__).resolve().parents[1]


class VllmModeTests(unittest.TestCase):
    def test_direct_vllm_entrypoints_force_v0_before_import(self):
        for filename in (
            "solver_population_server.py",
            "solver_center_server.py",
            "generate_questions.py",
            "evaluate_questions.py",
        ):
            source = (METHOD_DIR / filename).read_text(encoding="utf-8")
            self.assertLess(
                source.index('os.environ["VLLM_USE_V1"] = "0"'),
                source.index("import vllm"),
                filename,
            )

    def test_runner_forces_v0(self):
        source = (METHOD_DIR / "run.sh").read_text(encoding="utf-8")
        self.assertIn("export VLLM_USE_V1=0", source)

    def test_solver_population_generation_is_cpu_memory_bounded(self):
        source = (METHOD_DIR / "solver_population_server.py").read_text(encoding="utf-8")
        self.assertIn('parser.add_argument("--batch-size", type=int, default=32)', source)
        self.assertIn("range(0, len(prompts), ARGS.batch_size)", source)
        self.assertIn("prompts[start : start + ARGS.batch_size]", source)

        launcher = (METHOD_DIR / "start_solver_population.sh").read_text(encoding="utf-8")
        self.assertIn('--batch-size "$VLLM_SERVER_BATCH_SIZE"', launcher)

    def test_vllm_server_batch_does_not_expand_to_other_stages(self):
        for filename in (
            "generate_questions.py",
            "generate_questions.sh",
            "evaluate_questions.py",
            "evaluate_questions.sh",
        ):
            source = (METHOD_DIR / filename).read_text(encoding="utf-8")
            self.assertNotIn("VLLM_SERVER_BATCH_SIZE", source, filename)

    def test_central_solver_server_never_imports_or_constructs_a_population(self):
        source = (METHOD_DIR / "solver_center_server.py").read_text(encoding="utf-8")
        self.assertNotIn("GaussianPopulation", source)
        self.assertNotIn("make_expert_specs", source)
        self.assertNotIn("expert_seed", source)
        self.assertIn('"feedback_mode": "central"', source)


if __name__ == "__main__":
    unittest.main()
