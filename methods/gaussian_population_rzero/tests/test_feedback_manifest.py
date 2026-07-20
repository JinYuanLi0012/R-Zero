from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

METHOD_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(METHOD_DIR))

from manifests import central_feedback_manifest, population_manifest


class CentralFeedbackManifestTests(unittest.TestCase):
    def test_population_manifest_explicitly_records_feedback_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "solver_population_manifest.json"
            population_manifest(
                SimpleNamespace(
                    center="unresolved-test-center",
                    role="solver",
                    round_index=1,
                    population_size=2,
                    sigma=0.001,
                    global_seed=42,
                    samples=10,
                    gpu_ids="2,3",
                    output=output,
                )
            )
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["solver_feedback_mode"], "population")
            self.assertEqual(payload["population_size"], 2)

    def test_manifest_records_one_logical_solver_and_disjoint_physical_replicas(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "solver_feedback_manifest.json"
            central_feedback_manifest(
                SimpleNamespace(
                    center="unresolved-test-center",
                    round_index=2,
                    samples=10,
                    gpu_ids="2,3",
                    output=output,
                )
            )
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["solver_feedback_mode"], "central")
            self.assertEqual(payload["logical_solver_count"], 1)
            self.assertEqual(payload["physical_replicas"], 2)
            self.assertEqual(payload["physical_gpu_ids"], ["2", "3"])
            self.assertTrue(payload["each_question_evaluated_once"])
            self.assertFalse(payload["perturbed"])
            self.assertNotIn("experts", payload)
            self.assertNotIn("sigma", payload)

    def test_manifest_rejects_no_physical_replica(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                central_feedback_manifest(
                    SimpleNamespace(
                        center="unresolved-test-center",
                        round_index=1,
                        samples=10,
                        gpu_ids="",
                        output=Path(directory) / "manifest.json",
                    )
                )


if __name__ == "__main__":
    unittest.main()
