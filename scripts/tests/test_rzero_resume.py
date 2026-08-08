from __future__ import annotations

import tempfile
import unittest
import json
from pathlib import Path

from scripts.find_resume_checkpoint import find_complete_checkpoint
from scripts.rzero_pipeline_state import complete_stage, init_state, stage_complete
from scripts.validate_hf_checkpoint import validate_checkpoint


def write_training_checkpoint(root: Path, step: int, world_size: int = 2) -> Path:
    checkpoint = root / f"global_step_{step}"
    actor = checkpoint / "actor"
    actor.mkdir(parents=True)
    (checkpoint / "dataloader.pt").write_bytes(b"dataloader")
    for rank in range(world_size):
        (actor / f"model_world_size_{world_size}_rank_{rank}.pt").write_bytes(b"model")
        (actor / f"optim_world_size_{world_size}_rank_{rank}.pt").write_bytes(b"optimizer")
        (actor / f"extra_state_world_size_{world_size}_rank_{rank}.pt").write_bytes(b"extra")
    return checkpoint


class BaseRZeroResumeTests(unittest.TestCase):
    def test_partial_next_step_resumes_previous_atomic_step(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            step6 = write_training_checkpoint(root, 6)
            (root / "latest_global_step.txt").write_text("6", encoding="utf-8")

            partial7 = root / "global_step_7" / "actor"
            partial7.mkdir(parents=True)
            (partial7 / "model_world_size_2_rank_0.pt").write_bytes(b"partial")

            self.assertEqual(find_complete_checkpoint(root, 2), step6.resolve())

    def test_completed_step7_is_selected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_training_checkpoint(root, 6)
            step7 = write_training_checkpoint(root, 7)
            (root / "latest_global_step.txt").write_text("7", encoding="utf-8")
            self.assertEqual(find_complete_checkpoint(root, 2), step7.resolve())

    def test_incomplete_tracked_checkpoint_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            checkpoint = write_training_checkpoint(root, 7)
            (checkpoint / "actor" / "optim_world_size_2_rank_1.pt").unlink()
            (root / "latest_global_step.txt").write_text("7", encoding="utf-8")
            with self.assertRaisesRegex(FileNotFoundError, "missing or empty"):
                find_complete_checkpoint(root, 2)

    def test_stage_marker_requires_same_configuration_and_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = root / "state.json"
            marker = root / "stages" / "round_1" / "solver" / "_SUCCESS.json"
            artifact = root / "solver"
            artifact.mkdir()
            signature = init_state(state, {"model": "base", "rounds": "5"})
            complete_stage(state, marker, "round_1/solver", signature, [artifact], {"step": "15"})

            self.assertTrue(stage_complete(marker, signature, [artifact]))
            self.assertFalse(stage_complete(marker, "different", [artifact]))
            artifact.rmdir()
            self.assertFalse(stage_complete(marker, signature, []))

    def test_huggingface_validation_requires_weights(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "config.json").write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(FileNotFoundError, "no model weight"):
                validate_checkpoint(root)
            (root / "model.safetensors").write_bytes(b"weights")
            validate_checkpoint(root)

    def test_huggingface_validation_rejects_missing_index_shard(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "config.json").write_text("{}", encoding="utf-8")
            (root / "model-00001-of-00002.safetensors").write_bytes(b"weights")
            (root / "model.safetensors.index.json").write_text(
                json.dumps({"weight_map": {
                    "layer.0": "model-00001-of-00002.safetensors",
                    "layer.1": "model-00002-of-00002.safetensors",
                }}),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(FileNotFoundError, "missing indexed weight"):
                validate_checkpoint(root)


if __name__ == "__main__":
    unittest.main()
