from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import torch
from safetensors.torch import save_file

from methods.task_vector_rzero.resolve_base import build_manifest, verify_manifest


class ResolveBaseTest(unittest.TestCase):
    def test_local_base_is_content_addressed_and_rechecked(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "base"
            root.mkdir()
            (root / "config.json").write_text(json.dumps({"model_type": "tiny"}))
            weights = root / "model.safetensors"
            save_file({"weight": torch.ones(2, 2)}, weights)

            manifest = build_manifest(str(root), None)
            verify_manifest(manifest, str(root), None)
            self.assertEqual(manifest["source_type"], "local")
            self.assertEqual(len(manifest["identity_sha256"]), 64)

            extra = root / "generation_config.json"
            extra.write_text("{}")
            with self.assertRaisesRegex(ValueError, "file set changed"):
                verify_manifest(manifest, str(root), None)
            extra.unlink()

            save_file({"weight": torch.zeros(2, 2)}, weights)
            with self.assertRaisesRegex(ValueError, "changed or is missing"):
                verify_manifest(manifest, str(root), None)


if __name__ == "__main__":
    unittest.main()
