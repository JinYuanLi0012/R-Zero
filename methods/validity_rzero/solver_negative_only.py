"""Route R-Zero Solver task gradients after the original full-group GRPO.

Terra advantages, rewards, returns, response masks and reference KL are untouched.
An all-disagree group has no task gradient, even if format rewards differ.
"""

from collections import defaultdict

import torch


@torch.no_grad()
def apply_solver_negative_only(data, reward_metrics):
    advantages = data.batch["advantages"]
    sources = data.non_tensor_batch["source"]
    group_ids = data.non_tensor_batch["uid"]
    matches = reward_metrics["solver_answer_match"]
    size = advantages.shape[0]
    if not (len(sources) == len(group_ids) == len(matches) == size):
        raise ValueError("Solver source, uid and answer-match metadata must align with every rollout")
    if any(source not in {"rzero", "terra"} for source in sources):
        raise ValueError("Solver negative-only requires rzero/terra source metadata")
    if any(match not in (0, 1) for match in matches):
        raise ValueError("solver_answer_match must contain binary, finite judgments")

    # Token balancing reorders the batch: group by uid, never by adjacent rows.
    groups = defaultdict(list)
    for i, uid in enumerate(group_ids):
        groups[uid].append(i)

    eligible = [False] * size
    rzero_groups = zero_agree_groups = all_agree_groups = 0
    for indices in groups.values():
        source = sources[indices[0]]
        if any(sources[i] != source for i in indices):
            raise ValueError("A Solver rollout group cannot mix rzero and terra sources")
        if source == "terra":
            continue
        rzero_groups += 1
        n_agree = sum(matches[i] for i in indices)
        zero_agree_groups += int(n_agree == 0)
        all_agree_groups += int(n_agree == len(indices))
        if n_agree > 0:
            for i in indices:
                eligible[i] = matches[i] == 0

    device = advantages.device
    rzero = torch.tensor([source == "rzero" for source in sources], device=device)
    eligible = torch.tensor(eligible, dtype=torch.bool, device=device)
    keep_negative = eligible[:, None] & (advantages < 0)
    keep = ~rzero[:, None] | keep_negative
    # Out-of-place: GRPO returns may alias the original advantages.
    # Do not recenter, rescale, drop rows or alter the actor's loss denominator.
    data.batch["advantages"] = torch.where(keep, advantages, torch.zeros_like(advantages))

    rzero_count = int(rzero.sum().item())
    kept_count = int(keep_negative.any(dim=-1).sum().item())
    return {
        "solver_negative_only/rzero_group_count": rzero_groups,
        "solver_negative_only/zero_agree_group_rate": zero_agree_groups / max(rzero_groups, 1),
        "solver_negative_only/all_agree_group_rate": all_agree_groups / max(rzero_groups, 1),
        "solver_negative_only/kept_negative_rollout_count": kept_count,
        "solver_negative_only/kept_negative_rollout_rate": kept_count / max(rzero_count, 1),
    }
