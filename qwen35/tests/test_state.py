import json
import tempfile
import unittest
from pathlib import Path

from qwen35.rzero.pipeline.state import Artifact, RunState, StateError, canonical_hash, validate_artifact


class StateTests(unittest.TestCase):
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

    def test_checkpoint_requires_all_state_classes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "fsdp_config.json").write_text("{}")
            (root / "model_world_size_2_rank_0.pt").write_bytes(b"model")
            with self.assertRaises(StateError):
                validate_artifact(Artifact(root, "checkpoint"))
            (root / "optim_world_size_2_rank_0.pt").write_bytes(b"optim")
            (root / "extra_state_world_size_2_rank_0.pt").write_bytes(b"extra")
            self.assertEqual(validate_artifact(Artifact(root, "checkpoint"))["kind"], "checkpoint")


if __name__ == "__main__":
    unittest.main()
