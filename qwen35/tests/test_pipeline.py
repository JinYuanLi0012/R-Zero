import argparse
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from qwen35.rzero.pipeline.orchestrator import Pipeline
from qwen35.rzero.run_benchmark import apply_text_only_overlay


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "qwen35" / "configs" / "a100_4x_qwen35_4b_base.yaml"


class PipelineTests(unittest.TestCase):
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
            args = argparse.Namespace(
                run_dir=Path(temporary) / "run",
                config=str(CONFIG),
                resume=True,
                from_stage=None,
                dry_run=True,
                round=None,
            )
            pipeline = Pipeline(args)
            stages = pipeline.stages()
            self.assertEqual(len(stages), 73)
            self.assertEqual(len([stage for stage in stages if ".generate." in stage.key]), 20)
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                pipeline.run()
            self.assertIn("round_05.solver_export", buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
