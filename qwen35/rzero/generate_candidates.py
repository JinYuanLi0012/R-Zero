"""Generate one recoverable 2000-question shard with official vLLM."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from qwen35.rzero.prompts import QUESTIONER_MESSAGES
from qwen35.rzero.rewards.common import parse_questioner_response


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--samples", type=int, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--top-p", type=float, default=0.95)
    parser.add_argument("--max-tokens", type=int, default=4096)
    args = parser.parse_args()

    from transformers import AutoTokenizer
    from vllm import LLM, SamplingParams

    tokenizer = AutoTokenizer.from_pretrained(args.model)
    prompt = tokenizer.apply_chat_template(QUESTIONER_MESSAGES, tokenize=False, add_generation_prompt=True)
    model = LLM(
        model=args.model,
        tokenizer=args.model,
        seed=args.seed,
        language_model_only=True,
    )
    sampling = SamplingParams(
        max_tokens=args.max_tokens,
        temperature=args.temperature,
        top_p=args.top_p,
        n=1,
        stop_token_ids=[tokenizer.eos_token_id],
    )
    completions = model.generate([prompt] * args.samples, sampling_params=sampling)
    results = []
    for completion in completions:
        response = completion.outputs[0].text
        parsed = parse_questioner_response(response)
        results.append(
            {
                "question": parsed["question"] or response,
                "answer": parsed["answer"],
                "score": 0 if parsed["question"] and parsed["answer"] else -1,
            }
        )
    if len(results) != args.samples:
        raise RuntimeError(f"generated {len(results)} rows, expected {args.samples}")
    atomic_json(args.output, results)


if __name__ == "__main__":
    main()
