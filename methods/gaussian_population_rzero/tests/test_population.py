from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

METHOD_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(METHOD_DIR))

try:
    import torch
except ImportError:  # Local macOS checkout need not contain the CUDA training env.
    torch = None


@unittest.skipIf(torch is None, "torch is available in the R-Zero training environment")
class GaussianPopulationTests(unittest.TestCase):
    def setUp(self):
        from population import GaussianPopulation, make_expert_specs

        class TinyTied(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.first = torch.nn.Linear(8, 8, bias=False)
                self.second = torch.nn.Linear(8, 8, bias=False)
                self.tied = self.first

        torch.manual_seed(7)
        self.model = TinyTied()
        self.population = GaussianPopulation(self.model)
        self.specs = make_expert_specs(
            role="solver", round_index=1, population_size=2, sigma=0.01, global_seed=42
        )

    def snapshot(self):
        return {name: value.detach().clone() for name, value in self.model.named_parameters()}

    def test_deterministic_distinct_experts_and_exact_restore(self):
        center = self.snapshot()
        self.population.apply(self.specs[0])
        first = self.snapshot()
        self.population.restore()
        for name, value in self.snapshot().items():
            self.assertTrue(torch.equal(value, center[name]))

        self.population.apply(self.specs[0])
        repeated = self.snapshot()
        for name in first:
            self.assertTrue(torch.equal(first[name], repeated[name]))

        self.population.apply(self.specs[1])
        second = self.snapshot()
        self.assertTrue(any(not torch.equal(first[name], second[name]) for name in first))

    def test_same_shape_parameters_do_not_repeat_noise(self):
        self.population.apply(self.specs[0])
        delta_first = self.model.first.weight.float() - self.population.anchor["first.weight"].float()
        delta_second = self.model.second.weight.float() - self.population.anchor["second.weight"].float()
        self.assertFalse(torch.equal(delta_first, delta_second))

    def test_tied_parameter_has_one_canonical_entry(self):
        names = self.population.parameter_names
        self.assertIn("first.weight", names)
        self.assertNotIn("tied.weight", names)
        self.assertEqual(len(names), 2)

    def test_unrelated_checkpoint_file_is_never_written(self):
        with tempfile.TemporaryDirectory() as directory:
            checkpoint = Path(directory) / "weights.bin"
            checkpoint.write_bytes(b"immutable")
            before = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
            self.population.apply(self.specs[0])
            self.population.restore()
            after = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
            self.assertEqual(before, after)


class QuotaTests(unittest.TestCase):
    def test_exact_allocations(self):
        from population_spec import allocate_quotas

        self.assertEqual(allocate_quotas(4000, 10), [400] * 10)
        self.assertEqual(allocate_quotas(7, 3), [3, 2, 2])
        for total in range(1, 31):
            for population in range(1, total + 1):
                self.assertEqual(sum(allocate_quotas(total, population)), total)

    def test_attempt_seed_plan_is_deterministic_and_unique(self):
        from population_spec import allocate_quotas, make_attempt_seed_plan, make_expert_specs

        specs = make_expert_specs(
            role="questioner", round_index=1, population_size=10, sigma=0.001, global_seed=42
        )
        quotas = allocate_quotas(4000, 10)
        first = make_attempt_seed_plan(specs, quotas)
        second = make_attempt_seed_plan(specs, quotas)
        self.assertEqual(first, second)
        seeds = [seed for expert_seeds in first.values() for seed in expert_seeds]
        self.assertEqual(len(seeds), 4000)
        self.assertEqual(len(set(seeds)), 4000)

        next_round = make_expert_specs(
            role="questioner", round_index=2, population_size=10, sigma=0.001, global_seed=42
        )
        self.assertNotEqual(first, make_attempt_seed_plan(next_round, quotas))


if __name__ == "__main__":
    unittest.main()
