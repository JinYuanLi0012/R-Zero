import unittest
from pathlib import Path


class RisSlurmScriptTests(unittest.TestCase):
    def test_round0_smoke_uses_pinned_topology_and_isolated_profile(self):
        repo_root = Path(__file__).resolve().parents[2]
        script = (repo_root / "qwen35/scripts/ris_round0_smoke.sbatch").read_text(encoding="utf-8")
        self.assertIn("#SBATCH --partition=general-gpu", script)
        self.assertIn("#SBATCH --gpus=4", script)
        self.assertIn("#SBATCH --cpus-per-task=32", script)
        self.assertIn("#SBATCH --mem=512G", script)
        self.assertIn("#SBATCH --time=08:00:00", script)
        self.assertIn("rzero-qwen35:commit-81d554f1c4a871cc19387db929b1fad4a78cf170", script)
        self.assertIn("a100_4x_qwen35_4b_base_smoke.yaml", script)
        self.assertIn("--dry-run", script)
        self.assertIn("--resume", script)
        self.assertNotIn("a100_4x_qwen35_4b_base.yaml", script)


if __name__ == "__main__":
    unittest.main()
