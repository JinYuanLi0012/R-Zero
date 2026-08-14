"""Compatibility shim for whole-population rewards on official verl.

Ray async actors admit at most 1000 concurrent method calls by default. The
formal R-Zero Questioner population is 512 prompts x 4 rollouts = 2048
trajectories, and ``RZeroPopulationRewardManager`` must see that complete
population before any individual ``run_single`` call can return. Without a
larger actor concurrency limit, the first 1000 calls wait for the remaining
1048 calls that Ray will not admit.

The pinned verl release does not expose RewardLoopWorker concurrency as a
configuration field. This shim preserves verl's worker construction and only
adds ``max_concurrency`` to the existing Ray actor options for the R-Zero
population manager. No upstream source file is modified.
"""

from __future__ import annotations

from typing import Any


DEFAULT_ASYNC_ACTOR_CONCURRENCY = 1000
POPULATION_MANAGER = "RZeroPopulationRewardManager"


def required_reward_concurrency(config: Any) -> int:
    """Return enough admission slots to gather one complete rollout population."""

    population = int(config.data.train_batch_size) * int(config.actor_rollout_ref.rollout.n)
    if population <= 0:
        raise ValueError(f"reward population must be positive, got {population}")
    return max(DEFAULT_ASYNC_ACTOR_CONCURRENCY, population)


class _ConcurrencyActorClass:
    """Add a default concurrency option while retaining official actor options."""

    def __init__(self, actor_class: Any, max_concurrency: int):
        self.actor_class = actor_class
        self.max_concurrency = max_concurrency

    def options(self, **options: Any) -> Any:
        options.setdefault("max_concurrency", self.max_concurrency)
        return self.actor_class.options(**options)


def install_population_reward_concurrency_patch() -> None:
    """Patch the pinned manager idempotently before the official trainer starts."""

    from verl.experimental.reward_loop.reward_loop import RewardLoopManager

    if getattr(RewardLoopManager, "_rzero_population_concurrency_patch", False):
        return

    original = RewardLoopManager._init_reward_loop_workers

    def _init_reward_loop_workers(self: Any) -> Any:
        manager_name = str(self.config.reward.reward_manager.name)
        if manager_name != POPULATION_MANAGER:
            return original(self)
        if int(self.config.reward.num_workers) != 1:
            raise ValueError("R-Zero whole-population rewards require exactly one reward worker")

        official_actor_class = self.reward_loop_workers_class
        max_concurrency = required_reward_concurrency(self.config)
        print(f"RZERO_REWARD_LOOP_MAX_CONCURRENCY={max_concurrency}", flush=True)
        self.reward_loop_workers_class = _ConcurrencyActorClass(official_actor_class, max_concurrency)
        try:
            return original(self)
        finally:
            self.reward_loop_workers_class = official_actor_class

    RewardLoopManager._init_reward_loop_workers = _init_reward_loop_workers
    RewardLoopManager._rzero_population_concurrency_patch = True
