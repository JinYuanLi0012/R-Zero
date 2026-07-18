#!/usr/bin/env python3
"""Label one generated shard with the unperturbed central Solver only."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import vllm
from transformers import AutoTokenizer

from grading import answers_equivalent, extract_answer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=9)
    parser.add_argument("--worker-seed", type=int, default=0)
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.85)
    parser.add_argument("--batch-size", type=int, default=0)
    return parser.parse_args()


def prompt(tokenizer, question: str) -> str:
    chat = [
        {"role": "system", "content": "Please reason step by step, and put your final answer within \\boxed{}."},
        {"role": "user", "content": question},
    ]
    if tokenizer.chat_template:
        return tokenizer.apply_chat_template(
            chat, tokenize=False, add_generation_prompt=True, add_special_tokens=True
        )
    return f"system: {chat[0]['content']}\nuser: {question}"


def main() -> None:
    args = parse_args()
    if args.samples != 9:
        raise ValueError("central Solver labeling must use 9 samples to match standard R-Zero")
    records = json.loads(args.input.read_text(encoding="utf-8"))
    valid = [record for record in records if record.get("score") == 0]
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    llm = vllm.LLM(
        model=args.model,
        tokenizer=args.model,
        gpu_memory_utilization=args.gpu_memory_utilization,
        seed=args.worker_seed,
        enable_prefix_caching=False,
    )
    sampling = vllm.SamplingParams(
        max_tokens=args.max_tokens,
        temperature=1.0,
        top_p=1.0,
        top_k=40,
        n=args.samples,
        stop_token_ids=[tokenizer.eos_token_id],
    )
    prompts = [prompt(tokenizer, str(record["question"])) for record in valid]
    if args.batch_size > 0:
        outputs = []
        for start in range(0, len(prompts), args.batch_size):
            outputs.extend(
                llm.generate(prompts[start : start + args.batch_size], sampling_params=sampling, use_tqdm=True)
            )
    else:
        outputs = llm.generate(prompts, sampling_params=sampling, use_tqdm=True)
    if len(outputs) != len(valid):
        raise RuntimeError("central Solver returned an unexpected number of questions")

    evaluated = []
    for record, output in zip(valid, outputs):
        answers = [extract_answer(candidate.text) for candidate in output.outputs]
        if len(answers) != args.samples:
            raise RuntimeError(
                f"central Solver returned {len(answers)} rollouts; expected {args.samples}"
            )
        # Match standard R-Zero labeling: invalid boxed outputs are discarded,
        # and the difficulty score denominator is the number of valid outputs.
        representatives: list[str] = []
        counts: list[int] = []
        for answer in answers:
            if not answer:
                continue
            for index, existing in enumerate(representatives):
                if answers_equivalent(answer, existing):
                    counts[index] += 1
                    break
            else:
                representatives.append(answer)
                counts.append(1)
        if not counts:
            continue
        majority_index = max(range(len(counts)), key=counts.__getitem__)
        majority_answer = representatives[majority_index]
        rate = counts[majority_index] / sum(counts)
        question = str(record["question"])
        if "证明" in question or "box" in question.lower() or "text" in majority_answer.lower():
            continue
        item = dict(record)
        item.update(
            {
                "answer": majority_answer,
                "score": rate,
                "results": answers,
                "labeler_role": "central_solver",
                "labeler_samples": args.samples,
            }
        )
        evaluated.append(item)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evaluated, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
