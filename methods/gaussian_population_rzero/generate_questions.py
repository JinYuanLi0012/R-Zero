#!/usr/bin/env python3
"""Generate one exact share of B from logical Questioner experts."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import regex as re
import vllm
from transformers import AutoTokenizer

from population import (
    GaussianPopulation,
    allocate_quotas,
    assign_experts,
    get_vllm_model,
    make_expert_specs,
)


def extract_boxed(text: str) -> list[str]:
    results, cursor = [], 0
    prefix = r"\boxed{"
    while True:
        start = text.find(prefix, cursor)
        if start < 0:
            return results
        position, depth = start + len(prefix), 1
        while position < len(text) and depth:
            if text[position] == "{":
                depth += 1
            elif text[position] == "}":
                depth -= 1
            position += 1
        if depth == 0:
            results.append(text[start + len(prefix) : position - 1])
        cursor = position


def question_prompt(tokenizer) -> str:
    chat = [
        {
            "role": "system",
            "content": (
                "You are an expert competition-math problem setter.\n"
                "FIRST, in your private scratch-pad, think step-by-step to design a brand-new, non-trivial problem. "
                "The problem could come from any field of mathematics, including but not limited to algebra, geometry, "
                "number theory, combinatorics, prealgebra, probability, statistics, and calculus. "
                "Aim for a difficulty such that fewer than 30 % of advanced high-school students could solve it. "
                "Avoid re-using textbook clichés or famous contest problems.\n"
                "THEN, without revealing any of your private thoughts, output exactly these two blocks:\n\n"
                "<question>\n{The full problem statement}\n</question>\n\n\\boxed{final_answer}\n\n"
                "Do NOT output anything else—no explanations, no extra markup."
            ),
        },
        {
            "role": "user",
            "content": "Generate one new, challenging reasoning question now. Remember to format the output exactly as instructed.",
        },
    ]
    if tokenizer.chat_template:
        return tokenizer.apply_chat_template(
            chat, tokenize=False, add_generation_prompt=True, add_special_tokens=True
        )
    return f"system: {chat[0]['content']}\nuser: {chat[1]['content']}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--round-index", type=int, required=True)
    parser.add_argument("--population-size", type=int, required=True)
    parser.add_argument("--sigma", type=float, required=True)
    parser.add_argument("--global-seed", type=int, required=True)
    parser.add_argument("--total-budget", type=int, required=True)
    parser.add_argument("--worker-index", type=int, required=True)
    parser.add_argument("--num-workers", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.8)
    parser.add_argument("--tensor-parallel-size", type=int, default=1)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.tensor_parallel_size != 1:
        raise ValueError("Gaussian Population R-Zero currently requires TP=1")
    quotas = allocate_quotas(args.total_budget, args.population_size)
    assigned = assign_experts(args.population_size, args.worker_index, args.num_workers)
    specs = make_expert_specs(
        role="questioner",
        round_index=args.round_index,
        population_size=args.population_size,
        sigma=args.sigma,
        global_seed=args.global_seed,
    )

    tokenizer = AutoTokenizer.from_pretrained(args.model)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    llm = vllm.LLM(
        model=args.model,
        tokenizer=args.model,
        tensor_parallel_size=1,
        gpu_memory_utilization=args.gpu_memory_utilization,
        enable_prefix_caching=False,
    )
    population = GaussianPopulation(get_vllm_model(llm))
    prompt = question_prompt(tokenizer)
    records = []
    expert_counts: dict[str, int] = {}
    try:
        for expert_index in assigned:
            spec, quota = specs[expert_index], quotas[expert_index]
            population.apply(spec)
            sampling = vllm.SamplingParams(
                max_tokens=args.max_tokens,
                temperature=1.0,
                top_p=0.95,
                n=1,
                seed=spec.expert_seed % 2_147_483_647,
                stop_token_ids=[tokenizer.eos_token_id],
            )
            completions = llm.generate([prompt] * quota, sampling_params=sampling, use_tqdm=True)
            if len(completions) != quota:
                raise RuntimeError(f"expert {expert_index} generated {len(completions)} != {quota}")
            for completion in completions:
                response = completion.outputs[0].text
                questions = re.findall(r"<question>(.*?)</question>", response, re.DOTALL)
                answers = extract_boxed(response)
                valid = bool(questions and answers)
                records.append(
                    {
                        "question": questions[-1].strip() if valid else response,
                        "answer": answers[-1].strip() if valid else "",
                        "score": 0 if valid else -1,
                        "source_role": "questioner",
                        "source_round": args.round_index,
                        "source_expert_index": expert_index,
                        "source_expert_seed": spec.expert_seed,
                        "source_sigma": spec.sigma,
                    }
                )
            expert_counts[str(expert_index)] = len(completions)
    finally:
        population.restore()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    args.manifest.write_text(
        json.dumps(
            {
                "worker_index": args.worker_index,
                "num_workers": args.num_workers,
                "assigned_experts": assigned,
                "expert_counts": expert_counts,
                "generated_count": len(records),
                "total_budget": args.total_budget,
                "population_size": args.population_size,
                "sigma": args.sigma,
                "global_seed": args.global_seed,
                "tensor_parallel_size": 1,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
