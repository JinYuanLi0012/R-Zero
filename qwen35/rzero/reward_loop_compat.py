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
        # Some verl revisions pass Ray's default explicitly.  Never allow an
        # upstream option to reduce admission below the complete population.
        options["max_concurrency"] = max(int(options.get("max_concurrency", 0)), self.max_concurrency)
        return self.actor_class.options(**options)


def _runtime_env_with_population_hook(runtime_env: Any = None) -> dict[str, Any]:
    """Return a copied runtime env with the R-Zero hook installed."""

    merged = dict(runtime_env or {})
    existing_hook = merged.get("worker_process_setup_hook")
    if existing_hook is None:
        merged["worker_process_setup_hook"] = install_population_reward_concurrency_patch
    elif existing_hook is not install_population_reward_concurrency_patch:
        if not callable(existing_hook):
            raise TypeError("existing Ray worker_process_setup_hook must be callable")

        def _combined_worker_setup_hook() -> None:
            existing_hook()
            install_population_reward_concurrency_patch()

        merged["worker_process_setup_hook"] = _combined_worker_setup_hook
    return merged


class _TaskRunnerActorClass:
    """Apply the setup hook to the CPU TaskRunner, not every Ray worker.

    Ray assigns accelerator visibility when a GPU actor receives its resource
    allocation.  A job-wide setup hook can import torch before that assignment
    and cache the driver's device mapping in every FSDP worker.  The reward
    manager is constructed by the CPU-only TaskRunner, so that is the only
    actor which needs this compatibility patch.
    """

    def __init__(self, actor_class: Any):
        self.actor_class = actor_class

    def options(self, **options: Any) -> Any:
        options["runtime_env"] = _runtime_env_with_population_hook(options.get("runtime_env"))
        return self.actor_class.options(**options)

    def remote(self, *args: Any, **kwargs: Any) -> Any:
        return self.options().remote(*args, **kwargs)


def install_task_runner_setup_hook() -> None:
    """Install reward compatibility only in official verl's TaskRunner actor."""

    import verl.trainer.main_ppo as main_ppo

    if getattr(main_ppo.run_ppo, "_rzero_task_runner_hook", False):
        return

    original_run_ppo = main_ppo.run_ppo

    def _run_ppo(config: Any, task_runner_class: Any) -> Any:
        return original_run_ppo(config, _TaskRunnerActorClass(task_runner_class))

    _run_ppo._rzero_task_runner_hook = True  # type: ignore[attr-defined]
    main_ppo.run_ppo = _run_ppo


def install_local_ray_runtime() -> None:
    """Force this single-node training process to start a fresh local Ray job."""

    import ray

    if getattr(ray.init, "_rzero_local_runtime", False):
        return

    original_init = ray.init

    def _ray_init(*args: Any, **kwargs: Any) -> Any:
        kwargs.setdefault("address", "local")
        return original_init(*args, **kwargs)

    _ray_init._rzero_local_runtime = True  # type: ignore[attr-defined]
    ray.init = _ray_init


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
