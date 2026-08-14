import json
import tempfile
import unittest
from pathlib import Path

from qwen35.rzero.pipeline.state import Artifact, RunState, StateError, canonical_hash, validate_artifact
from qwen35.rzero.pipeline.checkpoint_recovery import recover_tracker


class StateTests(unittest.TestCase):
    @staticmethod
    def make_checkpoint(root: Path, step: int, complete: bool = True):
        actor = root / f"global_step_{step}" / "actor"
        actor.mkdir(parents=True)
        (actor / "fsdp_config.json").write_text("{}")
        for rank in range(2):
            (actor / f"model_world_size_2_rank_{rank}.pt").write_bytes(b"model")
        if complete:
            for rank in range(2):
                (actor / f"optim_world_size_2_rank_{rank}.pt").write_bytes(b"optim")
                (actor / f"extra_state_world_size_2_rank_{rank}.pt").write_bytes(b"extra")

    def test_rewinds_corrupt_latest_checkpoint(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.make_checkpoint(root, 2, complete=True)
            self.make_checkpoint(root, 3, complete=False)
            (root / "latest_checkpointed_iteration.txt").write_text("3\n")
            self.assertEqual(recover_tracker(root), 2)
            self.assertEqual((root / "latest_checkpointed_iteration.txt").read_text().strip(), "2")

    def test_from_stage_invalidates_only_suffix(self):
        with tempfile.TemporaryDirectory() as temporary:
            state = RunState(Path(temporary), "fingerprint")
            keys = ["a", "b", "c"]
            for key in keys:
                path = state.stage_manifest(key)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("{}")
            state.invalidate_from(keys, "b")
            self.assertTrue(state.stage_manifest("a").exists())
            self.assertFalse(state.stage_manifest("b").exists())
            self.assertFalse(state.stage_manifest("c").exists())

    def test_input_change_invalidates_only_dependent_stage(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            input_file = root / "input.json"
            output_a = root / "a.json"
            output_b = root / "b.json"
            input_file.write_text("[]\n")
            output_a.write_text("[]\n")
            output_b.write_text("[]\n")
            state = RunState(root / "run", canonical_hash({"test": 1}))
            state.initialize({"test": 1})
            state.commit("shard.0", [Artifact(output_a, "json")], inputs=[Artifact(input_file, "json")])
            state.commit("shard.1", [Artifact(output_b, "json")])
            self.assertTrue(state.is_complete("shard.0", [Artifact(output_a, "json")], [Artifact(input_file, "json")]))
            input_file.write_text("[1]\n")
            self.assertFalse(state.is_complete("shard.0", [Artifact(output_a, "json")], [Artifact(input_file, "json")]))
            self.assertTrue(state.is_complete("shard.1", [Artifact(output_b, "json")]))

    def test_corrupt_shard_is_not_complete(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "rows.json"
            output.write_text(json.dumps([1, 2]))
            state = RunState(root / "run", "fingerprint")
            state.initialize({})
            artifact = Artifact(output, "json", expected_count=2)
            state.commit("generate.0", [artifact])
            output.write_text("[]\n")
            self.assertFalse(state.is_complete("generate.0", [artifact]))

    def test_model_manifest_survives_json_round_trip(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            model = root / "model"
            model.mkdir()
            (model / "config.json").write_text("{}\n")
            (model / "model.safetensors").write_bytes(b"weights")
            state = RunState(root / "run", "fingerprint")
            state.initialize({})
            artifact = Artifact(model, "model")
            state.commit("resolve_model", [artifact])
            self.assertTrue(state.is_complete("resolve_model", [artifact]))

    def test_checkpoint_manifest_survives_json_round_trip(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.make_checkpoint(root, 1)
            actor = root / "global_step_1" / "actor"
            state = RunState(root / "run", "fingerprint")
            state.initialize({})
            artifact = Artifact(actor, "checkpoint")
            state.commit("questioner_train", [artifact])
            self.assertTrue(state.is_complete("questioner_train", [artifact]))

    def test_checkpoint_requires_all_state_classes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "fsdp_config.json").write_text("{}")
            for rank in range(2):
                (root / f"model_world_size_2_rank_{rank}.pt").write_bytes(b"model")
            with self.assertRaises(StateError):
                validate_artifact(Artifact(root, "checkpoint"))
            for rank in range(2):
                (root / f"optim_world_size_2_rank_{rank}.pt").write_bytes(b"optim")
                (root / f"extra_state_world_size_2_rank_{rank}.pt").write_bytes(b"extra")
            self.assertEqual(validate_artifact(Artifact(root, "checkpoint"))["kind"], "checkpoint")


if __name__ == "__main__":
    unittest.main()
