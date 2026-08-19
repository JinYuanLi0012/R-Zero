"""Evaluate one candidate shard without deleting its input."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from qwen35.rzero.generate_candidates import atomic_json
from qwen35.rzero.prompts import solver_messages
from qwen35.rzero.rewards.common import majority_vote


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=9)
    parser.add_argument("--seed", type=int, required=True)
    args = parser.parse_args()

    from mathruler.grader import extract_boxed_content, grade_answer
    from transformers import AutoTokenizer
    from vllm import LLM, SamplingParams

    source = json.loads(args.input.read_text(encoding="utf-8"))
    valid = [item for item in source if item.get("score") == 0]
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    model = LLM(
        model=args.model,
        tokenizer=args.model,
        gpu_memory_utilization=0.85,
        seed=args.seed,
        language_model_only=True,
    )
    sampling = SamplingParams(
        max_tokens=4096,
        temperature=1.0,
        top_p=1.0,
        top_k=40,
        n=args.samples,
        stop_token_ids=[tokenizer.eos_token_id],
    )
    prompts = [
        tokenizer.apply_chat_template(solver_messages(item["question"]), tokenize=False, add_generation_prompt=True)
        for item in valid
    ]
    responses = model.generate(prompts, sampling_params=sampling, use_tqdm=True) if prompts else []
    results = []
    for source_item, response in zip(valid, responses):
        answers = []
        for output in response.outputs:
            # Preserve released MathRuler semantics: an output without a box is
            # the literal sentinel "None" and remains one of the fixed m votes.
            answers.append(extract_boxed_content(output.text))
        majority, count, extracted = majority_vote(answers, grade_answer)
        if not extracted:
            continue
        question = source_item["question"]
        if "证明" in question or "box" in question.lower() or "text" in majority.lower():
            continue
        results.append(
            {
                "question": question,
                "answer": majority,
                # MathRuler returns the truthy sentinel "None" for an unboxed
                # output, so released evaluation retains all m=9 votes here.
                # Curation later rejects a majority answer equal to "None".
                "score": count / len(extracted),
                "results": extracted,
            }
        )
    atomic_json(args.output, results)


if __name__ == "__main__":
    main()
