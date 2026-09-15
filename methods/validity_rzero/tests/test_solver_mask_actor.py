"""Run the actual actor forward/update on CPU; substitute FlashAttention's
padding helpers with equivalent tensor indexing (no GPU kernel is available).
"""
from types import SimpleNamespace

import pytest
import torch
import transformers.modeling_flash_attention_utils as flash_utils

from methods.validity_rzero.solver_token_mask import full_vocab_entropy, mask_negative_advantages
from verl.protocol import DataProto
from verl.trainer.core_algos import compute_kl, compute_policy_loss
from verl.utils.torch_functional import masked_mean
from verl.workers.actor.config import ActorConfig


@pytest.fixture
def actor_class(monkeypatch):
    def pad(hidden_states, indices, batch, seqlen):
        result = hidden_states.new_zeros((batch * seqlen, *hidden_states.shape[1:]))
        return result.index_copy(0, indices, hidden_states).reshape(batch, seqlen, -1)

    def unpad(hidden_states, mask):
        indices = mask.flatten().nonzero().flatten()
        return hidden_states.reshape(-1, hidden_states.shape[-1])[indices], indices, None, None

    monkeypatch.setattr(flash_utils, "pad_input", pad, raising=False)
    monkeypatch.setattr(flash_utils, "unpad_input", unpad, raising=False)
    monkeypatch.setattr(flash_utils, "index_first_axis", lambda values, indices: values[indices], raising=False)
    from verl.workers.actor.dp_actor import DataParallelPPOActor
    return DataParallelPPOActor


class ToyModel(torch.nn.Module):
    def __init__(self):
        super().__init__()
        torch.manual_seed(91)
        self.embedding = torch.nn.Embedding(19, 19)

    def forward(self, input_ids, **kwargs):
        return SimpleNamespace(logits=self.embedding(input_ids))


def fixture_inputs():
    ids = torch.tensor([[0, 3, 4, 5, 6, 7, 0], [8, 9, 10, 11, 12, 13, 14], [0, 1, 2, 3, 4, 0, 0]])
    attention = torch.tensor([[0, 1, 1, 1, 1, 1, 0], [1, 1, 1, 1, 1, 1, 1], [0, 1, 1, 1, 1, 0, 0]])
    return dict(input_ids=ids, attention_mask=attention,
                responses=ids[:, -4:], position_ids=(attention.cumsum(-1) - 1).clamp(min=0))


@pytest.mark.parametrize("padding_free", [False, True])
def test_actor_entropy_predicts_same_response_positions_as_logprobs(actor_class, padding_free):
    config = ActorConfig(padding_free=padding_free, use_torch_compile=False)
    model = ToyModel()
    actor = actor_class(config, model)
    inputs = fixture_inputs()
    logp, entropy = actor._forward_micro_batch(inputs, temperature=.8, return_entropy=True)
    logits = model(inputs["input_ids"]).logits[:, -5:-1] / .8
    expected_logp = logits.log_softmax(-1).gather(-1, inputs["responses"].unsqueeze(-1)).squeeze(-1)
    valid = inputs["attention_mask"][:, -4:].bool()
    torch.testing.assert_close(logp[valid], expected_logp[valid])
    torch.testing.assert_close(entropy[valid], full_vocab_entropy(logits)[valid])
    assert not entropy.requires_grad


def test_actual_actor_update_matches_manual_masked_pg_plus_full_kl(actor_class):
    config = ActorConfig(use_torch_compile=False, solver_token_masking=True,
                         micro_batch_size_per_device_for_update=1, max_grad_norm=1e9)
    config.global_batch_size_per_device = 3
    config.use_kl_loss, config.disable_kl, config.kl_penalty, config.kl_coef = True, False, "low_var_kl", .01
    model = ToyModel()

    class CaptureSGD(torch.optim.SGD):
        def step(self, *args, **kwargs):
            self.gradients = [p.grad.clone() for group in self.param_groups for p in group["params"]]
            return super().step(*args, **kwargs)

    optimizer = CaptureSGD(model.parameters(), lr=0.)
    actor = actor_class(config, model, optimizer)
    inputs = fixture_inputs()
    logp, entropy = actor._forward_micro_batch(inputs, temperature=1., return_entropy=True)
    old, ref = logp.detach().clone(), logp.detach().clone() + .15
    advantages = torch.tensor([[-1.] * 4, [0.] * 4, [.3, -.3, 0., 0.]])
    eligible = torch.tensor([True, False, False])
    response_mask = inputs["attention_mask"][:, -4:]
    routed, mask = mask_negative_advantages(advantages, logp, entropy, response_mask, eligible)
    loss = 0
    for i in range(3):
        pg = compute_policy_loss(old[i:i+1], logp[i:i+1], routed[i:i+1], response_mask[i:i+1], .2, .3, 3.)[0]
        kl = masked_mean(compute_kl(logp[i:i+1], ref[i:i+1], "low_var_kl"), response_mask[i:i+1])
        loss = loss + (pg + .01 * kl) / 3
    expected = torch.autograd.grad(loss, tuple(model.parameters()))
    data = DataProto.from_dict(tensors={**inputs, "old_log_probs": old, "ref_log_probs": ref,
                                       "advantages": advantages, "solver_negative_token_mask": eligible},
                               meta_info={"temperature": 1.})
    metrics = actor.update_policy(data)
    for actual, wanted in zip(optimizer.gradients, expected):
        torch.testing.assert_close(actual, wanted)
    assert metrics["actor/negative_mask_eligible_tokens"] == [3]
    assert metrics["actor/negative_mask_kept_tokens"] == [int(mask[0].sum())]
    assert torch.equal(data.batch["advantages"], advantages)  # no in-place routing/renormalization
