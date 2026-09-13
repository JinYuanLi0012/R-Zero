"""Small CPU checks using the real GRPO, PPO clipping and reference KL code."""

from types import SimpleNamespace

import numpy as np
import pytest
import torch

from methods.validity_rzero.mixed_reward import compute_score
from methods.validity_rzero.solver_negative_only import apply_solver_negative_only
from verl.trainer.core_algos import compute_grpo_outcome_advantage, compute_kl, compute_policy_loss
from verl.utils.torch_functional import masked_mean


def training_batch():
    # Interleave groups, as token balancing can do. All-disagree/all-agree
    # groups deliberately have different format rewards and nonzero raw A.
    matches = np.array([[0] * 5, [1, 1, 1, 0, 0], [1] * 5, [1, 0, 0, 0, 1]])
    rewards = torch.tensor([
        [0.1, 0.1, 0, 0, 0], [1, 1, 0.9, 0.1, 0],
        [1, 1, 0.9, 0.9, 0.9], [1, 0, -0.5, -0.1, 1],
    ]).flatten()
    order = torch.arange(20).reshape(4, 5).T.flatten()
    ids = np.repeat(["zero", "mixed", "all", "terra"], 5)[order.numpy()]
    sources = np.repeat(["rzero", "rzero", "rzero", "terra"], 5)[order.numpy()]
    mask = torch.ones(20, 3)
    mask[::2, -1] = 0  # Unequal response lengths, with padding.
    scores = torch.zeros_like(mask)
    scores[torch.arange(20), mask.sum(-1).long() - 1] = rewards[order]
    advantages, returns = compute_grpo_outcome_advantage(scores, mask, ids)
    data = SimpleNamespace(
        batch={"advantages": advantages, "returns": returns, "response_mask": mask,
               "token_level_scores": scores, "token_level_rewards": scores},
        non_tensor_batch={"source": sources, "uid": ids},
    )
    return data, {"solver_answer_match": matches.flatten()[order.numpy()].tolist()}


def policy_loss(log_probs, advantages, mask):
    return compute_policy_loss(torch.full_like(log_probs, -2.0), log_probs,
                               advantages, mask, 0.2, 0.2, 3.0)[0]


def test_group_edges_terra_and_original_normalization():
    data, metadata = training_batch()
    original = {key: value.clone() for key, value in data.batch.items()}
    ids = data.non_tensor_batch["uid"]
    stats = apply_solver_negative_only(data, metadata)
    for group in ("zero", "all"):
        assert original["advantages"][ids == group].abs().sum() > 0
        assert torch.count_nonzero(data.batch["advantages"][ids == group]) == 0
    torch.testing.assert_close(data.batch["advantages"][ids == "terra"],
                               original["advantages"][ids == "terra"], rtol=0, atol=0)
    for i in np.flatnonzero(ids == "mixed"):
        expected = torch.zeros(3) if metadata["solver_answer_match"][i] else original["advantages"][i]
        torch.testing.assert_close(data.batch["advantages"][i], expected, rtol=0, atol=0)
    for key in original.keys() - {"advantages"}:
        torch.testing.assert_close(data.batch[key], original[key], rtol=0, atol=0)
    assert stats["solver_negative_only/zero_agree_group_rate"] == pytest.approx(1 / 3)
    assert stats["solver_negative_only/all_agree_group_rate"] == pytest.approx(1 / 3)
    assert stats["solver_negative_only/kept_negative_rollout_count"] == 2
    assert stats["solver_negative_only/kept_negative_rollout_rate"] == pytest.approx(2 / 15)


@pytest.mark.parametrize("delta", [-1.0, 0.0, 0.4, 2.0])
def test_actual_clipped_policy_gradients_and_loss_denominator(delta):
    data, metadata = training_batch()
    original = data.batch["advantages"].clone()
    apply_solver_negative_only(data, metadata)
    mask = data.batch["response_mask"]
    log_probs = torch.full_like(original, -2.0 + delta, requires_grad=True)
    baseline_grad, = torch.autograd.grad(policy_loss(log_probs, original, mask), log_probs)
    routed_grad, = torch.autograd.grad(policy_loss(log_probs, data.batch["advantages"], mask), log_probs)
    active = data.batch["advantages"] != 0
    # Kept rows have exactly the original PPO gradients, including clipping.
    torch.testing.assert_close(routed_grad[active], baseline_grad[active], rtol=0, atol=0)
    assert torch.count_nonzero(routed_grad[~active]) == 0
    if delta == 0:
        torch.testing.assert_close(routed_grad, -data.batch["advantages"] / mask.sum())


def test_suppressed_task_rows_still_contribute_full_reference_kl():
    data, metadata = training_batch()
    apply_solver_negative_only(data, metadata)
    advantages, mask = data.batch["advantages"], data.batch["response_mask"]
    log_probs = torch.full_like(advantages, -2.0, requires_grad=True)
    ref_log_probs = torch.full_like(advantages, -2.3)
    pg = policy_loss(log_probs, advantages, mask)
    kl = 0.01 * masked_mean(compute_kl(log_probs, ref_log_probs, "low_var_kl"), mask)
    pg_grad, = torch.autograd.grad(pg, log_probs, retain_graph=True)
    kl_grad, = torch.autograd.grad(kl, log_probs, retain_graph=True)
    total_grad, = torch.autograd.grad(pg + kl, log_probs)
    suppressed = (advantages == 0) & mask.bool()
    assert torch.all(kl_grad[suppressed] != 0)
    torch.testing.assert_close(total_grad[suppressed], kl_grad[suppressed])
    torch.testing.assert_close(total_grad, pg_grad + kl_grad)
    assert torch.count_nonzero(total_grad[~mask.bool()]) == 0


def test_matching_is_mathematical_and_metadata_is_dense_for_mixed_sources():
    predictions = [r"\boxed{0.5}", r"\boxed{INVALID}", r"<think>x</think> \boxed{7}", "no box"]
    scores = compute_score(predictions, [r"\frac{1}{2}", "INVALID", "2", "2"],
                           ["rzero", "terra", "rzero", "terra"])
    assert [score["solver_answer_match"] for score in scores] == [1, 1, 0, 0]
    assert [score["overall"] for score in scores] == [0.9, 1, 0.1, -0.1]


def test_nonnegative_unmatched_advantages_are_never_kept():
    data, metadata = training_batch()
    ids = data.non_tensor_batch["uid"]
    wrong = [i for i in np.flatnonzero(ids == "mixed") if not metadata["solver_answer_match"][i]]
    data.batch["advantages"][wrong[0]] = 1.0
    data.batch["advantages"][wrong[1]] = 0.0
    apply_solver_negative_only(data, metadata)
    assert torch.count_nonzero(data.batch["advantages"][wrong]) == 0


@pytest.mark.parametrize("bad_metadata", ["short", "nan", "mixed_source"])
def test_bad_alignment_fails_instead_of_silently_routing_wrong_rollouts(bad_metadata):
    data, metadata = training_batch()
    if bad_metadata == "short":
        metadata["solver_answer_match"].pop()
    elif bad_metadata == "nan":
        metadata["solver_answer_match"][0] = float("nan")
    else:
        data.non_tensor_batch["source"][0] = "terra"
    with pytest.raises(ValueError):
        apply_solver_negative_only(data, metadata)
