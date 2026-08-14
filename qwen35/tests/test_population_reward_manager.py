import asyncio
import importlib.util
import sys
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


class _Scalar:
    def __init__(self, value):
        self.value = value

    def sum(self):
        return self

    def item(self):
        return self.value


class _Sequence(list):
    @property
    def shape(self):
        return (len(self),)

    def __getitem__(self, index):
        value = super().__getitem__(index)
        return _Sequence(value) if isinstance(index, slice) else value

    def sum(self):
        return _Scalar(sum(self))


class _Item:
    def __init__(self, token, source):
        self.batch = {
            "responses": _Sequence([token, 0]),
            "attention_mask": _Sequence([1, 1, 1, 0]),
        }
        self.non_tensor_batch = {
            "data_source": source,
            "reward_model": {"ground_truth": None},
            "extra_info": {},
        }


class _SingleData:
    def __init__(self, item):
        self.item = item

    def __len__(self):
        return 1

    def __getitem__(self, index):
        if index != 0:
            raise IndexError(index)
        return self.item


class PopulationRewardManagerTests(unittest.TestCase):
    def _load_class(self, register_module=True):
        base_module = types.ModuleType("verl.experimental.reward_loop.reward_manager.base")

        class RewardManagerBase:
            def __init__(self, config, tokenizer, compute_score):
                self.config = config
                self.tokenizer = tokenizer
                self.compute_score = compute_score
                self.loop = asyncio.get_running_loop()

        base_module.RewardManagerBase = RewardManagerBase
        verl_module = types.ModuleType("verl")
        verl_module.DataProto = object
        module_path = Path(__file__).resolve().parents[1] / "rzero/rewards/population.py"
        spec = importlib.util.spec_from_file_location("rzero_population_test_module", module_path)
        module = importlib.util.module_from_spec(spec)
        with patch.dict(
            sys.modules,
            {
                "verl": verl_module,
                "verl.experimental": types.ModuleType("verl.experimental"),
                "verl.experimental.reward_loop": types.ModuleType("verl.experimental.reward_loop"),
                "verl.experimental.reward_loop.reward_manager": types.ModuleType(
                    "verl.experimental.reward_loop.reward_manager"
                ),
                "verl.experimental.reward_loop.reward_manager.base": base_module,
            },
        ):
            if register_module:
                sys.modules[spec.name] = module
            try:
                spec.loader.exec_module(module)
            finally:
                sys.modules.pop(spec.name, None)
        return module.RZeroPopulationRewardManager

    def test_loads_with_verl_dynamic_loader_module_semantics(self):
        # verl.utils.import_utils.load_module executes an external module
        # without first registering it in sys.modules.
        self.assertEqual(self._load_class(register_module=False).__name__, "RZeroPopulationRewardManager")

    def test_scores_complete_population_once_and_preserves_alignment(self):
        async def exercise():
            manager_cls = self._load_class()
            config = SimpleNamespace(
                reward=SimpleNamespace(num_workers=1),
                data=SimpleNamespace(train_batch_size=1),
                actor_rollout_ref=SimpleNamespace(rollout=SimpleNamespace(n=2)),
            )
            calls = []

            def score(**kwargs):
                calls.append(kwargs["solution_strs"])
                return [{"score": 0.25}, {"score": -0.5}]

            tokenizer = SimpleNamespace(decode=lambda ids, skip_special_tokens: str(ids[0]))
            manager = manager_cls(config, tokenizer, score)
            first, second = await asyncio.gather(
                manager.run_single(_SingleData(_Item(11, "a"))),
                manager.run_single(_SingleData(_Item(22, "b"))),
            )
            self.assertEqual(calls, [["11", "22"]])
            self.assertEqual(first["reward_score"], 0.25)
            self.assertEqual(second["reward_score"], -0.5)

        asyncio.run(exercise())

    def test_requires_single_reward_worker(self):
        async def exercise():
            manager_cls = self._load_class()
            config = SimpleNamespace(
                reward=SimpleNamespace(num_workers=2),
                data=SimpleNamespace(train_batch_size=1),
                actor_rollout_ref=SimpleNamespace(rollout=SimpleNamespace(n=2)),
            )
            with self.assertRaisesRegex(ValueError, "reward.num_workers=1"):
                manager_cls(config, SimpleNamespace(), lambda **_: [])

        asyncio.run(exercise())


if __name__ == "__main__":
    unittest.main()
