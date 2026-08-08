import argparse
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from qwen35.rzero.pipeline.orchestrator import Pipeline


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "qwen35" / "configs" / "a100_4x_qwen35_4b_base.yaml"


class PipelineTests(unittest.TestCase):
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
