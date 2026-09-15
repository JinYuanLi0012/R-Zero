import pytest
import torch

from methods.validity_rzero.solver_token_mask import full_vocab_entropy, mask_negative_advantages, ttpo_token_mask
from verl.trainer.core_algos import compute_kl, compute_policy_loss
from verl.utils.torch_functional import masked_mean


def test_chunked_entropy_matches_full_distribution_and_has_no_gradient():
    logits = torch.randn(2, 17, 101, requires_grad=True)
    log_p = logits.log_softmax(-1)
    expected = -(log_p.exp() * log_p).sum(-1)
    actual = full_vocab_entropy(logits, chunk_size=3)
    torch.testing.assert_close(actual, expected)
    assert not actual.requires_grad
    # The sampled token probability alone does not determine full entropy.
    probs = torch.tensor([[0.5, 0.25, 0.25], [0.5, 0.49, 0.01]])
    assert full_vocab_entropy(probs.log())[0] > full_vocab_entropy(probs.log())[1]


def test_per_response_q98_median_excludes_padding_and_handles_ties():
    logp = -torch.arange(1, 13, dtype=torch.float32).reshape(2, 6)
    entropy = torch.tensor([[0.1, 0.2, 0.4, 0.8, 90, 999], [2., 2, 2, 2, 2, 2]])
    response = torch.tensor([[1, 1, 1, 1, 1, 0], [1, 1, 1, 1, 0, 0]])
    mask = ttpo_token_mask(logp, entropy, response)
    for i in range(2):
        valid = response[i].bool()
        h = entropy[i, valid]
        upper, lower = h.quantile(.98), h.min()
        norm = torch.zeros_like(h) if upper == lower else ((h.clamp(max=upper) - lower) / (upper - lower)).clamp(0, 1)
        score = -logp[i, valid] * (1 - norm)
        assert torch.equal(mask[i, valid], score >= score.quantile(.5))
    assert not mask[~response.bool()].any()
    assert ttpo_token_mask(torch.zeros(1, 4), torch.ones(1, 4), torch.ones(1, 4)).all()
    assert not ttpo_token_mask(logp, entropy, torch.zeros_like(response)).any()


@pytest.mark.parametrize("delta", [-1., 0., .4, 2.])
def test_mask_only_removes_eligible_pg_and_preserves_kl_denominator_and_terra(delta):
    logp = torch.full((3, 6), -2. + delta, requires_grad=True)
    old = torch.full_like(logp, -2.)
    ref = torch.full_like(logp, -2.3)
    mask = torch.tensor([[1, 1, 1, 1, 0, 0], [1, 1, 1, 1, 1, 1], [1, 1, 1, 0, 0, 0]])
    advantages = torch.tensor([[-1.] * 6, [0.] * 6, [-.4] * 6])  # negative R-Zero, positive R-Zero, Terra
    entropy = torch.arange(18).reshape(3, 6).float()
    eligible = torch.tensor([True, False, False])
    routed, selected = mask_negative_advantages(advantages, logp, entropy, mask, eligible)
    original_mask = mask.clone()
    def pg(adv):
        return compute_policy_loss(old, logp, adv, mask, .2, .3, 3.)[0]
    kl = .01 * masked_mean(compute_kl(logp, ref, "low_var_kl"), mask)
    before, = torch.autograd.grad(pg(advantages), logp, retain_graph=True)
    kl_grad, = torch.autograd.grad(kl, logp, retain_graph=True)
    after, = torch.autograd.grad(pg(routed) + kl, logp)
    drop = eligible[:, None] & ~selected & mask.bool()
    expected = torch.where(drop, torch.zeros_like(before), before) + kl_grad
    torch.testing.assert_close(after, expected)
    torch.testing.assert_close(routed[2], advantages[2], rtol=0, atol=0)
    assert torch.equal(mask, original_mask)
    assert not routed.requires_grad and not selected.requires_grad
