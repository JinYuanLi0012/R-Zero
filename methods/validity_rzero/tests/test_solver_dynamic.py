"""CPU tests of real DataProto, GRPO and mixed 16-vote/5-update orchestration."""

from collections import Counter

import numpy as np
import pytest
import torch

from examples.reward_function.math import compute_score
from methods.validity_rzero.solver_dynamic import (
    extract_answer, generate_mixed_rollouts, prepare_update, take_rows, vote,
)
from verl.protocol import DataProto
from verl.trainer.core_algos import compute_grpo_outcome_advantage


@pytest.mark.parametrize("answers,target,count,reason", [
    (["1/2", r"\frac{1}{2}", "3"], "1/2", 2, "valid"),
    (["A", "A", "B", "B"], None, 2, "tie"),
    (["A", "B", None], None, 1, "singleton"),
    ([None] * 16, None, 0, "no_answer"),
    (["A", "A"] + list("BCDEFGHIJKLMNO") + [None], "A", 2, "valid"),
])
def test_vote_uses_unique_plurality_not_absolute_majority(answers, target, count, reason):
    assert vote(answers) == (target, count, reason)


def test_extract_uses_existing_last_box_and_excludes_malformed_answers():
    assert extract_answer(r"\boxed{3} later \boxed{\frac{1}{2}}") == r"\frac{1}{2}"
    for text in ("no box", r"\boxed{}", r"\boxed{broken", r"\boxed{2} then \boxed{oops"):
        assert extract_answer(text) is None


def test_generation_preserves_terra_five_and_removes_dispatch_padding():
    sources = np.array(["terra", "rzero", "terra", "rzero", "rzero"], dtype=object)
    prompts = DataProto.from_dict(
        tensors={"input_ids": torch.arange(5)[:, None], "attention_mask": torch.ones(5, 1)},
        non_tensors={"raw_prompt_ids": np.arange(5, dtype=object)},
    )
    batch = DataProto.from_dict(
        tensors={"row_id": torch.arange(5)},
        non_tensors={"source": sources, "ground_truth": np.full(5, "A", dtype=object)},
    )
    calls = []

    def generate(padded):
        n = padded.meta_info["n"]
        calls.append((len(padded), n))
        ids = padded.batch["input_ids"].repeat_interleave(n, 0)
        return DataProto.from_dict(
            tensors={"responses": ids * 100 + torch.arange(n).repeat(len(padded))[:, None]},
            meta_info={"n": n},
        )

    output = generate_mixed_rollouts(batch, prompts, generate, world_size=4)
    assert calls == [(4, 16), (4, 5)]
    assert len(output) == 3 * 16 + 2 * 5
    for row_id, n in ((0, 5), (1, 16), (2, 5), (3, 16), (4, 16)):
        rows = output.batch["row_id"] == row_id
        assert int(rows.sum()) == n
        assert output.batch["responses"][rows, 0].tolist() == list(range(row_id * 100, row_id * 100 + n))
        assert len(set(output.non_tensor_batch["uid"][rows.numpy()])) == 1
    assert "n" not in output.meta_info


def full_batch():
    group_answers = {
        "mixed": ["1"] * 9 + ["2"] * 7,
        "minority": ["1"] * 2 + [str(i) for i in range(2, 16)],
        "one_negative": ["1"] * 15 + ["2"],
        "all": ["1"] * 16,
        "tie": ["1"] * 8 + ["2"] * 8,
        "single": [str(i) for i in range(16)],
        "empty": [None] * 16,
        "terra": ["1", "2", "1", "2", "2"],
    }
    ids, sources, texts = [], [], []
    for uid, answers in group_answers.items():
        for j, answer in enumerate(answers):
            ids.append(uid)
            sources.append("terra" if uid == "terra" else "rzero")
            body = r"\boxed{" + answer + "}" if answer is not None else "unextractable"
            # Format differences make all-agree raw advantages nonzero.
            texts.append(("<think>x</think> " if j % 2 else "") + body)
    size = len(ids)
    mask = torch.ones(size, 3, dtype=torch.long)
    mask[::2, -1] = 0
    responses = torch.zeros(size, 3, dtype=torch.long)
    responses[:, 0] = torch.arange(size)
    data = DataProto.from_dict(
        tensors={"responses": responses, "response_mask": mask, "original_row": torch.arange(size)},
        non_tensors={"uid": np.array(ids, dtype=object), "source": np.array(sources, dtype=object),
                     "ground_truth": np.full(size, "2", dtype=object)},
    )

    class Tokenizer:
        def decode(self, tokens, **kwargs):
            return texts[int(tokens[0])]

    def reward(batch):
        scores = compute_score(
            [texts[int(i)] for i in batch.batch["original_row"]],
            batch.non_tensor_batch["ground_truth"].tolist())
        tensor = torch.zeros_like(batch.batch["response_mask"], dtype=torch.float32)
        tensor[torch.arange(len(batch)), batch.batch["response_mask"].sum(-1) - 1] = torch.tensor([s["overall"] for s in scores])
        return tensor, {"solver_answer_match": [s["accuracy"] for s in scores],
                        "overall": [s["overall"] for s in scores]}
    return data, Tokenizer(), reward


def test_full_group_advantages_selection_and_terra_survive_reordering():
    data, tokenizer, reward = full_batch()
    data = take_rows(data, np.random.default_rng(42).permutation(len(data)))
    terra = data.non_tensor_batch["source"] == "terra"
    original_terra = take_rows(data, np.flatnonzero(terra))
    terra_scores, _ = reward(original_terra)
    terra_adv, _ = compute_grpo_outcome_advantage(
        terra_scores, original_terra.batch["response_mask"], original_terra.non_tensor_batch["uid"])
    original_masks = data.batch["response_mask"].clone()
    selected, stats, selected_rewards, audit = prepare_update(data, tokenizer, reward, seed=11)
    raw_adv, _ = compute_grpo_outcome_advantage(
        data.batch["token_level_rewards"], data.batch["response_mask"], data.non_tensor_batch["uid"])
    assert len(selected) == 8 * 5
    assert Counter(selected.non_tensor_batch["uid"]) == {uid: 5 for uid in set(data.non_tensor_batch["uid"])}
    assert len(set(selected.batch["original_row"].tolist())) == len(selected)
    torch.testing.assert_close(data.batch["response_mask"], original_masks)
    assert stats["solver_dynamic/tie_group_rate"] == pytest.approx(1 / 7)
    assert stats["solver_dynamic/singleton_group_rate"] == pytest.approx(1 / 7)
    assert stats["solver_dynamic/no_answer_group_rate"] == pytest.approx(1 / 7)
    assert stats["solver_dynamic/all_agree_group_rate"] == pytest.approx(1 / 7)
    assert audit
    for j in range(len(selected)):
        row_id = int(selected.batch["original_row"][j])
        original_idx = int(torch.nonzero(data.batch["original_row"] == row_id)[0])
        uid = selected.non_tensor_batch["uid"][j]
        if uid == "terra":
            terra_idx = int(torch.nonzero(original_terra.batch["original_row"] == row_id)[0])
            torch.testing.assert_close(selected.batch["advantages"][j], terra_adv[terra_idx], rtol=0, atol=0)
            assert selected.non_tensor_batch["ground_truth"][j] == "2"
            assert not selected.batch["solver_negative_token_mask"][j]
        elif uid in {"tie", "single", "empty", "all"} or selected_rewards["solver_answer_match"][j]:
            assert torch.count_nonzero(selected.batch["advantages"][j]) == 0
        else:
            torch.testing.assert_close(selected.batch["advantages"][j], raw_adv[original_idx], rtol=0, atol=0)
            assert selected.batch["solver_negative_token_mask"][j]
    for uid, n_pos in (("mixed", 2), ("minority", 2), ("one_negative", 4), ("all", 5)):
        rows = selected.non_tensor_batch["uid"] == uid
        assert sum(np.array(selected_rewards["solver_answer_match"])[rows]) == n_pos
    # In the 9/16 group, selected 2/5 statistics would yield different A.
    rows = selected.non_tensor_batch["uid"] == "mixed"
    wrong_adv, _ = compute_grpo_outcome_advantage(
        selected.batch["token_level_rewards"][rows], selected.batch["response_mask"][rows], np.array(["x"] * 5))
    assert not torch.allclose(selected.batch["returns"][rows], wrong_adv)


def test_selection_seed_is_reproducible_and_not_length_based():
    runs = []
    for seed in (10, 10, 11):
        data, tokenizer, reward = full_batch()
        selected, _, _, _ = prepare_update(data, tokenizer, reward, seed)
        runs.append(selected.batch["original_row"])
    assert torch.equal(runs[0], runs[1])
    assert not torch.equal(runs[0], runs[2])


def test_actual_mixed_reward_manager_sparse_metrics_align_after_selection():
    from verl.workers.reward.config import RewardConfig
    from verl.workers.reward.function import BatchFunctionRewardManager

    data, tokenizer, _ = full_batch()
    config = RewardConfig(reward_function="./methods/validity_rzero/mixed_reward.py:compute_score",
                          reward_function_data_keys=["source"])
    config.post_init()
    manager = BatchFunctionRewardManager(config, tokenizer)
    data = take_rows(data, np.random.default_rng(4).permutation(len(data)))
    selected, stats, rewards, _ = prepare_update(data, tokenizer, manager.compute_reward, seed=7)
    rzero = selected.non_tensor_batch["source"] == "rzero"
    assert len(rewards["accuracy"]) == int(rzero.sum()) == 35
    assert len(rewards["format"]) == 35
    assert len(rewards["correct"]) == 5
    assert len(rewards["format_ok"]) == 5
    assert rewards["actual_replay_ratio"] == [5 / 40] * 40
    _, expected = manager.compute_reward(selected)
    for key in rewards:
        assert rewards[key] == expected[key], key
