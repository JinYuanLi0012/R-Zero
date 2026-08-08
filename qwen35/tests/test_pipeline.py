import argparse
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from qwen35.rzero.pipeline.orchestrator import Pipeline
from qwen35.rzero.run_benchmark import apply_text_only_overlay


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "qwen35" / "configs" / "a100_4x_qwen35_4b_base.yaml"


class PipelineTests(unittest.TestCase):
    def args(self, run_dir, **overrides):
        values = dict(
            run_dir=Path(run_dir), config=str(CONFIG), resume=True,
            from_stage=None, dry_run=True, round=None,
        )
        values.update(overrides)
        return argparse.Namespace(**values)

    def test_benchmark_overlay_is_text_only_and_copy_local(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "generate.py").write_text("model = vllm.LLM(\n    model='x')\n")
            for name in ("eval_supergpqa.py", "eval_bbeh.py", "eval_mmlupro.py"):
                (root / name).write_text("model = LLM(model='x')\n")
            apply_text_only_overlay(root)
            self.assertIn("language_model_only=True", (root / "generate.py").read_text())
            self.assertIn("language_model_only=True", (root / "eval_bbeh.py").read_text())

    def test_formal_stage_graph(self):
        with tempfile.TemporaryDirectory() as temporary:
            args = self.args(Path(temporary) / "run")
            pipeline = Pipeline(args)
            stages = pipeline.stages()
            self.assertEqual(len(stages), 73)
            self.assertEqual(len([stage for stage in stages if ".generate." in stage.key]), 20)
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                pipeline.run()
            self.assertIn("round_05.solver_export", buffer.getvalue())

    def test_from_stage_quarantines_affected_checkpoints_and_forces_fresh_training(self):
        with tempfile.TemporaryDirectory() as temporary:
            pipeline = Pipeline(self.args(Path(temporary) / "run", from_stage="round_02.curate"))
            stages = pipeline.stages()
            solver_checkpoint = pipeline.run_dir / "round_02" / "solver" / "checkpoints"
            later_questioner = pipeline.run_dir / "round_03" / "questioner" / "checkpoints"
            (solver_checkpoint / "global_step_15").mkdir(parents=True)
            (later_questioner / "global_step_5").mkdir(parents=True)

            pipeline._prepare_recompute(stages, "round_02.curate")

            self.assertFalse(solver_checkpoint.exists())
            self.assertFalse(later_questioner.exists())
            self.assertIn("round_02.solver_train", pipeline.force_fresh_stages)
            self.assertIn("round_03.questioner_train", pipeline.force_fresh_stages)
            events = list((pipeline.run_dir / "manifests" / "recomputations").glob("*.json"))
            event = json.loads(events[0].read_text(encoding="utf-8"))
            self.assertEqual(len(event["moved_checkpoint_roots"]), 2)

    def test_round_and_from_stage_cannot_create_partial_downstream_lineage(self):
        with tempfile.TemporaryDirectory() as temporary:
            pipeline = Pipeline(
                self.args(Path(temporary) / "run", round=2, from_stage="round_02.curate")
            )
            with self.assertRaisesRegex(Exception, "cannot be combined"):
                pipeline.run()

    def test_recompute_training_disables_resume_but_failure_recovery_keeps_it(self):
        with tempfile.TemporaryDirectory() as temporary:
            pipeline = Pipeline(self.args(Path(temporary) / "run"))
            commands = []
            pipeline._run = lambda command, *args, **kwargs: commands.append(command)
            stage_key = "round_02.solver_train"
            pipeline.force_fresh_stages = {stage_key}
            pipeline._train_solver(2, Path("/model"), stage_key)
            self.assertNotIn("--resume", commands[-1])

            pipeline.force_fresh_stages.clear()
            pipeline._train_solver(2, Path("/model"), stage_key)
            self.assertIn("--resume", commands[-1])


if __name__ == "__main__":
    unittest.main()
