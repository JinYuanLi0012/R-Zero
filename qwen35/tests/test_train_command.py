import argparse
import sys
import unittest
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

from qwen35.rzero.reward_loop_compat import (
    _ConcurrencyActorClass,
    _patch_task_runner_actor,
    install_local_ray_runtime,
    install_population_reward_concurrency_patch,
    install_task_runner_setup_hook,
    required_reward_concurrency,
)
from qwen35.rzero.train_grpo import build_command, sanitize_nvidia_visibility_env


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "qwen35" / "configs" / "a100_4x_qwen35_4b_base.yaml"
SMOKE_CONFIG = ROOT / "qwen35" / "configs" / "a100_4x_qwen35_4b_base_smoke.yaml"
THINKING_OFF_CONFIG = ROOT / "qwen35" / "configs" / "a100_4x_qwen35_4b_base_one_step_thinking_off.yaml"


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
        self.assertIn("actor_rollout_ref.rollout.agent.num_workers=8", rendered)
        self.assertIn("actor_rollout_ref.actor.ppo_mini_batch_size=16", rendered)
        self.assertIn("actor_rollout_ref.actor.clip_ratio=0.2", rendered)
        self.assertIn("actor_rollout_ref.actor.clip_ratio_low=0.2", rendered)
        self.assertIn("actor_rollout_ref.actor.clip_ratio_high=0.3", rendered)
        self.assertIn("actor_rollout_ref.actor.clip_ratio_c=3.0", rendered)
        self.assertIn("actor_rollout_ref.rollout.temperature=1.0", rendered)
        self.assertIn("actor_rollout_ref.rollout.top_p=0.99", rendered)
        self.assertIn("actor_rollout_ref.rollout.seed=1", rendered)
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
        self.assertNotIn("apply_chat_template_kwargs.enable_thinking", rendered)
        self.assertNotIn("trainer.rollout_data_dir", rendered)

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

    def test_local_ray_runtime_does_not_attach_to_an_existing_cluster(self):
        calls = []

        def init(*args, **kwargs):
            calls.append((args, kwargs))
            return "ray-context"

        fake_ray = SimpleNamespace(init=init)
        with patch.dict(sys.modules, {"ray": fake_ray}):
            install_local_ray_runtime()
            result = fake_ray.init(runtime_env={"env_vars": {"A": "1"}})

        self.assertEqual(result, "ray-context")
        self.assertEqual(calls[0][1]["address"], "local")
        self.assertEqual(calls[0][1]["runtime_env"]["env_vars"], {"A": "1"})

    def test_population_hook_is_scoped_to_task_runner_run(self):
        events = []

        class TaskRunner:
            def run(self, config):
                events.append(("official", config))
                return "complete"

        actor_class = SimpleNamespace(
            __ray_metadata__=SimpleNamespace(modified_class=TaskRunner),
        )
        _patch_task_runner_actor(actor_class)
        with patch(
            "qwen35.rzero.reward_loop_compat.install_population_reward_concurrency_patch",
            side_effect=lambda: events.append(("patch", None)),
        ):
            result = TaskRunner().run("config")

        self.assertEqual(result, "complete")
        self.assertEqual(events, [("patch", None), ("official", "config")])
        self.assertFalse(hasattr(actor_class, "runtime_env"))

    def test_official_run_ppo_wraps_only_task_runner(self):
        calls = []
        main_ppo = ModuleType("verl.trainer.main_ppo")

        def run_ppo(config, task_runner_class):
            calls.append((config, task_runner_class))

        main_ppo.run_ppo = run_ppo
        verl = ModuleType("verl")
        trainer = ModuleType("verl.trainer")
        trainer.main_ppo = main_ppo
        verl.trainer = trainer
        with patch.dict(
            sys.modules,
            {"verl": verl, "verl.trainer": trainer, "verl.trainer.main_ppo": main_ppo},
        ):
            install_task_runner_setup_hook()
            class TaskRunner:
                def run(self, config):
                    return config

            actor_class = SimpleNamespace(
                __ray_metadata__=SimpleNamespace(modified_class=TaskRunner),
            )
            main_ppo.run_ppo("config", actor_class)

        self.assertEqual(calls[0][0], "config")
        self.assertIs(calls[0][1], actor_class)
        self.assertTrue(TaskRunner._rzero_population_task_runner_patch)

    def test_solver_uses_naive_manager_and_four_gpus(self):
        rendered = "\n".join(build_command(self.args("solver")))
        self.assertIn("reward.reward_manager.name=naive", rendered)
        self.assertNotIn("reward.reward_manager.source=importlib", rendered)
        self.assertIn("trainer.use_v1=false", rendered)
        self.assertIn("trainer.n_gpus_per_node=4", rendered)
        self.assertIn("trainer.total_training_steps=15", rendered)
        self.assertIn("data.train_batch_size=512", rendered)
        self.assertIn("actor_rollout_ref.rollout.n=5", rendered)
        self.assertIn("actor_rollout_ref.rollout.agent.num_workers=8", rendered)
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
        self.assertIn("actor_rollout_ref.rollout.agent.num_workers=8", questioner)
        self.assertIn("data.train_batch_size=4", solver)
        self.assertIn("actor_rollout_ref.actor.ppo_mini_batch_size=4", solver)
        self.assertIn("actor_rollout_ref.rollout.agent.num_workers=4", solver)

    def test_thinking_off_gate_reaches_verl_dataset_and_captures_real_rollouts(self):
        questioner = "\n".join(build_command(self.args("questioner", THINKING_OFF_CONFIG)))
        solver = "\n".join(build_command(self.args("solver", THINKING_OFF_CONFIG)))
        self.assertIn("+data.apply_chat_template_kwargs.enable_thinking=false", questioner)
        self.assertIn("trainer.rollout_data_dir=/diagnostics/training_rollouts", questioner)
        self.assertNotIn("apply_chat_template_kwargs.enable_thinking", solver)
        self.assertNotIn("trainer.rollout_data_dir", solver)

    def test_training_subprocess_removes_rocm_visibility_on_nvidia(self):
        original = {
            "CUDA_VISIBLE_DEVICES": "0,1",
            "ROCR_VISIBLE_DEVICES": "0,1,2,3",
            "HIP_VISIBLE_DEVICES": "0,1,2,3",
            "RAY_ADDRESS": "auto",
            "RAY_EXPERIMENTAL_NOSET_CUDA_VISIBLE_DEVICES": "1",
            "RAY_EXPERIMENTAL_NOSET_ROCR_VISIBLE_DEVICES": "1",
            "KEEP": "yes",
        }
        sanitized = sanitize_nvidia_visibility_env(original)
        self.assertEqual(sanitized["CUDA_VISIBLE_DEVICES"], "0,1")
        self.assertEqual(sanitized["KEEP"], "yes")
        self.assertNotIn("ROCR_VISIBLE_DEVICES", sanitized)
        self.assertNotIn("HIP_VISIBLE_DEVICES", sanitized)
        self.assertNotIn("RAY_ADDRESS", sanitized)
        self.assertNotIn("RAY_EXPERIMENTAL_NOSET_CUDA_VISIBLE_DEVICES", sanitized)
        self.assertNotIn("RAY_EXPERIMENTAL_NOSET_ROCR_VISIBLE_DEVICES", sanitized)
        self.assertIn("ROCR_VISIBLE_DEVICES", original)


if __name__ == "__main__":
    unittest.main()
