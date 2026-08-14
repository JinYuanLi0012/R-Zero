import argparse
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from qwen35.rzero.reward_loop_compat import (
    _ConcurrencyActorClass,
    install_population_reward_concurrency_patch,
    install_ray_worker_setup_hook,
    required_reward_concurrency,
)
from qwen35.rzero.train_grpo import build_command, sanitize_nvidia_visibility_env


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "qwen35" / "configs" / "a100_4x_qwen35_4b_base.yaml"
SMOKE_CONFIG = ROOT / "qwen35" / "configs" / "a100_4x_qwen35_4b_base_smoke.yaml"


class TrainCommandTests(unittest.TestCase):
    def args(self, role, config=CONFIG):
        return argparse.Namespace(
            role=role,
            config=str(config),
            model=Path("/model"),
            train_file=Path("/train.parquet"),
            val_file=Path("/val.parquet"),
            output_dir=Path("/checkpoints"),
            experiment_name="test",
            resume=True,
        )

    def test_questioner_uses_population_manager_and_two_gpus(self):
        command = build_command(self.args("questioner"))
        rendered = "\n".join(command)
        self.assertEqual(command[1:3], ["-m", "qwen35.rzero.verl_main_ppo"])
        self.assertIn("reward.reward_manager.name=RZeroPopulationRewardManager", rendered)
        self.assertIn("reward.reward_manager.source=importlib", rendered)
        self.assertIn("reward.reward_manager.module.path=", rendered)
        self.assertIn("/qwen35/rzero/rewards/population.py", rendered)
        self.assertIn("trainer.use_v1=false", rendered)
        self.assertIn("trainer.n_gpus_per_node=2", rendered)
        self.assertIn("trainer.total_training_steps=5", rendered)
        self.assertIn("data.train_batch_size=512", rendered)
        self.assertIn("actor_rollout_ref.rollout.n=4", rendered)
        self.assertIn("actor_rollout_ref.actor.ppo_mini_batch_size=4", rendered)
        self.assertIn("actor_rollout_ref.actor.ppo_micro_batch_size_per_gpu=1", rendered)
        self.assertIn("actor_rollout_ref.ref.log_prob_micro_batch_size_per_gpu=1", rendered)
        self.assertIn("actor_rollout_ref.rollout.log_prob_micro_batch_size_per_gpu=1", rendered)
        self.assertNotIn("actor_rollout_ref.ref.log_prob_micro_batch_size=", rendered)
        self.assertNotIn("actor_rollout_ref.rollout.log_prob_micro_batch_size=", rendered)
        self.assertIn("reward.num_workers=1", rendered)
        self.assertIn("actor_rollout_ref.actor.strategy=fsdp2", rendered)
        self.assertIn("actor_rollout_ref.model.use_remove_padding=true", rendered)
        self.assertIn("actor_rollout_ref.model.external_lib=qwen35.rzero.verl_text_only", rendered)
        self.assertIn("trainer.balance_batch=false", rendered)
        self.assertIn("+actor_rollout_ref.rollout.engine_kwargs.vllm.language_model_only=true", rendered)
        self.assertIn("hydra.run.dir=/logs/hydra/test/${now:%Y-%m-%d_%H-%M-%S}", rendered)
        self.assertIn("hydra.job.chdir=false", rendered)

    def test_formal_population_fits_reward_actor_concurrency(self):
        class Config:
            class data:
                train_batch_size = 512

            class actor_rollout_ref:
                class rollout:
                    n = 4

        self.assertEqual(required_reward_concurrency(Config), 2048)

    def test_concurrency_wrapper_retains_official_actor_options(self):
        class ActorClass:
            def options(self, **options):
                return options

        wrapped = _ConcurrencyActorClass(ActorClass(), 2048)
        self.assertEqual(
            wrapped.options(name="reward_loop_worker_0"),
            {"name": "reward_loop_worker_0", "max_concurrency": 2048},
        )

    def test_concurrency_wrapper_overrides_smaller_explicit_limit(self):
        class ActorClass:
            def options(self, **options):
                return options

        wrapped = _ConcurrencyActorClass(ActorClass(), 2048)
        self.assertEqual(wrapped.options(max_concurrency=1000)["max_concurrency"], 2048)

    def test_ray_init_installs_patch_in_worker_processes(self):
        calls = []

        def init(*args, **kwargs):
            calls.append((args, kwargs))
            return "ray-context"

        fake_ray = SimpleNamespace(init=init)
        with patch.dict(sys.modules, {"ray": fake_ray}):
            install_ray_worker_setup_hook()
            result = fake_ray.init(address="local", runtime_env={"env_vars": {"A": "1"}})

        self.assertEqual(result, "ray-context")
        self.assertEqual(calls[0][1]["runtime_env"]["env_vars"], {"A": "1"})
        self.assertIs(
            calls[0][1]["runtime_env"]["worker_process_setup_hook"],
            install_population_reward_concurrency_patch,
        )

    def test_solver_uses_naive_manager_and_four_gpus(self):
        rendered = "\n".join(build_command(self.args("solver")))
        self.assertIn("reward.reward_manager.name=naive", rendered)
        self.assertNotIn("reward.reward_manager.source=importlib", rendered)
        self.assertIn("trainer.use_v1=false", rendered)
        self.assertIn("trainer.n_gpus_per_node=4", rendered)
        self.assertIn("trainer.total_training_steps=15", rendered)
        self.assertIn("data.train_batch_size=512", rendered)
        self.assertIn("actor_rollout_ref.rollout.n=5", rendered)
        self.assertIn("actor_rollout_ref.actor.ppo_mini_batch_size=128", rendered)
        self.assertIn("actor_rollout_ref.ref.log_prob_micro_batch_size_per_gpu=1", rendered)
        self.assertIn("actor_rollout_ref.rollout.log_prob_micro_batch_size_per_gpu=1", rendered)
        self.assertIn("actor_rollout_ref.model.external_lib=qwen35.rzero.verl_text_only", rendered)
        self.assertIn("trainer.balance_batch=false", rendered)

    def test_smoke_minibatches_pass_upstream_verl_batch_constraint(self):
        questioner = "\n".join(build_command(self.args("questioner", SMOKE_CONFIG)))
        solver = "\n".join(build_command(self.args("solver", SMOKE_CONFIG)))
        self.assertIn("data.train_batch_size=4", questioner)
        self.assertIn("actor_rollout_ref.actor.ppo_mini_batch_size=4", questioner)
        self.assertIn("data.train_batch_size=4", solver)
        self.assertIn("actor_rollout_ref.actor.ppo_mini_batch_size=4", solver)

    def test_training_subprocess_removes_rocm_visibility_on_nvidia(self):
        original = {
            "CUDA_VISIBLE_DEVICES": "0,1",
            "ROCR_VISIBLE_DEVICES": "0,1,2,3",
            "HIP_VISIBLE_DEVICES": "0,1,2,3",
            "KEEP": "yes",
        }
        sanitized = sanitize_nvidia_visibility_env(original)
        self.assertEqual(sanitized["CUDA_VISIBLE_DEVICES"], "0,1")
        self.assertEqual(sanitized["KEEP"], "yes")
        self.assertNotIn("ROCR_VISIBLE_DEVICES", sanitized)
        self.assertNotIn("HIP_VISIBLE_DEVICES", sanitized)
        self.assertIn("ROCR_VISIBLE_DEVICES", original)


if __name__ == "__main__":
    unittest.main()
