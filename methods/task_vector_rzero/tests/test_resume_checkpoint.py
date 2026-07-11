from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from methods.task_vector_rzero.find_resume_checkpoint import find_complete_checkpoint
from verl.utils.checkpoint.checkpoint_manager import (
    atomic_write_checkpoint_tracker,
    prune_training_state_except_latest,
)


def write_checkpoint(root: Path, step: int, world_size: int = 2) -> Path:
    checkpoint = root / f"global_step_{step}"
    actor = checkpoint / "actor"
    huggingface = actor / "huggingface"
    huggingface.mkdir(parents=True)
    (huggingface / "config.json").write_text("{}", encoding="utf-8")
    (checkpoint / "dataloader.pt").write_bytes(b"dataloader")
    for rank in range(world_size):
        (actor / f"model_world_size_{world_size}_rank_{rank}.pt").write_bytes(b"model")
        (actor / f"optim_world_size_{world_size}_rank_{rank}.pt").write_bytes(b"optim")
        (actor / f"extra_state_world_size_{world_size}_rank_{rank}.pt").write_bytes(b"extra")
    return checkpoint


class ResumeCheckpointTest(unittest.TestCase):
    def test_all_models_remain_but_only_latest_training_state_remains(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            step1 = write_checkpoint(root, 1)
            step2 = write_checkpoint(root, 2)

            atomic_write_checkpoint_tracker(str(root), 2)
            removed = prune_training_state_except_latest(str(root), 2)

            self.assertTrue(removed)
            self.assertTrue((step1 / "actor/model_world_size_2_rank_0.pt").is_file())
            self.assertTrue((step1 / "actor/huggingface/config.json").is_file())
            self.assertFalse((step1 / "actor/optim_world_size_2_rank_0.pt").exists())
            self.assertFalse((step1 / "actor/extra_state_world_size_2_rank_0.pt").exists())
            self.assertFalse((step1 / "dataloader.pt").exists())
            self.assertTrue((step2 / "actor/optim_world_size_2_rank_0.pt").is_file())
            self.assertEqual(find_complete_checkpoint(root, 2), step2.resolve())

    def test_tracker_pointing_to_incomplete_checkpoint_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            checkpoint = write_checkpoint(root, 3)
            (checkpoint / "actor/optim_world_size_2_rank_1.pt").unlink()
            atomic_write_checkpoint_tracker(str(root), 3)

            with self.assertRaisesRegex(FileNotFoundError, "Missing or empty"):
                find_complete_checkpoint(root, 2)

    def test_missing_tracker_means_no_committed_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_checkpoint(root, 1)
            self.assertIsNone(find_complete_checkpoint(root, 2))


if __name__ == "__main__":
    unittest.main()
