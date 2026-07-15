from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import torch
from safetensors import safe_open
from safetensors.torch import save_file

from methods.task_vector_rzero.compose_task_vectors import ModelLayout, _sha256
from methods.task_vector_rzero.extrapolate_rank1 import build_extrapolations
from methods.task_vector_rzero.resolve_base import build_manifest


CONFIG = {
    "architectures": ["TinyForCausalLM"],
    "model_type": "tiny",
    "hidden_size": 2,
    "num_hidden_layers": 1,
    "num_attention_heads": 1,
    "vocab_size": 2,
    "tie_word_embeddings": False,
}


def write_model(root: Path, weight: torch.Tensor) -> None:
    root.mkdir(parents=True)
    (root / "config.json").write_text(json.dumps(CONFIG), encoding="utf-8")
    save_file({"model.weight": weight}, root / "model.safetensors")


def read_weight(root: Path) -> torch.Tensor:
    layout = ModelLayout.inspect(root)
    filename = layout.weight_map["model.weight"]
    with safe_open(root / filename, framework="pt", device="cpu") as reader:
        return reader.get_tensor("model.weight")


def create_source_run(root: Path) -> tuple[Path, torch.Tensor, torch.Tensor]:
    source = root / "source"
    base_weight = torch.tensor([[1.0, 2.0], [3.0, 4.0]], dtype=torch.bfloat16)
    delta = torch.tensor([[0.5, -0.5], [1.0, -1.0]], dtype=torch.bfloat16)
    base = root / "base"
    rank1 = source / "rank1_fits" / "r1"
    write_model(base, base_weight)
    write_model(rank1, base_weight + delta)

    base_manifest = build_manifest(str(base), None)
    state_dir = source / "state"
    state_dir.mkdir(parents=True)
    (state_dir / "base_manifest.json").write_text(
        json.dumps(base_manifest), encoding="utf-8"
    )
    (state_dir / "run_state.json").write_text(
        json.dumps(
            {
                "run_fingerprint": "test-fingerprint",
                "configuration": {"task_vector_method": "relex_rank1"},
            }
        ),
        encoding="utf-8",
    )
    marker = state_dir / "round_1" / "relex_rank1" / "_SUCCESS.json"
    marker.parent.mkdir(parents=True)
    marker.write_text(
        json.dumps(
            {
                "stage": "round_1/relex_rank1",
                "run_fingerprint": "test-fingerprint",
                "artifacts": [str(rank1)],
            }
        ),
        encoding="utf-8",
    )
    weight_file = rank1 / "model.safetensors"
    (rank1 / "relex_rank1_manifest.json").write_text(
        json.dumps(
            {
                "algorithm": "relex_rank1_reconstruct",
                "rank": 1,
                "base": base_manifest,
                "weight_files": [
                    {
                        "name": weight_file.name,
                        "size": weight_file.stat().st_size,
                        "sha256": _sha256(weight_file),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return source, base_weight, delta


class Rank1ExtrapolationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.source, self.base, self.delta = create_source_run(self.root)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_builds_scaled_versions_from_only_round1_delta(self) -> None:
        output = self.root / "output"
        summary = build_extrapolations(
            self.source,
            output,
            [1.0, 2.0, 3.0, 4.0, 5.0],
            chunk_elements=2,
        )

        self.assertEqual([item["scale"] for item in summary["outputs"]], [1, 2, 3, 4, 5])
        for index, scale in enumerate(range(1, 6), start=1):
            actual = read_weight(output / "composed_solvers" / f"v{index}").float()
            expected = self.base.float() + scale * self.delta.float()
            torch.testing.assert_close(actual, expected)
            manifest = json.loads(
                (
                    output
                    / "composed_solvers"
                    / f"v{index}"
                    / "task_vector_manifest.json"
                ).read_text()
            )
            self.assertEqual(manifest["scales"], [float(scale)])
            self.assertEqual(len(manifest["auxiliaries"]), 1)

    def test_resume_validates_and_reuses_outputs(self) -> None:
        output = self.root / "output"
        build_extrapolations(self.source, output, [1.0, 2.0], chunk_elements=2)
        before = _sha256(output / "composed_solvers" / "v2" / "model.safetensors")

        build_extrapolations(
            self.source,
            output,
            [1.0, 2.0],
            chunk_elements=2,
            resume=True,
        )
        after = _sha256(output / "composed_solvers" / "v2" / "model.safetensors")
        self.assertEqual(before, after)

    def test_existing_output_requires_resume(self) -> None:
        output = self.root / "output"
        build_extrapolations(self.source, output, [1.0], chunk_elements=2)
        with self.assertRaisesRegex(FileExistsError, "Use --resume"):
            build_extrapolations(self.source, output, [1.0], chunk_elements=2)

    def test_output_cannot_be_written_inside_source_run(self) -> None:
        with self.assertRaisesRegex(ValueError, "outside the read-only source run"):
            build_extrapolations(
                self.source,
                self.source / "extrapolation",
                [1.0],
                chunk_elements=2,
            )

    def test_source_rank1_weight_tampering_is_rejected(self) -> None:
        rank1_weight = self.source / "rank1_fits" / "r1" / "model.safetensors"
        save_file({"model.weight": self.base + 7}, rank1_weight)
        with self.assertRaisesRegex(ValueError, "hash changed"):
            build_extrapolations(
                self.source,
                self.root / "output",
                [1.0],
                chunk_elements=2,
            )


if __name__ == "__main__":
    unittest.main()
