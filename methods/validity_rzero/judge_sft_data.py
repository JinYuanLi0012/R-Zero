"""Pure-Python SFT preparation; prompt tokens are never supervised."""
import json
from .semantic_judge_offline.run_pair_judge_v3_vllm import parse_response_v3


def read_messages(path):
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    for row in rows:
        messages = row["messages"]
        if [m["role"] for m in messages] != ["system", "user", "assistant"]:
            raise ValueError("Expected exactly system/user/assistant messages")
        if parse_response_v3(messages[-1]["content"])["parsed_label"] is None:
            raise ValueError("Missing or conflicting training target label")
    return rows


def encode_example(tokenizer, row, max_length):
    messages = row["messages"]
    # Use exactly the same generation prefix in training and evaluation. Do not
    # render a full chat separately: its assistant separator may differ.
    prompt = tokenizer.apply_chat_template(messages[:-1], tokenize=False, add_generation_prompt=True)
    prompt_ids = tokenizer.encode(prompt, add_special_tokens=False)
    target = messages[-1]["content"]
    target_ids = tokenizer.encode(target, add_special_tokens=False) + [tokenizer.eos_token_id]
    ids = prompt_ids + target_ids
    if len(ids) > max_length:
        raise ValueError(f"Example length {len(ids)} exceeds max_length={max_length}; refusing truncation")
    if prompt_ids[0] != tokenizer.bos_token_id or prompt_ids.count(tokenizer.bos_token_id) != 1:
        raise ValueError("Expected exactly one initial BOS")
    return {"input_ids": ids, "labels": [-100] * len(prompt_ids) + target_ids,
            "prompt_ids": prompt_ids, "prompt": prompt, "target": target,
            "expected_label": parse_response_v3(target)["parsed_label"]}


def metrics(records):
    n = len(records)
    result = {"n": n, "correct": sum(r["prediction"] == r["expected_label"] for r in records),
              "parse_ok": sum(r["prediction"] is not None for r in records),
              "length_stops": sum(r["length_stop"] for r in records)}
    result["accuracy"] = result["correct"] / n
    result["parse_rate"] = result["parse_ok"] / n
    recalls = []
    for label in ("SAME_TYPE", "DIFFERENT"):
        group = [r for r in records if r["expected_label"] == label]
        correct = sum(r["prediction"] == label for r in group)
        result[label] = {"n": len(group), "correct": correct, "recall": correct / len(group) if group else None}
        if group:
            recalls.append(correct / len(group))
    result["balanced_accuracy"] = sum(recalls) / len(recalls)
    negatives = [r for r in records if r["expected_label"] == "DIFFERENT"]
    result["false_same_rate"] = sum(r["prediction"] == "SAME_TYPE" for r in negatives) / len(negatives) if negatives else None
    return result
