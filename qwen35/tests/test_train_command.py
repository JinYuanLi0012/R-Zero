import argparse
import unittest
from pathlib import Path

from qwen35.rzero.train_grpo import build_command


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

    def test_questioner_uses_official_batch_manager_and_two_gpus(self):
        command = build_command(self.args("questioner"))
        rendered = "\n".join(command)
        self.assertIn("reward.reward_manager.name=batch", rendered)
        self.assertIn("trainer.n_gpus_per_node=2", rendered)
        self.assertIn("trainer.total_training_steps=5", rendered)
        self.assertIn("data.train_batch_size=512", rendered)
        self.assertIn("reward.num_workers=1", rendered)
        self.assertIn("actor_rollout_ref.actor.strategy=fsdp2", rendered)
        self.assertIn("actor_rollout_ref.model.use_remove_padding=false", rendered)
        self.assertIn("+actor_rollout_ref.rollout.engine_kwargs.vllm.language_model_only=true", rendered)
        self.assertIn("hydra.run.dir=/logs/hydra/test/${now:%Y-%m-%d_%H-%M-%S}", rendered)
        self.assertIn("hydra.job.chdir=false", rendered)

    def test_solver_uses_naive_manager_and_four_gpus(self):
        rendered = "\n".join(build_command(self.args("solver")))
        self.assertIn("reward.reward_manager.name=naive", rendered)
        self.assertIn("trainer.n_gpus_per_node=4", rendered)
        self.assertIn("trainer.total_training_steps=15", rendered)

    def test_smoke_minibatches_pass_upstream_verl_batch_constraint(self):
        questioner = "\n".join(build_command(self.args("questioner", SMOKE_CONFIG)))
        solver = "\n".join(build_command(self.args("solver", SMOKE_CONFIG)))
        self.assertIn("data.train_batch_size=4", questioner)
        self.assertIn("actor_rollout_ref.actor.ppo_mini_batch_size=4", questioner)
        self.assertIn("data.train_batch_size=4", solver)
        self.assertIn("actor_rollout_ref.actor.ppo_mini_batch_size=4", solver)


if __name__ == "__main__":
    unittest.main()
