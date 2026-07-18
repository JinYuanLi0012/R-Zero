from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

METHOD_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(METHOD_DIR))

from manifests import verify_generation
from population_spec import allocate_quotas, make_attempt_seed_plan, make_expert_specs


class GenerationManifestTests(unittest.TestCase):
    def _fixture(self, root: Path) -> SimpleNamespace:
        population_size, total_budget, round_index = 3, 7, 1
        specs = make_expert_specs(
            role="questioner",
            round_index=round_index,
            population_size=population_size,
            sigma=0.001,
            global_seed=42,
        )
        quotas = allocate_quotas(total_budget, population_size)
        plan = make_attempt_seed_plan(specs, quotas)
        save_name = "questions"
        for shard, experts in enumerate(([0, 2], [1])):
            records = [
                {
                    "source_expert_index": expert_index,
                    "source_attempt_index": attempt_index,
                    "source_sampling_seed": sampling_seed,
                }
                for expert_index in experts
                for attempt_index, sampling_seed in enumerate(plan[expert_index])
            ]
            (root / f"{save_name}_{shard}.json").write_text(
                json.dumps(records), encoding="utf-8"
            )
            (root / f"{save_name}_{shard}_generation_manifest.json").write_text(
                json.dumps(
                    {
                        "expert_counts": {
                            str(expert_index): quotas[expert_index] for expert_index in experts
                        },
                        "expert_attempt_seeds": {
                            str(expert_index): plan[expert_index] for expert_index in experts
                        },
                        "generated_count": len(records),
                    }
                ),
                encoding="utf-8",
            )
        return SimpleNamespace(
            center="unresolved-test-center",
            round_index=round_index,
            population_size=population_size,
            sigma=0.001,
            global_seed=42,
            total_budget=total_budget,
            num_shards=2,
            generated_dir=root,
            save_name=save_name,
            gpu_ids="0,1",
            output=root / "population_manifest.json",
        )

    def test_exact_attempt_seed_plan_is_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            args = self._fixture(Path(directory))
            verify_generation(args)
            manifest = json.loads(args.output.read_text(encoding="utf-8"))
            seeds = [
                seed
                for expert_seeds in manifest["observed_attempt_seeds"].values()
                for seed in expert_seeds
            ]
            self.assertEqual(len(seeds), 7)
            self.assertEqual(len(set(seeds)), 7)

    def test_changed_attempt_seed_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = self._fixture(root)
            path = root / "questions_0.json"
            records = json.loads(path.read_text(encoding="utf-8"))
            records[0]["source_sampling_seed"] += 1
            path.write_text(json.dumps(records), encoding="utf-8")
            with self.assertRaises(RuntimeError):
                verify_generation(args)


if __name__ == "__main__":
    unittest.main()
