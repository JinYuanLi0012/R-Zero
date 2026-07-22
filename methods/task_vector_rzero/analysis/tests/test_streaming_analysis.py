#!/usr/bin/env python3

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

try:
    import torch
    from safetensors.torch import save_file

    from methods.task_vector_rzero.analysis.analyze_delta_geometry import (
        inspect_layouts,
        process_composition_tensor,
        process_tensor,
    )
    from methods.task_vector_rzero.analysis.delta_definitions import DeltaSpec, RunInputs

    DEPENDENCIES_AVAILABLE = True
except ModuleNotFoundError:
    DEPENDENCIES_AVAILABLE = False


@unittest.skipUnless(DEPENDENCIES_AVAILABLE, "torch and safetensors are required")
class StreamingAnalysisTest(unittest.TestCase):
    def _checkpoint(self, root: Path, name: str, value: "torch.Tensor") -> Path:
        path = root / name
        path.mkdir()
        (path / "config.json").write_text(
            json.dumps({"model_type": "toy", "tie_word_embeddings": False}),
            encoding="utf-8",
        )
        save_file({"weight": value}, path / "model.safetensors")
        return path

    def test_streamed_gram_matches_direct_flatten(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            base = torch.zeros((2, 3), dtype=torch.bfloat16)
            checkpoints = {"base": self._checkpoint(root, "base", base)}
            direct: list[torch.Tensor] = []
            deltas: list[DeltaSpec] = []
            rank_increments: list[torch.Tensor] = []

            previous_q = base
            for round_number in range(1, 6):
                increment = torch.zeros_like(base)
                increment.reshape(-1)[(round_number - 1) % increment.numel()] = float(round_number)
                q = previous_q + increment
                checkpoints[f"q{round_number}"] = self._checkpoint(root, f"q{round_number}", q)
                start = "base" if round_number == 1 else f"q{round_number - 1}"
                deltas.append(
                    DeltaSpec(
                        f"questioner_full_r{round_number}",
                        "questioner_full",
                        round_number,
                        start,
                        f"q{round_number}",
                    )
                )
                direct.append(increment.float().reshape(-1))
                previous_q = q
            for family, prefix, scale in (
                ("solver_rank1", "r", 1.0),
                ("solver_full", "a", 2.0),
            ):
                for round_number in range(1, 6):
                    increment = torch.zeros_like(base)
                    increment.reshape(-1)[(round_number - 1) % increment.numel()] = scale * round_number
                    checkpoints[f"{prefix}{round_number}"] = self._checkpoint(
                        root, f"{prefix}{round_number}", base + increment
                    )
                    deltas.append(
                        DeltaSpec(
                            f"{family}_r{round_number}",
                            family,
                            round_number,
                            "base",
                            f"{prefix}{round_number}",
                        )
                    )
                    direct.append(increment.float().reshape(-1))
                    if family == "solver_rank1":
                        rank_increments.append(increment)

            cumulative = torch.zeros_like(base)
            for round_number, increment in enumerate(rank_increments, start=1):
                cumulative = cumulative + increment
                checkpoints[f"v{round_number}"] = self._checkpoint(
                    root, f"v{round_number}", base + cumulative
                )

            inputs = RunInputs(root, "toy", checkpoints, tuple(deltas), 5)
            layouts = inspect_layouts(inputs)
            result = process_tensor(
                "weight",
                inputs,
                layouts,
                chunk_elements=2,
                device=torch.device("cpu"),
                start_ids=["base", "q1", "q2", "q3", "q4"],
            )
            expected = torch.stack(direct) @ torch.stack(direct).T
            torch.testing.assert_close(
                torch.tensor(result["gram"], dtype=torch.float64), expected.double()
            )

            composition = process_composition_tensor(
                "weight",
                inputs,
                layouts,
                chunk_elements=2,
                device=torch.device("cpu"),
            )
            torch.testing.assert_close(
                torch.tensor(composition["residual_norm_sq"]), torch.zeros(5)
            )


if __name__ == "__main__":
    unittest.main()
