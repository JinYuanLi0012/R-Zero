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
from qwen35.rzero.official_verl import build_pythonpath, verl_source_root
from qwen35.rzero.pipeline.checkpoint_recovery import recover_tracker
from qwen35.rzero.pipeline.training_lineage import build_training_lineage, ensure_training_lineage


def _override(name: str, value: object) -> str:
    if isinstance(value, bool):
        rendered = str(value).lower()
    else:
        rendered = str(value)
    return f"{name}={rendered}"


def sanitize_nvidia_visibility_env(env: dict[str, str]) -> dict[str, str]:
    """Remove ROCm selectors that conflict with CUDA in verl Ray workers."""
    sanitized = env.copy()
    sanitized.pop("ROCR_VISIBLE_DEVICES", None)
    sanitized.pop("HIP_VISIBLE_DEVICES", None)
    return sanitized


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
    population_manager_path = Path(__file__).parent / "rewards" / "population.py"
    # Formal values map released EasyR1's rollout_batch_size and actor global
    # batch size; the smoke profile scales them down explicitly.
    train_batch_size = algorithm[
        "questioner_prompt_batch_size" if is_questioner else "solver_prompt_batch_size"
    ]
    mini_batch_size = algorithm[
        "questioner_update_batch_size" if is_questioner else "solver_update_batch_size"
    ]
    micro_batch_size = 1
    round_dir = args.output_dir.parent.parent
    hydra_run_dir = round_dir / "logs" / "hydra" / args.experiment_name / "${now:%Y-%m-%d_%H-%M-%S}"

    overrides = {
        # The official /opt/verl checkout is intentionally read-only inside the
        # SquashFS image. Keep Hydra metadata with the persistent round logs
        # while retaining /opt/verl as cwd for unambiguous package resolution.
        "hydra.run.dir": str(hydra_run_dir),
        "hydra.job.chdir": False,
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
        # The pinned verl commit's official text-only Qwen3.5 FSDP recipes use
        # the model-specific packed path.  Its qwen3_5 patch carries cu_seqlens
        # through Gated DeltaNet and full-attention layers; the padded path was
        # observed to produce an invalid FlashAttention varlen QKV reshape.
        "actor_rollout_ref.model.use_remove_padding": True,
        "actor_rollout_ref.model.enable_gradient_checkpointing": True,
        "actor_rollout_ref.actor.strategy": "fsdp2",
        "actor_rollout_ref.ref.strategy": "fsdp2",
        "actor_rollout_ref.actor.freeze_vision_tower": True,
        "actor_rollout_ref.actor.use_torch_compile": False,
        "actor_rollout_ref.actor.optim.lr": algorithm["learning_rate"],
        "actor_rollout_ref.actor.ppo_mini_batch_size": mini_batch_size,
        "actor_rollout_ref.actor.ppo_micro_batch_size_per_gpu": micro_batch_size,
        "actor_rollout_ref.actor.use_dynamic_bsz": False,
        "actor_rollout_ref.actor.use_kl_loss": True,
        "actor_rollout_ref.actor.kl_loss_coef": algorithm["kl_coef"],
        "actor_rollout_ref.actor.kl_loss_type": "low_var_kl",
        "actor_rollout_ref.actor.checkpoint.save_contents": "[model,optimizer,extra]",
        # Current verl requires the per-GPU form for both reference-policy and
        # rollout log-prob forward passes when dynamic batching is disabled.
        # This is a memory partition only; it does not change PPO mini-batches.
        "actor_rollout_ref.ref.log_prob_micro_batch_size_per_gpu": 1,
        "actor_rollout_ref.rollout.name": "vllm",
        "actor_rollout_ref.rollout.n": rollouts,
        "actor_rollout_ref.rollout.log_prob_micro_batch_size_per_gpu": 1,
        "actor_rollout_ref.rollout.tensor_model_parallel_size": 1,
        "actor_rollout_ref.rollout.gpu_memory_utilization": 0.45,
        "actor_rollout_ref.rollout.enforce_eager": True,
        "actor_rollout_ref.rollout.enable_chunked_prefill": False,
        "+actor_rollout_ref.rollout.engine_kwargs.vllm.language_model_only": True,
        "reward.custom_reward_function.path": str(reward_path.resolve()),
        "reward.custom_reward_function.name": "compute_score",
        "reward.reward_manager.name": "RZeroPopulationRewardManager" if is_questioner else reward_manager,
        # Challenger diversity is defined over the complete rollout population;
        # splitting it across reward workers would change BLEU cluster shares.
        "reward.num_workers": 1 if is_questioner else 8,
        "trainer.project_name": "rzero_qwen35",
        "trainer.experiment_name": args.experiment_name,
        "trainer.logger": "[console]",
        # Keep the official synchronous V0 trainer to preserve the established
        # PPO/checkpoint path used by this migration.  Both V0 and V1 in this
        # pinned commit share the new reward loop; Questioner therefore uses
        # the importlib population adapter configured below.
        "trainer.use_v1": False,
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
    if is_questioner:
        overrides.update(
            {
                "reward.reward_manager.source": "importlib",
                "reward.reward_manager.module.path": str(population_manager_path.resolve()),
            }
        )
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
    config = load_config(args.config)
    steps = config["algorithm"]["questioner_steps" if args.role == "questioner" else "solver_steps"]
    lineage = build_training_lineage(
        role=args.role,
        model=args.model,
        train_file=args.train_file,
        val_file=args.val_file,
        config_snapshot=config,
        total_steps=steps,
    )
    ensure_training_lineage(args.output_dir, lineage, resume=args.resume)
    if args.resume:
        recover_tracker(args.output_dir)
    env = sanitize_nvidia_visibility_env(os.environ)
    env.setdefault("VLLM_USE_V1", "1")
    repo_root = Path(__file__).resolve().parents[2]
    official_root = verl_source_root(config["runtime"]["verl_source_root"])
    env["PYTHONPATH"] = build_pythonpath(official_root, repo_root, env.get("PYTHONPATH"))
    subprocess.run(command, check=True, env=env, cwd=official_root)


if __name__ == "__main__":
    main()
