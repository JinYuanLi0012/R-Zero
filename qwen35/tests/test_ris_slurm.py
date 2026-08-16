import unittest
from pathlib import Path


class RisSlurmScriptTests(unittest.TestCase):
    def test_solver_gate_reuses_curated_data_and_exports_official_checkpoint(self):
        repo_root = Path(__file__).resolve().parents[2]
        script = (repo_root / "qwen35/scripts/solver_gate.sh").read_text(encoding="utf-8")
        self.assertIn("--role solver", script)
        self.assertIn("round_01/dataset/train.parquet", script)
        self.assertIn("a100_4x_qwen35_4b_base_smoke.yaml", script)
        self.assertIn("qwen35.rzero.export_model", script)
        self.assertIn("RZERO_SOLVER_GATE_OK", script)

    def test_compute2_solver_gate_is_a_detached_four_gpu_job(self):
        repo_root = Path(__file__).resolve().parents[2]
        script = (repo_root / "qwen35/scripts/ris_solver_gate.sbatch").read_text(encoding="utf-8")
        self.assertIn("#SBATCH --account=compute2-jiaxinh", script)
        self.assertIn("#SBATCH --partition=general-gpu", script)
        self.assertIn("#SBATCH --gpus=4", script)
        self.assertIn("#SBATCH --cpus-per-task=32", script)
        self.assertIn("#SBATCH --mem=512G", script)
        self.assertIn("#SBATCH --time=04:00:00", script)
        self.assertIn("rzero-qwen35-bdc8b2c29981.sqsh", script)
        self.assertIn("qwen35/scripts/solver_gate.sh", script)
        self.assertIn("--source-run-dir /workspace/R-Zero/runs/rzero-qwen35-one-step", script)
        self.assertIn("--output-dir /workspace/R-Zero/runs/rzero-qwen35-solver-gate", script)

    def test_compute2_formal_job_uses_only_formal_resumable_pipeline(self):
        repo_root = Path(__file__).resolve().parents[2]
        script = (repo_root / "qwen35/scripts/ris_formal.sbatch").read_text(encoding="utf-8")
        self.assertIn("#SBATCH --account=compute2-jiaxinh", script)
        self.assertIn("#SBATCH --partition=general-gpu", script)
        self.assertIn("#SBATCH --gpus=4", script)
        self.assertIn("#SBATCH --cpus-per-task=32", script)
        self.assertIn("#SBATCH --mem=512G", script)
        self.assertIn("#SBATCH --time=1-00:00:00", script)
        self.assertIn("rzero-qwen35-bdc8b2c29981.sqsh", script)
        self.assertIn("a100_4x_qwen35_4b_base.yaml", script)
        self.assertIn("runs/rzero-qwen35-formal", script)
        self.assertIn("--resume", script)
        self.assertNotIn("smoke.yaml", script)
        self.assertNotIn("solver_gate.sh", script)

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
