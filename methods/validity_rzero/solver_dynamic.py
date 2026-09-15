"""Current-policy voting on 16 R-Zero rollouts, followed by 5 update rows.

All group statistics precede selection. No target/advantage is recomputed during
PPO updates. Terra uses its original five rollouts and labeled reward.
"""

from collections import Counter, defaultdict
from functools import lru_cache
import re
import uuid

import numpy as np
import torch
from mathruler.grader import extract_boxed_content, grade_answer

from verl.protocol import DataProto, pad_dataproto_to_divisor, unpad_dataproto
from verl.trainer.core_algos import compute_grpo_outcome_advantage
from .solver_negative_only import apply_solver_negative_only


VOTE_N, UPDATE_N, POSITIVE_N = 16, 5, 2


def take_rows(data, indices):
    """DataProto.__getitem__ returns DataProtoItem for array indices; avoid it."""
    indices = np.asarray(indices, dtype=np.int64)
    return DataProto(
        batch=data.batch[torch.as_tensor(indices, device=data.batch.device)],
        non_tensor_batch={key: value[indices] for key, value in data.non_tensor_batch.items()},
        meta_info=data.meta_info.copy(),
    )


def generate_mixed_rollouts(batch, prompts, generate, world_size):
    sources = batch.non_tensor_batch["source"]
    if any(source not in {"rzero", "terra"} for source in sources):
        raise ValueError("Dynamic Solver requires rzero/terra source metadata")
    batch.non_tensor_batch["uid"] = np.array([str(uuid.uuid4()) for _ in sources], dtype=object)
    parts = []
    for source, n in (("rzero", VOTE_N), ("terra", UPDATE_N)):
        indices = np.flatnonzero(sources == source)
        if not len(indices):
            continue
        source_prompts = take_rows(prompts, indices)
        source_prompts.meta_info["n"] = n
        # Each source count may not divide the DP world size. Duplicates serve
        # dispatch only and are removed BEFORE voting or reward statistics.
        source_prompts, pad_size = pad_dataproto_to_divisor(source_prompts, world_size)
        output = unpad_dataproto(generate(source_prompts), pad_size * n)
        if len(output) != len(indices) * n:
            raise ValueError("Generated rollout count does not match source sampling plan")
        part = take_rows(batch, indices).repeat(n, interleave=True).union(output)
        parts.append(part)
    result = DataProto.concat(parts)
    result.meta_info = result.meta_info.copy()
    result.meta_info.pop("n", None)  # Sampling n differs by source; update n stays 5.
    return result


@lru_cache(maxsize=32768)
def equivalent(answer, target):
    if not answer or not target:
        return False
    if answer == target:
        return True
    try:
        return bool(grade_answer(answer, target))
    except Exception:
        return False


def extract_answer(response):
    # Use the SAME last-box extraction/normalization as the existing reward.
    response = re.sub(r"\s*(<|>|/)\s*", r"\1", response)
    start = response.rfind(r"\boxed{")
    if start < 0:
        return None
    depth = 1
    for char in response[start + len(r"\boxed{"):]:
        depth += (char == "{") - (char == "}")
        if depth == 0:
            answer = extract_boxed_content(response).strip()
            return answer if answer and answer != "None" else None
    return None


def vote(answers):
    clusters = []
    for i, answer in enumerate(answers):
        if answer is None:
            continue
        for representative, members in clusters:
            if equivalent(answer, representative):
                members.append(i)
                break
        else:
            clusters.append((answer, [i]))
    if not clusters:
        return None, 0, "no_answer"
    largest = max(len(members) for _, members in clusters)
    # Disjoint rejection reasons: singleton takes priority over singleton ties.
    if largest < 2:
        return None, largest, "singleton"
    winners = [answer for answer, members in clusters if len(members) == largest]
    if len(winners) != 1:
        return None, largest, "tie"
    return winners[0], largest, "valid"


def grouped_rows(data):
    groups = defaultdict(list)
    for i, uid in enumerate(data.non_tensor_batch["uid"]):
        groups[uid].append(i)
    for rows in groups.values():
        sources = {data.non_tensor_batch["source"][i] for i in rows}
        if len(sources) != 1 or not sources <= {"rzero", "terra"}:
            raise ValueError("Each uid must belong to one known source")
        expected = VOTE_N if next(iter(sources)) == "rzero" else UPDATE_N
        if len(rows) != expected:
            raise ValueError(f"Full group requires {expected} rows, got {len(rows)}")
    return groups


def prepare_targets(data, tokenizer):
    groups = grouped_rows(data)
    old_targets = data.non_tensor_batch["ground_truth"].astype(object).copy()
    targets = old_targets.copy()
    vote_valid = np.ones(len(data), dtype=bool)
    reasons = np.full(len(data), "terra", dtype=object)
    answers = np.full(len(data), None, dtype=object)
    texts = np.full(len(data), "", dtype=object)
    lengths = data.batch["response_mask"].sum(-1).long().tolist()
    counts = Counter()
    for rows in groups.values():
        if data.non_tensor_batch["source"][rows[0]] != "rzero":
            continue
        for i in rows:
            texts[i] = tokenizer.decode(data.batch["responses"][i, :lengths[i]], skip_special_tokens=True)
            answers[i] = extract_answer(texts[i])
        target, size, reason = vote(answers[rows])
        valid = reason == "valid"
        counts["groups"] += 1
        counts[reason] += 1
        counts["largest_fraction"] += size / VOTE_N
        counts["invalid_answers"] += sum(answers[i] is None for i in rows)
        counts["all_agree"] += int(valid and size == VOTE_N)
        counts["old_label_agree"] += int(valid and equivalent(target, str(old_targets[rows[0]])))
        for i in rows:
            targets[i] = target or ""  # No consensus: never fall back to the stored label.
            vote_valid[i] = valid
            reasons[i] = reason
            counts["clipped"] += int(lengths[i] == data.batch["responses"].shape[-1])
            counts["length_sum"] += lengths[i]
            # Bounded diagnostic, not a reward: a nonblank unit repeated >=10x
            # covering >=200 characters in the final 1000 characters.
            repeated = any(
                len(m.group(0)) >= 200 and m.group(1).strip()
                for m in re.finditer(r"(.{1,100}?)\1{9,}", texts[i][-1000:], re.DOTALL)
            )
            counts["repeated_tail"] += bool(repeated)
    data.non_tensor_batch.update(
        ground_truth=targets, solver_static_label=old_targets,
        solver_vote_valid=vote_valid, solver_vote_reason=reasons,
        solver_vote_answer=answers,
    )
    n = max(counts["groups"], 1)
    stats = {
        "group_count": counts["groups"], "largest_cluster_fraction": counts["largest_fraction"] / n,
        "invalid_answer_rate": counts["invalid_answers"] / (n * VOTE_N),
        "valid_group_rate": counts["valid"] / n, "all_agree_group_rate": counts["all_agree"] / n,
        "old_label_agreement_on_valid": counts["old_label_agree"] / max(counts["valid"], 1),
        "response_length_mean": counts["length_sum"] / (n * VOTE_N),
        "response_clip_rate": counts["clipped"] / (n * VOTE_N),
        "repeated_tail_rate": counts["repeated_tail"] / (n * VOTE_N),
    }
    stats.update({f"{reason}_group_rate": counts[reason] / n for reason in ("tie", "singleton", "no_answer")})
    return stats, texts


def select_update_rows(data, matches, seed):
    rng = np.random.default_rng(seed)
    selected = []
    counts = Counter(selected_positive_count=0, selected_negative_count=0)
    for rows in grouped_rows(data).values():
        if data.non_tensor_batch["source"][rows[0]] == "terra":
            selected.extend(rows)
            continue
        if not data.non_tensor_batch["solver_vote_valid"][rows[0]]:
            chosen = rng.choice(rows, UPDATE_N, replace=False).tolist()
        else:
            pos = rng.permutation([i for i in rows if matches[i]]).tolist()
            neg = rng.permutation([i for i in rows if not matches[i]]).tolist()
            n_pos = min(POSITIVE_N, len(pos))
            n_neg = min(UPDATE_N - POSITIVE_N, len(neg))
            n_pos += min(UPDATE_N - n_pos - n_neg, len(pos) - n_pos)
            n_neg += min(UPDATE_N - n_pos - n_neg, len(neg) - n_neg)
            chosen = pos[:n_pos] + neg[:n_neg]
            rng.shuffle(chosen)
            counts["selected_positive_count"] += n_pos
            counts["selected_negative_count"] += n_neg
        selected.extend(chosen)
    result = take_rows(data, selected)
    counts["selected_rzero_count"] = int(sum(result.non_tensor_batch["source"] == "rzero"))
    counts["selected_no_consensus_count"] = int(sum(
        (result.non_tensor_batch["source"] == "rzero") & ~result.non_tensor_batch["solver_vote_valid"]))
    counts["effective_negative_count"] = int(result.batch["solver_negative_token_mask"].sum())
    return result, dict(counts), selected


def prepare_update(data, tokenizer, reward, seed):
    """CPU orchestration; reward callback is the existing remote reward manager."""
    stats, texts = prepare_targets(data, tokenizer)
    reward_tensor, reward_metrics = reward(data)
    matches = reward_metrics["solver_answer_match"]
    # Refuse silent disagreement between voting and training answer semantics.
    for i, source in enumerate(data.non_tensor_batch["source"]):
        if source == "rzero" and data.non_tensor_batch["solver_vote_valid"][i]:
            expected = equivalent(data.non_tensor_batch["solver_vote_answer"][i], data.non_tensor_batch["ground_truth"][i])
            if bool(matches[i]) != expected:
                raise ValueError("Voting and reward answer equivalence disagree")
    data.batch["token_level_scores"] = reward_tensor
    data.batch["token_level_rewards"] = reward_tensor
    advantages, returns = compute_grpo_outcome_advantage(
        reward_tensor, data.batch["response_mask"], data.non_tensor_batch["uid"])
    data.batch["advantages"], data.batch["returns"] = advantages, returns
    routing_stats = apply_solver_negative_only(data, reward_metrics)
    result, selected_stats, selected = select_update_rows(data, matches, seed)
    stats.update(selected_stats)
    # A few complete groups can be inspected later without rerunning inference.
    audit = []
    rzero_groups = [rows for rows in grouped_rows(data).values()
                    if data.non_tensor_batch["source"][rows[0]] == "rzero"]
    audit_groups = rzero_groups[:2]
    for reason in ("tie", "singleton", "no_answer"):
        example = next((rows for rows in rzero_groups if data.non_tensor_batch["solver_vote_reason"][rows[0]] == reason), None)
        if example is not None and example not in audit_groups:
            audit_groups.append(example)
    selected_set = set(selected)
    for rows in audit_groups:
        for i in rows:
            audit.append({
                "uid": str(data.non_tensor_batch["uid"][i]),
                "prompt": tokenizer.decode(data.batch["prompts"][i], skip_special_tokens=True)
                if "prompts" in data.batch else None,
                "old_label": str(data.non_tensor_batch["solver_static_label"][i]),
                "label": str(data.non_tensor_batch["ground_truth"][i]),
                "vote_reason": str(data.non_tensor_batch["solver_vote_reason"][i]),
                "answer": data.non_tensor_batch["solver_vote_answer"][i],
                "selected": i in selected_set, "match": bool(matches[i]),
                "raw_advantage": float(returns[i, 0]),
                "negative_eligible": bool(data.batch["solver_negative_token_mask"][i]),
                "response": texts[i],
            })
    metrics = {f"solver_dynamic/{key}": value for key, value in stats.items()}
    metrics.update({f"full_group/{key}": value for key, value in routing_stats.items()})
    # Report original reward metrics for selected rows, matching update-batch scope.
    selected_rewards = {}
    for key, values in reward_metrics.items():
        if len(values) == len(data):
            selected_rewards[key] = [values[i] for i in selected]
        else:
            # The existing manager emits math-only accuracy/format arrays and
            # Terra-only diagnostics. These do NOT have full-batch row indices.
            source = "rzero" if key in {"accuracy", "format"} else "terra"
            source_rows = np.flatnonzero(data.non_tensor_batch["source"] == source)
            if len(values) != len(source_rows):
                raise ValueError(f"Unexpected sparse reward metric alignment: {key}")
            by_row = dict(zip(source_rows, values))
            selected_rewards[key] = [by_row[i] for i in selected if i in by_row]
    # mixed_reward's diagnostic counts are repeated constants over the full
    # generation batch. Recompute them for update rows (Terra remains ~10%).
    if "actual_replay_ratio" in selected_rewards:
        sources = result.non_tensor_batch["source"]
        overall = np.asarray(selected_rewards["overall"])
        diagnostics = {}
        for source in ("rzero", "terra"):
            in_source = sources == source
            diagnostics[f"{source}_count"] = int(in_source.sum())
            diagnostics[f"{source}_reward_mean"] = float(overall[in_source].mean()) if in_source.any() else 0.
        diagnostics["actual_replay_ratio"] = diagnostics["terra_count"] / len(result)
        selected_rewards.update({key: [value] * len(result) for key, value in diagnostics.items()})
    return result, metrics, selected_rewards, audit
