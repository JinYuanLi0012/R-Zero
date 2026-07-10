from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import torch
from safetensors import safe_open
from safetensors.torch import save_file

from methods.task_vector_rzero.compose_task_vectors import ModelLayout
from methods.task_vector_rzero.relex_rank1 import reconstruct_rank1


CONFIG = {
    "architectures": ["TinyForCausalLM"],
    "model_type": "tiny",
    "hidden_size": 2,
    "num_hidden_layers": 1,
    "num_attention_heads": 1,
    "vocab_size": 2,
    "tie_word_embeddings": False,
}


def write_model(root: Path, value: torch.Tensor) -> None:
    root.mkdir()
    (root / "config.json").write_text(json.dumps(CONFIG))
    save_file({"weight": value}, root / "model.safetensors")


class RelexRank1Test(unittest.TestCase):
    def test_checkpoint_reconstruction_matches_rank1_svd(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            base = torch.zeros(2, 2)
            deltas = [
                torch.tensor([[1.0, 0.0], [0.0, 0.0]]),
                torch.tensor([[2.0, 0.2], [0.0, 0.0]]),
                torch.tensor([[3.0, 1.0], [0.0, 0.2]]),
            ]
            write_model(root / "base", base)
            for step, delta in zip((5, 10, 15), deltas):
                write_model(root / f"step{step}", base + delta)

            output = root / "rank1"
            reconstruct_rank1(
                ModelLayout.inspect(root / "base"),
                [ModelLayout.inspect(root / f"step{step}") for step in (5, 10, 15)],
                [5, 10, 15],
                15,
                output,
                chunk_elements=2,
                provenance={"base": {}, "trajectory": []},
            )

            matrix = np.stack([delta.numpy().reshape(-1) for delta in deltas]).astype(np.float32)
            _, _, vh = np.linalg.svd(matrix, full_matrices=False)
            direction = vh[0]
            expected_delta = (matrix[-1] @ direction) * direction
            with safe_open(output / "model.safetensors", framework="pt", device="cpu") as reader:
                actual = reader.get_tensor("weight").float().numpy().reshape(-1)
            np.testing.assert_allclose(actual, expected_delta, atol=1e-2, rtol=1e-2)

            diagnostics = json.loads((output / "relex_rank1_diagnostics.json").read_text())
            self.assertEqual(diagnostics["rank"], 1)
            self.assertEqual(diagnostics["steps"], [5, 10, 15])
            self.assertGreater(diagnostics["per_tensor"]["weight"]["explained_variance"], 0.9)


if __name__ == "__main__":
    unittest.main()
