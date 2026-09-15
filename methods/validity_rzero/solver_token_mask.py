"""TTPO probability x low-entropy mask, restricted to each valid response.

Entropy is over the FULL vocabulary, evaluated in detached FP32 token chunks.
Per-response 98th-percentile clipping/min-max normalization and median threshold
match TTPO's microbatch-wide implementation when microbatch size is one. Keeping
ties (>= median) follows that implementation and can retain more than half.
"""

import torch


@torch.no_grad()
def full_vocab_entropy(logits, chunk_size=64):
    if logits.ndim == 3:
        return torch.stack([full_vocab_entropy(row, chunk_size) for row in logits])
    if logits.ndim != 2:
        raise ValueError("Expected [tokens, vocab] or [batch, tokens, vocab] logits")
    entropy = torch.empty(logits.shape[0], dtype=torch.float32, device=logits.device)
    for start in range(0, len(logits), chunk_size):
        log_p = torch.log_softmax(logits[start:start + chunk_size].detach().float(), dim=-1)
        entropy[start:start + chunk_size] = -(log_p.exp() * log_p).nan_to_num(0.0).sum(-1)
    return entropy


@torch.no_grad()
def ttpo_token_mask(log_probs, entropy, response_mask):
    if log_probs.shape != entropy.shape or entropy.shape != response_mask.shape:
        raise ValueError("Token probabilities, full-vocab entropy and response mask must align")
    mask = torch.zeros_like(response_mask, dtype=torch.bool)
    for i in range(log_probs.shape[0]):
        valid = response_mask[i].bool()
        if not valid.any():
            continue
        h = entropy[i, valid].float()
        if not torch.isfinite(h).all() or not torch.isfinite(log_probs[i, valid]).all():
            raise ValueError("Nonfinite token probability/entropy in TTPO masking")
        lo, hi = h.min(), torch.quantile(h, 0.98)
        normalized = torch.zeros_like(h) if hi - lo < 1e-8 else ((h.clamp(max=hi) - lo) / (hi - lo)).clamp(0, 1)
        scores = -log_probs[i, valid].detach().float() * (1 - normalized)
        mask[i, valid] = scores >= torch.quantile(scores, 0.5)
    return mask


def mask_negative_advantages(advantages, log_probs, entropy, response_mask, eligible):
    """Change only the PG numerator. Never modify response_mask or KL inputs."""
    mask = ttpo_token_mask(log_probs.detach(), entropy.detach(), response_mask)
    active = eligible.bool()[:, None] & (advantages < 0) & response_mask.bool()
    return torch.where(active & ~mask, torch.zeros_like(advantages), advantages), mask
