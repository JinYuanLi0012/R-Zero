from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import torch
from safetensors import safe_open
from safetensors.torch import save_file

from methods.task_vector_rzero.compose_task_vectors import ModelLayout, compose


CONFIG = {
    "architectures": ["TinyForCausalLM"],
    "model_type": "tiny",
    "hidden_size": 2,
    "num_hidden_layers": 1,
    "num_attention_heads": 1,
    "vocab_size": 3,
    "tie_word_embeddings": False,
}


def write_model(root: Path, tensors: dict[str, torch.Tensor], config=None) -> None:
    root.mkdir()
    (root / "config.json").write_text(json.dumps(config or CONFIG), encoding="utf-8")
    first = "model-00001-of-00002.safetensors"
    second = "model-00002-of-00002.safetensors"
    save_file({"embed.weight": tensors["embed.weight"]}, root / first)
    save_file({"lm_head.weight": tensors["lm_head.weight"]}, root / second)
    index = {
        "metadata": {"total_size": sum(t.numel() * t.element_size() for t in tensors.values())},
        "weight_map": {"embed.weight": first, "lm_head.weight": second},
    }
    (root / "model.safetensors.index.json").write_text(json.dumps(index), encoding="utf-8")


def read_tensor(root: Path, key: str) -> torch.Tensor:
    index = json.loads((root / "model.safetensors.index.json").read_text())
    with safe_open(root / index["weight_map"][key], framework="pt", device="cpu") as reader:
        return reader.get_tensor(key)


def write_tied_model(root: Path, embed: torch.Tensor, include_lm_head: bool) -> None:
    root.mkdir()
    config = dict(CONFIG)
    config["tie_word_embeddings"] = True
    (root / "config.json").write_text(json.dumps(config), encoding="utf-8")
    tensors = {"model.embed_tokens.weight": embed}
    if include_lm_head:
        tensors["lm_head.weight"] = embed.clone()
    save_file(tensors, root / "model.safetensors")


class ComposeTaskVectorsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.base_tensors = {
            "embed.weight": torch.tensor([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]),
            "lm_head.weight": torch.tensor([[0.5, -1.0], [2.0, 3.0], [4.0, 5.0]]),
        }
        write_model(self.root / "base", self.base_tensors)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_multishard_weighted_composition_and_diagnostics(self) -> None:
        a1 = {key: value + 1.0 for key, value in self.base_tensors.items()}
        a2 = {key: value - 2.0 for key, value in self.base_tensors.items()}
        write_model(self.root / "a1", a1)
        write_model(self.root / "a2", a2)
        output = self.root / "output"

        compose(
            ModelLayout.inspect(self.root / "base"),
            [ModelLayout.inspect(self.root / "a1"), ModelLayout.inspect(self.root / "a2")],
            [1.0, 0.5],
            output,
            chunk_elements=2,
            provenance={"base": {"source": "base"}, "auxiliaries": [{"source": "a1"}, {"source": "a2"}]},
        )

        for key, base in self.base_tensors.items():
            # base + 1*(base+1-base) + .5*(base-2-base) == base
            torch.testing.assert_close(read_tensor(output, key).float(), base)
        diagnostics = json.loads((output / "task_vector_diagnostics.json").read_text())
        output_config = json.loads((output / "config.json").read_text())
        self.assertEqual(output_config["torch_dtype"], "bfloat16")
        self.assertEqual(diagnostics["scales"], [1.0, 0.5])
        self.assertAlmostEqual(diagnostics["cosine_similarity"][0][1], -1.0, places=6)
        self.assertAlmostEqual(diagnostics["combined_update_norm"], 0.0, places=6)

    def test_shape_mismatch_is_rejected(self) -> None:
        bad = dict(self.base_tensors)
        bad["lm_head.weight"] = torch.zeros(4, 2)
        write_model(self.root / "bad", bad)
        with self.assertRaisesRegex(ValueError, "shape mismatch"):
            compose(
                ModelLayout.inspect(self.root / "base"),
                [ModelLayout.inspect(self.root / "bad")],
                [1.0],
                self.root / "output",
                chunk_elements=2,
                provenance={"base": {}, "auxiliaries": [{}]},
            )

    def test_key_mismatch_is_rejected(self) -> None:
        bad = {"embed.weight": self.base_tensors["embed.weight"], "lm_head.weight": self.base_tensors["lm_head.weight"]}
        write_model(self.root / "bad", bad)
        index_path = self.root / "bad" / "model.safetensors.index.json"
        index = json.loads(index_path.read_text())
        second = index["weight_map"]["lm_head.weight"]
        del index["weight_map"]["lm_head.weight"]
        index["weight_map"]["other.weight"] = second
        save_file({"other.weight": bad["lm_head.weight"]}, self.root / "bad" / second)
        index_path.write_text(json.dumps(index))
        with self.assertRaisesRegex(ValueError, "tensor keys differ"):
            compose(
                ModelLayout.inspect(self.root / "base"),
                [ModelLayout.inspect(self.root / "bad")],
                [1.0],
                self.root / "output",
                chunk_elements=2,
                provenance={"base": {}, "auxiliaries": [{}]},
            )

    def test_config_mismatch_is_rejected(self) -> None:
        bad_config = dict(CONFIG)
        bad_config["hidden_size"] = 3
        write_model(self.root / "bad", self.base_tensors, bad_config)
        with self.assertRaisesRegex(ValueError, "incompatible model config"):
            compose(
                ModelLayout.inspect(self.root / "base"),
                [ModelLayout.inspect(self.root / "bad")],
                [1.0],
                self.root / "output",
                chunk_elements=2,
                provenance={"base": {}, "auxiliaries": [{}]},
            )

    def test_tied_lm_head_is_normalized_like_relex(self) -> None:
        embed = torch.tensor([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
        write_tied_model(self.root / "base_tied", embed, include_lm_head=True)
        write_tied_model(self.root / "aux_tied", embed + 0.5, include_lm_head=False)
        output = self.root / "tied_output"

        compose(
            ModelLayout.inspect(self.root / "base_tied"),
            [ModelLayout.inspect(self.root / "aux_tied")],
            [1.0],
            output,
            chunk_elements=2,
            provenance={"base": {}, "auxiliaries": [{}]},
        )

        layout = ModelLayout.inspect(output)
        self.assertEqual(layout.task_vector_keys(), {"model.embed_tokens.weight"})
        self.assertNotIn("lm_head.weight", layout.weight_map)
        with safe_open(output / "model.safetensors", framework="pt", device="cpu") as reader:
            torch.testing.assert_close(
                reader.get_tensor("model.embed_tokens.weight").float(), embed + 0.5
            )


if __name__ == "__main__":
    unittest.main()
