from __future__ import annotations

import argparse
import json
import tempfile
import unittest
from pathlib import Path

import torch
from datasets import Dataset, load_dataset
from safetensors.torch import save_file

from methods.task_vector_rzero.materialize_bootstrap import (
    materialize_dataset,
    materialize_model,
)


class MaterializeBootstrapTest(unittest.TestCase):
    def test_local_questioner_is_content_addressed_and_symlinked(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "questioner"
            source.mkdir()
            (source / "config.json").write_text(
                json.dumps({"model_type": "tiny"}), encoding="utf-8"
            )
            save_file({"weight": torch.ones(2, 2)}, source / "model.safetensors")
            output = root / "run" / "q1" / "huggingface"
            manifest = root / "run" / "q1" / "bootstrap_questioner_manifest.json"
            args = argparse.Namespace(
                source=str(source), revision=None, output=output, manifest=manifest
            )

            materialize_model(args)
            materialize_model(args)

            self.assertTrue(output.is_symlink())
            self.assertEqual(output.resolve(), source.resolve())
            self.assertEqual(json.loads(manifest.read_text())["source"], str(source))

    def test_local_dataset_is_canonicalized_and_rechecked(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.parquet"
            Dataset.from_dict(
                {
                    "problem": ["p1", "p2"],
                    "answer": ["a1", "a2"],
                    "score": [0.4, 0.7],
                }
            ).to_parquet(str(source))
            output = root / "run" / "d1" / "train.parquet"
            manifest = root / "run" / "d1" / "dataset_manifest.json"
            args = argparse.Namespace(
                source=str(source),
                config=None,
                split="train",
                revision=None,
                output=output,
                manifest=manifest,
            )

            materialize_dataset(args)
            materialize_dataset(args)

            materialized = load_dataset("parquet", data_files=str(output), split="train")
            metadata = json.loads(manifest.read_text())
            self.assertEqual(len(materialized), 2)
            self.assertEqual(metadata["filtered_count"], 2)
            self.assertTrue(metadata["bootstrap"])

            output.write_bytes(output.read_bytes() + b"changed")
            with self.assertRaisesRegex(ValueError, "hash changed"):
                materialize_dataset(args)


if __name__ == "__main__":
    unittest.main()
