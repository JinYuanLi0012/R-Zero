"""Single-GPU raw-output probe; no training, reward updates, API, or retries."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import random

from .semantic_judge_offline.semantic_pair_prompt_formal import build_prompt, PROMPT_VERSION
from .semantic_judge_offline.run_pair_judge_v3_vllm import parse_response_v3, sampling_options


def select_pairs(rows, questions, seed):
    """Sample unique question texts from train only; no semantic gold labels."""
    if questions < 2 or questions % 2:
        raise ValueError("--questions must be an even integer >= 2")
    unique = {}
    for index, row in enumerate(rows):
        if row.get("split", "train") != "train":
            raise ValueError("Input contains a non-train row")
        question = row.get("question")
        if isinstance(question, str) and question.strip():
            unique.setdefault(question.strip(), {"id": row.get("id", index),
                "question": question.strip(), "terra_validity": row.get("terra_validity")})
    if len(unique) < questions:
        raise ValueError(f"Need {questions} unique questions; found {len(unique)}")
    selected = random.Random(seed).sample(list(unique.values()), questions)
    return [{"pair_id": i // 2, "a": selected[i], "b": selected[i + 1],
             "prompt": build_prompt(selected[i]["question"], selected[i + 1]["question"])}
            for i in range(0, questions, 2)]


def options(condition, max_tokens, seed):
    result = sampling_options(max_tokens, seed)
    if condition == "no-box-stop":
        result["stop"] = []  # EOS and length limits remain active.
    elif condition != "current":
        raise ValueError(condition)
    return result


def summarize(records):
    summary = {}
    for condition in dict.fromkeys(row["condition"] for row in records):
        group = [row for row in records if row["condition"] == condition]
        summary[condition] = {
            "responses": len(group),
            "parse_failure_rate": sum(r["parse"]["format_status"] != "ok" for r in group) / len(group),
            "length_stop_rate": sum(r["finish_reason"] == "length" for r in group) / len(group),
            "mean_output_tokens": sum(r["output_tokens"] for r in group) / len(group),
            "labels": dict(Counter(r["parse"]["predicted_label"] for r in group)),
            "errors": dict(Counter(r["parse"]["format_error_reason"] for r in group if r["parse"]["format_error_reason"])),
        }
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="OctoThinker/OctoThinker-3B-Hybrid-Base")
    parser.add_argument("--dataset", default="jinyuan222/rzero-validity-rl-terra-v1-clean-v1")
    parser.add_argument("--train-parquet", type=Path, help="Optional original Terra train parquet, no HF download")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--questions", type=int, default=20, help="20 questions = 10 disjoint pairs")
    parser.add_argument("--seed", type=int, default=43, help="Question selection seed")
    parser.add_argument("--generation-seed", type=int, default=42)
    parser.add_argument("--max-tokens", type=int, default=1024)
    parser.add_argument("--max-model-len", type=int, default=8192, help="Bound KV cache; never truncate prompts")
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.6)
    parser.add_argument("--conditions", nargs="+", choices=["current", "no-box-stop"], default=["current"])
    args = parser.parse_args()
    if args.questions < 2 or args.questions % 2 or args.max_tokens < 1 or args.batch_size < 1:
        parser.error("Use an even --questions >=2 and positive token/batch limits")
    if not 0 < args.gpu_memory_utilization < 1:
        parser.error("GPU memory utilization must be between 0 and 1")

    import torch
    from datasets import load_dataset
    from transformers import AutoTokenizer
    from vllm import LLM, SamplingParams

    if torch.cuda.device_count() != 1:
        parser.error("Expose exactly one allocated GPU using CUDA_VISIBLE_DEVICES")
    # Refuse any existing directory, preserving old/partial diagnostics.
    args.output_dir.mkdir(parents=True, exist_ok=False)
    if args.train_parquet:
        rows = load_dataset("parquet", data_files={"train": str(args.train_parquet)}, split="train")
    else:
        rows = load_dataset(args.dataset, data_files={"train": "train.jsonl"}, split="train")
    pairs = select_pairs(rows, args.questions, args.seed)
    pair_text = "".join(json.dumps(p, ensure_ascii=False) + "\n" for p in pairs)
    (args.output_dir / "pairs.jsonl").write_text(pair_text, encoding="utf-8")

    # Deliberately no chat-template override: reproduce the online semantic worker.
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    if any(len(tokenizer.encode(p["prompt"])) + args.max_tokens > args.max_model_len for p in pairs):
        raise ValueError("A prompt plus response exceeds --max-model-len; increase it explicitly")
    manifest = {"model": args.model, "dataset": args.dataset if not args.train_parquet else None,
        "train_parquet": str(args.train_parquet) if args.train_parquet else None,
        "split": "train", "dataset_fingerprint": rows._fingerprint,
        "pair_sha256": hashlib.sha256(pair_text.encode()).hexdigest(),
        "prompt_version": PROMPT_VERSION, "selection_seed": args.seed,
        "bos_token": tokenizer.bos_token, "bos_token_id": tokenizer.bos_token_id,
        "eos_token": tokenizer.eos_token, "eos_token_id": tokenizer.eos_token_id,
        "tokenizer_class": type(tokenizer).__name__, "chat_template_used": False,
        "cuda_visible_devices": os.getenv("CUDA_VISIBLE_DEVICES"),
        "gpu_name": torch.cuda.get_device_name(0), "first_attempt_only": True,
        "max_model_len": args.max_model_len,
        "note": "Random Terra train pairs, no semantic gold labels; not a replay of the original training batch.",
        "sampling": {c: options(c, args.max_tokens, args.generation_seed) for c in args.conditions}}
    (args.output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    model = LLM(model=args.model, tokenizer=args.model, dtype="bfloat16", tensor_parallel_size=1,
                max_model_len=args.max_model_len,
                gpu_memory_utilization=args.gpu_memory_utilization, seed=args.generation_seed,
                enable_prefix_caching=True)
    records = []
    with (args.output_dir / "raw_outputs.jsonl").open("w", encoding="utf-8") as raw, \
         (args.output_dir / "report.txt").open("w", encoding="utf-8") as report:
        for condition in dict.fromkeys(args.conditions):
            sampling = SamplingParams(**options(condition, args.max_tokens, args.generation_seed))
            for start in range(0, len(pairs), args.batch_size):
                batch = pairs[start:start + args.batch_size]
                outputs = model.generate([p["prompt"] for p in batch], sampling_params=sampling, use_tqdm=True)
                if len(outputs) != len(batch):
                    raise RuntimeError("Wrong number of generated responses")
                for pair, output in zip(batch, outputs):
                    completion = output.outputs[0]
                    record = {**pair, "condition": condition, "response": completion.text,
                        "response_with_special_tokens": tokenizer.decode(completion.token_ids, skip_special_tokens=False),
                        "prompt_token_ids": list(output.prompt_token_ids),
                        "output_token_ids": list(completion.token_ids),
                        "output_tokens": len(completion.token_ids),
                        "finish_reason": completion.finish_reason, "stop_reason": completion.stop_reason,
                        "parse": parse_response_v3(completion.text)}
                    records.append(record)
                    raw.write(json.dumps(record, ensure_ascii=False) + "\n")
                    raw.flush()
                    report.write(f"\n{'=' * 72}\nPAIR {pair['pair_id']} / {condition}\n"
                        f"PROMPT:\n{pair['prompt']}\n\nRAW OUTPUT:\n{completion.text}\n\n"
                        f"WITH SPECIAL TOKENS:\n{record['response_with_special_tokens']}\n\n"
                        f"TOKENS: {record['output_tokens']} FINISH: {completion.finish_reason} STOP: {completion.stop_reason}\n"
                        f"PARSE: {json.dumps(record['parse'])}\n")
                    report.flush()
    summary = summarize(records)
    (args.output_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"Read full prompts/responses: {args.output_dir / 'report.txt'}")


if __name__ == "__main__":
    main()
