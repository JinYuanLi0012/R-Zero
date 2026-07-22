#!/usr/bin/env python3

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from methods.task_vector_rzero.analysis.delta_definitions import discover_run_inputs


class DeltaDefinitionsTest(unittest.TestCase):
    def test_discovery_uses_pipeline_selected_checkpoints(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            base = root / "immutable_base"
            base.mkdir()
            stages = {}
            for round_number in range(1, 6):
                questioner = (
                    root / "questioners/q1/huggingface"
                    if round_number == 1
                    else root / f"questioners/q{round_number}/global_step_5/actor/huggingface"
                )
                base_fit = root / f"base_fits/a{round_number}/global_step_15/actor/huggingface"
                rank1 = root / f"rank1_fits/r{round_number}"
                composed = root / f"composed_solvers/v{round_number}"
                for path in (questioner, base_fit, rank1, composed):
                    path.mkdir(parents=True)
                for stage, artifact in (
                    ("questioner", questioner),
                    ("base_fit", base_fit),
                    ("relex_rank1", rank1),
                    ("compose", composed),
                ):
                    stages[f"round_{round_number}/{stage}"] = {"artifacts": [str(artifact)]}
            state = {
                "configuration": {"num_rounds": "5", "task_vector_method": "relex_rank1"},
                "stages": stages,
            }
            state_dir = root / "state"
            state_dir.mkdir()
            (state_dir / "run_state.json").write_text(json.dumps(state), encoding="utf-8")
            (state_dir / "base_manifest.json").write_text(
                json.dumps({"resolved_path": str(base), "identity_sha256": "base-id"}),
                encoding="utf-8",
            )

            inputs = discover_run_inputs(root)
            self.assertEqual(inputs.base_identity, "base-id")
            self.assertEqual(len(inputs.deltas), 15)
            self.assertEqual(inputs.deltas[0].start, "base")
            self.assertEqual(inputs.deltas[0].end, "q1")
            self.assertEqual(inputs.deltas[1].start, "q1")
            self.assertEqual(inputs.deltas[1].end, "q2")
            self.assertEqual(inputs.deltas[5].delta_id, "solver_rank1_r1")
            self.assertEqual(inputs.deltas[5].start, "base")
            self.assertEqual(inputs.deltas[10].delta_id, "solver_full_r1")
            self.assertIn("global_step_5", str(inputs.checkpoints["q5"]))


if __name__ == "__main__":
    unittest.main()
