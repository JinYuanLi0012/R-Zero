"""Launch official verl PPO with narrowly scoped R-Zero compatibility hooks."""

from __future__ import annotations

from qwen35.rzero.reward_loop_compat import (
    install_local_ray_runtime,
    install_task_runner_setup_hook,
)


def main() -> None:
    install_local_ray_runtime()
    install_task_runner_setup_hook()
    from verl.trainer.main_ppo import main as official_main

    official_main()


if __name__ == "__main__":
    main()
