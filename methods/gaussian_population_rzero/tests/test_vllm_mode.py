from __future__ import annotations

import unittest
from pathlib import Path


METHOD_DIR = Path(__file__).resolve().parents[1]


class VllmModeTests(unittest.TestCase):
    def test_direct_vllm_entrypoints_force_v0_before_import(self):
        for filename in (
            "solver_population_server.py",
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


if __name__ == "__main__":
    unittest.main()
