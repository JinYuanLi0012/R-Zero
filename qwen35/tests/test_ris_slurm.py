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
        self.assertIn("rzero-qwen35-bdc8b2c29981.sqsh", script)
        self.assertIn("26e47958e9b689f21eb63b730fff88c5d13854d407fff592cdddcda87f329ec5", script)
        self.assertIn("prepared image checksum mismatch", script)
        self.assertIn("export SLURM_EXPORT_ENV=ALL", script)
        self.assertEqual(script.count('--export="ALL,XDG_CACHE_HOME='), 2)
        self.assertNotIn("ENROOT_CACHE_PATH", script)
        self.assertIn("a100_4x_qwen35_4b_base_smoke.yaml", script)
        self.assertIn("rzero-qwen35-smoke-v2", script)
        self.assertIn("--dry-run", script)
        self.assertIn("--resume", script)
        self.assertNotIn("a100_4x_qwen35_4b_base.yaml", script)

    def test_image_prepare_job_imports_once_to_scratch_squashfs(self):
        repo_root = Path(__file__).resolve().parents[2]
        script = (repo_root / "qwen35/scripts/ris_prepare_image.sbatch").read_text(encoding="utf-8")
        self.assertIn("#SBATCH --partition=general-short", script)
        self.assertIn("enroot import --output", script)
        self.assertIn("docker://ghcr.io#jinyuanli0012/rzero-qwen35:commit-81d554f1", script)
        self.assertIn("/rzero-qwen35-bdc8b2c29981.sqsh", script)
        self.assertIn("mv \"${TEMP_IMAGE}\" \"${IMAGE_PATH}\"", script)
        self.assertIn('tee "${IMAGE_PATH}.sha256"', script)


if __name__ == "__main__":
    unittest.main()
