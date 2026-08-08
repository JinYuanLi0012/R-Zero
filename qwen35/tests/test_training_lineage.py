import tempfile
import unittest
from pathlib import Path

from qwen35.rzero.pipeline.state import StateError
from qwen35.rzero.pipeline.training_lineage import build_training_lineage, ensure_training_lineage


class TrainingLineageTests(unittest.TestCase):
    def _inputs(self, root: Path):
        model = root / "model"
        model.mkdir()
        (model / "config.json").write_text('{"model_type":"qwen3_5"}\n', encoding="utf-8")
        (model / "model.safetensors").write_bytes(b"weights")
        train = root / "train.parquet"
        val = root / "val.parquet"
        train.write_bytes(b"train-v1")
        val.write_bytes(b"val-v1")
        return model, train, val

    def test_matching_resume_is_allowed_but_changed_data_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            model, train, val = self._inputs(root)
            checkpoint = root / "checkpoints"
            expected = build_training_lineage(
                role="solver", model=model, train_file=train, val_file=val,
                config_snapshot={"algorithm": {"seed": 1}}, total_steps=15,
            )
            ensure_training_lineage(checkpoint, expected, resume=True)
            ensure_training_lineage(checkpoint, expected, resume=True)

            train.write_bytes(b"train-v2")
            changed = build_training_lineage(
                role="solver", model=model, train_file=train, val_file=val,
                config_snapshot={"algorithm": {"seed": 1}}, total_steps=15,
            )
            with self.assertRaisesRegex(StateError, "lineage mismatch"):
                ensure_training_lineage(checkpoint, changed, resume=True)

    def test_unlabelled_checkpoint_state_is_never_adopted(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            model, train, val = self._inputs(root)
            checkpoint = root / "checkpoints"
            (checkpoint / "global_step_15").mkdir(parents=True)
            expected = build_training_lineage(
                role="solver", model=model, train_file=train, val_file=val,
                config_snapshot={"algorithm": {"seed": 1}}, total_steps=15,
            )
            with self.assertRaisesRegex(StateError, "has no R-Zero lineage"):
                ensure_training_lineage(checkpoint, expected, resume=True)


if __name__ == "__main__":
    unittest.main()
