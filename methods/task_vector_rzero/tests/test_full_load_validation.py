from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import torch
from tokenizers import Tokenizer, models, pre_tokenizers
from transformers import PreTrainedTokenizerFast, Qwen3Config, Qwen3ForCausalLM

from methods.task_vector_rzero.compose_task_vectors import ModelLayout, compose
from methods.task_vector_rzero.relex_rank1 import reconstruct_rank1


SCRIPT = Path(__file__).parents[1] / "validate_checkpoint.py"


def save_tiny_qwen(root: Path, offset: float) -> None:
    torch.manual_seed(0)
    config = Qwen3Config(
        vocab_size=16,
        hidden_size=8,
        intermediate_size=16,
        num_hidden_layers=1,
        num_attention_heads=2,
        num_key_value_heads=1,
        head_dim=4,
        max_position_embeddings=32,
        tie_word_embeddings=True,
    )
    model = Qwen3ForCausalLM(config)
    with torch.no_grad():
        for parameter in model.parameters():
            parameter.add_(offset)
    model.save_pretrained(root, safe_serialization=True)

    vocabulary = {"<unk>": 0, "<bos>": 1, "<eos>": 2, **{f"t{i}": i + 3 for i in range(13)}}
    backend = Tokenizer(models.WordLevel(vocabulary, unk_token="<unk>"))
    backend.pre_tokenizer = pre_tokenizers.Whitespace()
    tokenizer = PreTrainedTokenizerFast(
        tokenizer_object=backend,
        unk_token="<unk>",
        bos_token="<bos>",
        eos_token="<eos>",
    )
    tokenizer.save_pretrained(root)


class FullLoadValidationTest(unittest.TestCase):
    def test_composed_tiny_qwen_loads_and_remains_tied(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            save_tiny_qwen(root / "base", 0.0)
            save_tiny_qwen(root / "aux", 0.01)
            output = root / "output"
            compose(
                ModelLayout.inspect(root / "base"),
                [ModelLayout.inspect(root / "aux")],
                [1.0],
                output,
                chunk_elements=16,
                provenance={"base": {}, "auxiliaries": [{}]},
            )

            result = subprocess.run(
                [sys.executable, SCRIPT, output, "--full-load"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertTrue(report["full_load"]["tied_embeddings"])
            self.assertEqual(report["full_load"]["model_class"], "Qwen3ForCausalLM")

    def test_rank1_tiny_qwen_loads_and_remains_tied(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            save_tiny_qwen(root / "base", 0.0)
            for step, offset in ((5, 0.005), (10, 0.01), (15, 0.02)):
                save_tiny_qwen(root / f"step{step}", offset)
            output = root / "rank1"
            reconstruct_rank1(
                ModelLayout.inspect(root / "base"),
                [ModelLayout.inspect(root / f"step{step}") for step in (5, 10, 15)],
                [5, 10, 15],
                15,
                output,
                chunk_elements=16,
                provenance={"base": {}, "trajectory": []},
            )

            result = subprocess.run(
                [sys.executable, SCRIPT, output, "--full-load"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertTrue(report["full_load"]["tied_embeddings"])


if __name__ == "__main__":
    unittest.main()
