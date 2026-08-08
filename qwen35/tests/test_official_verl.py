import os
import unittest
from pathlib import Path

from qwen35.rzero.official_verl import assert_official_verl, build_pythonpath
from qwen35.rzero.validation.environment import hydra_compose_command


class OfficialVerlTests(unittest.TestCase):
    def test_official_verl_precedes_repository_and_inherited_path(self):
        rendered = build_pythonpath(Path("/opt/verl"), Path("/workspace/R-Zero"), "/legacy:/opt/verl")
        self.assertEqual(rendered.split(os.pathsep), ["/opt/verl", "/workspace/R-Zero", "/legacy"])

    def test_source_assertion_rejects_repository_shadow_package(self):
        with self.assertRaises(RuntimeError):
            assert_official_verl("/workspace/R-Zero/verl/__init__.py", Path("/opt/verl"))
        self.assertEqual(
            assert_official_verl("/opt/verl/verl/__init__.py", Path("/opt/verl")),
            Path("/opt/verl/verl/__init__.py"),
        )

    def test_smoke_composes_official_main_ppo_job(self):
        self.assertEqual(hydra_compose_command()[-4:], ["-m", "verl.trainer.main_ppo", "--cfg", "job"])


if __name__ == "__main__":
    unittest.main()
