from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve()
GAUSSIAN_DIR = HERE.parents[2] / "gaussian_population_rzero"
sys.path.insert(0, str(GAUSSIAN_DIR))

TORCH_AVAILABLE = importlib.util.find_spec("torch") is not None
if TORCH_AVAILABLE:
    import torch
    from population import GaussianPopulation
    from population_spec import make_expert_specs


@unittest.skipUnless(TORCH_AVAILABLE, "torch is installed in the server environment")
class PopulationIntegrationTests(unittest.TestCase):
    def test_anchor_relative_noise_does_not_accumulate_and_direction_is_shared(self):
        torch.manual_seed(3)
        model = torch.nn.Linear(4, 3, bias=False)
        population = GaussianPopulation(model)
        center = model.weight.detach().clone().float()
        small = make_expert_specs(
            role="solver", round_index=1, population_size=1, sigma=0.01, global_seed=42
        )[0]
        large = make_expert_specs(
            role="solver", round_index=1, population_size=1, sigma=0.02, global_seed=42
        )[0]
        population.apply(small)
        small_delta = model.weight.detach().clone().float() - center
        population.apply(large)
        large_delta = model.weight.detach().clone().float() - center
        self.assertTrue(torch.allclose(large_delta, 2 * small_delta, atol=1e-6))
        population.apply(small)
        self.assertTrue(torch.allclose(model.weight.detach().float() - center, small_delta))
        population.restore()
        self.assertTrue(torch.equal(model.weight.detach().float(), center))


if __name__ == "__main__":
    unittest.main()
