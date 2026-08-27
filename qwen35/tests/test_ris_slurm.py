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
        self.assertIn("#SBATCH --time=7-00:00:00", script)
        self.assertIn("rzero-qwen35-bdc8b2c29981.sqsh", script)
        self.assertIn("a100_4x_qwen35_4b_base.yaml", script)
        self.assertIn("runs/rzero-qwen35-formal", script)
        self.assertIn('CONTAINER_RUN_DIR="/workspace/R-Zero/', script)
        self.assertIn('--run-dir "${CONTAINER_RUN_DIR}"', script)
        self.assertIn("--resume", script)
        self.assertIn('FROM_STAGE=${FROM_STAGE:-}', script)
        self.assertIn('pipeline_args+=(--from-stage "${FROM_STAGE}")', script)
        self.assertNotIn("smoke.yaml", script)
        self.assertNotIn("solver_gate.sh", script)

    def test_questioner_thinking_off_gate_is_detached_and_stops_before_solver_training(self):
        repo_root = Path(__file__).resolve().parents[2]
        script = (repo_root / "qwen35/scripts/ris_questioner_thinking_off_one_step.sbatch").read_text(
            encoding="utf-8"
        )
        self.assertIn("#SBATCH --account=compute2-jiaxinh", script)
        self.assertIn("#SBATCH --partition=general-gpu", script)
        self.assertIn("#SBATCH --gpus=4", script)
        self.assertIn("#SBATCH --time=7-00:00:00", script)
        self.assertIn("a100_4x_qwen35_4b_base_one_step_thinking_off.yaml", script)
        self.assertIn("qwen35.rzero.diagnostics.questioner_one_step", script)
        self.assertNotIn("solver_gate.sh", script)
        self.assertNotIn("qwen35/scripts/run.sh", script)

    def test_questioner_candidate_gate_reuses_official_n9_evaluator_without_training(self):
        repo_root = Path(__file__).resolve().parents[2]
        batch = (repo_root / "qwen35/scripts/ris_questioner_candidate_gate.sbatch").read_text(
            encoding="utf-8"
        )
        gate = (repo_root / "qwen35/scripts/questioner_candidate_gate.sh").read_text(encoding="utf-8")
        self.assertIn("#SBATCH --account=compute2-jiaxinh", batch)
        self.assertIn("#SBATCH --gpus=1", batch)
        self.assertIn("#SBATCH --time=7-00:00:00", batch)
        self.assertIn("questioner_candidate_gate.sh", batch)
        self.assertIn("qwen35.rzero.evaluate_candidates", gate)
        self.assertIn("--samples 9", gate)
        self.assertIn("--min-score 0.3", gate)
        self.assertIn("--max-score 0.8", gate)
        self.assertNotIn("train_grpo", gate)
        self.assertNotIn("curate_dataset", gate)

    def test_solver_thinking_off_gate_is_a_strict_detached_single_gpu_ab(self):
        repo_root = Path(__file__).resolve().parents[2]
        batch = (repo_root / "qwen35/scripts/ris_solver_thinking_off_gate.sbatch").read_text(
            encoding="utf-8"
        )
        gate = (repo_root / "qwen35/scripts/solver_thinking_off_gate.sh").read_text(
            encoding="utf-8"
        )
        diagnostic = (
            repo_root / "qwen35/rzero/diagnostics/evaluate_solver_thinking_off.py"
        ).read_text(encoding="utf-8")
        self.assertIn("#SBATCH --account=compute2-jiaxinh", batch)
        self.assertIn("#SBATCH --gpus=1", batch)
        self.assertIn("#SBATCH --time=7-00:00:00", batch)
        self.assertIn("solver_n9_gate/candidates.json", batch)
        self.assertIn("solver_n9_thinking_off_gate", batch)
        self.assertIn("solver_thinking_off_gate.sh", batch)
        self.assertIn("/tmp/rzero-qwen35-${UID}/${cache_scope}", gate)
        for expected in (
            "--samples 9",
            "--seed 0",
            "--temperature 1.0",
            "--top-p 1.0",
            "--top-k 40",
            "--min-score 0.3",
            "--max-score 0.8",
            "--expected-total-candidates 64",
            "--expected-parseable-candidates 60",
        ):
            self.assertIn(expected, gate)
        self.assertIn("--max-tokens 4096", batch)
        self.assertIn("solver_messages(item[\"question\"])", diagnostic)
        self.assertIn("enable_thinking=False", diagnostic)
        self.assertIn("stop_token_ids=[tokenizer.eos_token_id]", diagnostic)
        self.assertNotIn("train_grpo", gate)
        self.assertNotIn("curate_dataset", gate)
        self.assertNotIn("repeat_for_integration", diagnostic)

    def test_solver_16k_gate_changes_only_the_output_budget_and_destination(self):
        repo_root = Path(__file__).resolve().parents[2]
        baseline = (repo_root / "qwen35/scripts/ris_solver_thinking_off_gate.sbatch").read_text(
            encoding="utf-8"
        )
        extended = (
            repo_root / "qwen35/scripts/ris_solver_thinking_off_16k_gate.sbatch"
        ).read_text(encoding="utf-8")
        gate = (repo_root / "qwen35/scripts/solver_thinking_off_gate.sh").read_text(
            encoding="utf-8"
        )
        self.assertIn("#SBATCH --account=compute2-jiaxinh", extended)
        self.assertIn("#SBATCH --gpus=1", extended)
        self.assertIn("#SBATCH --time=7-00:00:00", extended)
        self.assertIn("solver_n9_gate/candidates.json", extended)
        self.assertIn("solver_n9_thinking_off_gate/summary.json", extended)
        self.assertIn("solver_n9_thinking_off_16k_gate", extended)
        self.assertIn("--max-tokens 4096", baseline)
        self.assertIn("--max-tokens 16384", extended)
        self.assertIn("--comparison-baseline", extended)
        self.assertIn("--max-tokens \"${max_tokens}\"", gate)
        self.assertIn("--samples 9", gate)
        self.assertIn("--seed 0", gate)
        self.assertIn("--temperature 1.0", gate)
        self.assertIn("--top-p 1.0", gate)
        self.assertIn("--top-k 40", gate)
        self.assertNotIn("presence_penalty", gate)
        self.assertNotIn("train_grpo", extended)
        self.assertNotIn("curate_dataset", extended)

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
