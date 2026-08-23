from pathlib import Path

import numpy as np
import torch

from verl.protocol import DataProto
from verl.workers.reward.config import RewardConfig
from verl.workers.reward.function import BatchFunctionRewardManager


class Tokenizer:
    def decode(self, token_ids, skip_special_tokens=True):
        return "response"


def batch():
    return DataProto.from_dict(
        tensors={
            "responses": torch.tensor([[1], [2]]),
            "response_mask": torch.ones((2, 1), dtype=torch.long),
        },
        non_tensors={
            "ground_truth": np.array(["a", "b"], dtype=object),
            "source": np.array(["rzero", "terra"], dtype=object),
        },
    )


def reward_file(tmp_path: Path, with_source: bool) -> str:
    signature = ", source" if with_source else ""
    body = "assert source == ['rzero', 'terra']\n" if with_source else ""
    path = tmp_path / ("with_source.py" if with_source else "baseline.py")
    path.write_text(
        f"def compute_score(predicts, targets{signature}):\n"
        f"    {body or 'pass'}\n"
        "    return [{'overall': 1.0} for _ in predicts]\n",
        encoding="utf-8",
    )
    return f"{path}:compute_score"


def test_baseline_reward_signature_is_unchanged(tmp_path):
    config = RewardConfig(reward_function=reward_file(tmp_path, False))
    config.post_init()
    manager = BatchFunctionRewardManager(config, Tokenizer())
    rewards, _ = manager.compute_reward(batch())
    assert rewards[:, -1].tolist() == [1.0, 1.0]


def test_source_is_forwarded_only_when_requested(tmp_path):
    config = RewardConfig(
        reward_function=reward_file(tmp_path, True),
        reward_function_data_keys=("source",),
    )
    config.post_init()
    manager = BatchFunctionRewardManager(config, Tokenizer())
    rewards, _ = manager.compute_reward(batch())
    assert rewards[:, -1].tolist() == [1.0, 1.0]
