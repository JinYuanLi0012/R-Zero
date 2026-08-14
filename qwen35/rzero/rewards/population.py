"""Whole-population reward-loop adapter for the R-Zero Challenger.

The pinned verl reward loop invokes ``run_single`` concurrently for each
trajectory, while released R-Zero computes the Challenger diversity penalty
over the complete prompt-batch x rollout population.  This adapter uses verl's
official importlib RewardManager extension point, gathers exactly that
population in the single configured reward worker, invokes the existing batch
``compute_score`` function once, and returns the aligned per-trajectory scores.
"""

from __future__ import annotations

import asyncio
import inspect
from typing import Any

from verl import DataProto
from verl.experimental.reward_loop.reward_manager.base import RewardManagerBase


class _PendingReward:
    """Simple record compatible with verl's non-registered dynamic loader."""

    def __init__(self, future, data_source, solution, ground_truth, extra_info):
        self.future = future
        self.data_source = data_source
        self.solution = solution
        self.ground_truth = ground_truth
        self.extra_info = extra_info


class RZeroPopulationRewardManager(RewardManagerBase):
    """Bridge verl's per-trajectory reward loop to R-Zero batch scoring."""

    def __init__(self, config, tokenizer, compute_score, **_: Any):
        super().__init__(config, tokenizer, compute_score)
        if compute_score is None:
            raise ValueError("RZeroPopulationRewardManager requires a custom compute_score")
        if int(config.reward.num_workers) != 1:
            raise ValueError("R-Zero population rewards require reward.num_workers=1")
        self.population_size = int(config.data.train_batch_size) * int(config.actor_rollout_ref.rollout.n)
        if self.population_size <= 0:
            raise ValueError("R-Zero reward population size must be positive")
        self._pending: list[_PendingReward] = []
        self._lock = asyncio.Lock()
        self._is_async_score = inspect.iscoroutinefunction(compute_score)

    async def _decode(self, data: DataProto) -> _PendingReward:
        if len(data) != 1:
            raise ValueError(f"expected one trajectory per reward-loop call, got {len(data)}")
        item = data[0]
        response_ids = item.batch["responses"]
        response_length = response_ids.shape[-1]
        valid_length = int(item.batch["attention_mask"][-response_length:].sum().item())
        valid_ids = response_ids[:valid_length]
        solution = await self.loop.run_in_executor(
            None, lambda: self.tokenizer.decode(valid_ids, skip_special_tokens=True)
        )
        reward_model = item.non_tensor_batch.get("reward_model", {})
        extra_info = dict(item.non_tensor_batch.get("extra_info", {}))
        extra_info["rollout_reward_scores"] = item.non_tensor_batch.get("reward_scores", {})
        return _PendingReward(
            future=asyncio.get_running_loop().create_future(),
            data_source=item.non_tensor_batch["data_source"],
            solution=solution,
            ground_truth=reward_model.get("ground_truth"),
            extra_info=extra_info,
        )

    async def _score_population(self, population: list[_PendingReward]) -> None:
        kwargs = {
            "data_sources": [item.data_source for item in population],
            "solution_strs": [item.solution for item in population],
            "ground_truths": [item.ground_truth for item in population],
            "extra_infos": [item.extra_info for item in population],
        }
        try:
            if self._is_async_score:
                results = await self.compute_score(**kwargs)
            else:
                results = await self.loop.run_in_executor(None, lambda: self.compute_score(**kwargs))
            if len(results) != len(population):
                raise RuntimeError(
                    f"population reward returned {len(results)} scores for {len(population)} trajectories"
                )
            for pending, result in zip(population, results):
                if isinstance(result, dict):
                    score = float(result["score"])
                    extra = dict(result)
                else:
                    score = float(result)
                    extra = {"acc": score}
                pending.future.set_result({"reward_score": score, "reward_extra_info": extra})
        except BaseException as error:
            for pending in population:
                if not pending.future.done():
                    pending.future.set_exception(error)

    async def run_single(self, data: DataProto) -> dict[str, Any]:
        pending = await self._decode(data)
        population: list[_PendingReward] | None = None
        async with self._lock:
            self._pending.append(pending)
            if len(self._pending) > self.population_size:
                raise RuntimeError(
                    f"reward population exceeded expected size {self.population_size}; "
                    "check train_batch_size and rollout.n"
                )
            if len(self._pending) == self.population_size:
                population, self._pending = self._pending, []
        if population is not None:
            await self._score_population(population)
        return await pending.future
