"""Thin command builder for upstream verl GRPO.

No training loop is implemented here. This module validates R-Zero role
settings and execs ``verl.trainer.main_ppo`` with official configuration keys.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from qwen35.rzero.config import load_config


def _override(name: str, value: object) -> str:
    if isinstance(value, bool):
        rendered = str(value).lower()
    else:
        rendered = str(value)
    return f"{name}={rendered}"


def build_command(args: argparse.Namespace) -> list[str]:
    config = load_config(args.config)
    algorithm = config["algorithm"]
    data = config["data"]
    checkpoint = config["checkpoint"]
    is_questioner = args.role == "questioner"

    steps = algorithm["questioner_steps"] if is_questioner else algorithm["solver_steps"]
    rollouts = algorithm["questioner_rollouts"] if is_questioner else algorithm["solver_rollouts"]
    reward_path = Path(__file__).parent / "rewards" / ("challenger.py" if is_questioner else "solver.py")
    reward_manager = "batch" if is_questioner else "naive"
    train_batch_size = 4 if is_questioner else 128
    mini_batch_size = 16 if is_questioner else 128
    micro_batch_size = 1

    overrides = {
        "algorithm.adv_estimator": "grpo",
        "algorithm.use_kl_in_reward": False,
        "data.train_files": str(args.train_file),
        "data.val_files": str(args.val_file),
        "data.train_batch_size": train_batch_size,
        "data.max_prompt_length": data["max_prompt_length"],
        "data.max_response_length": data["max_response_length"],
        "data.filter_overlong_prompts": True,
        "data.truncation": "error",
        "data.seed": algorithm["seed"],
        "actor_rollout_ref.model.path": str(args.model),
        "actor_rollout_ref.model.trust_remote_code": False,
        "actor_rollout_ref.model.use_remove_padding": False,
        "actor_rollout_ref.model.enable_gradient_checkpointing": True,
        "actor_rollout_ref.actor.strategy": "fsdp2",
        "actor_rollout_ref.ref.strategy": "fsdp2",
        "actor_rollout_ref.actor.optim.lr": algorithm["learning_rate"],
        "actor_rollout_ref.actor.ppo_mini_batch_size": mini_batch_size,
        "actor_rollout_ref.actor.ppo_micro_batch_size_per_gpu": micro_batch_size,
        "actor_rollout_ref.actor.use_dynamic_bsz": False,
        "actor_rollout_ref.actor.use_kl_loss": True,
        "actor_rollout_ref.actor.kl_loss_coef": algorithm["kl_coef"],
        "actor_rollout_ref.actor.kl_loss_type": "low_var_kl",
        "actor_rollout_ref.actor.checkpoint.save_contents": "[model,optimizer,extra]",
        "actor_rollout_ref.rollout.name": "vllm",
        "actor_rollout_ref.rollout.n": rollouts,
        "actor_rollout_ref.rollout.tensor_model_parallel_size": 1,
        "actor_rollout_ref.rollout.gpu_memory_utilization": 0.45,
        "actor_rollout_ref.rollout.enforce_eager": True,
        "actor_rollout_ref.rollout.enable_chunked_prefill": False,
        "reward.custom_reward_function.path": str(reward_path.resolve()),
        "reward.custom_reward_function.name": "compute_score",
        "reward.reward_manager.name": reward_manager,
        "trainer.project_name": "rzero_qwen35",
        "trainer.experiment_name": args.experiment_name,
        "trainer.logger": "[console]",
        "trainer.nnodes": 1,
        "trainer.n_gpus_per_node": 2 if is_questioner else 4,
        "trainer.total_training_steps": steps,
        "trainer.save_freq": checkpoint["save_freq"],
        "trainer.max_actor_ckpt_to_keep": checkpoint["keep"],
        "trainer.default_local_dir": str(args.output_dir),
        "trainer.resume_mode": "auto" if args.resume else "disable",
        "trainer.test_freq": -1,
        "trainer.val_before_train": False,
    }
    return [sys.executable, "-m", "verl.trainer.main_ppo", *[_override(key, value) for key, value in overrides.items()]]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--role", choices=["questioner", "solver"], required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--train-file", type=Path, required=True)
    parser.add_argument("--val-file", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--experiment-name", required=True)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--print-command", action="store_true")
    args = parser.parse_args()
    command = build_command(args)
    if args.print_command:
        print(" ".join(command))
        return
    args.output_dir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.setdefault("VLLM_USE_V1", "1")
    subprocess.run(command, check=True, env=env)


if __name__ == "__main__":
    main()
