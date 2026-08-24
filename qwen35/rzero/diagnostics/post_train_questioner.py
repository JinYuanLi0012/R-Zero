"""Generate raw Questioner candidates from a trained export with thinking off."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from qwen35.rzero.diagnostics.base_questioner import build_record, summarize, validate_rendered_prompt
from qwen35.rzero.generate_candidates import atomic_json
from qwen35.rzero.prompts import QUESTIONER_MESSAGES


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=64)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--top-p", type=float, default=0.95)
    parser.add_argument("--max-tokens", type=int, default=4096)
    args = parser.parse_args()

    from transformers import AutoConfig, AutoTokenizer
    from vllm import LLM, SamplingParams

    config = AutoConfig.from_pretrained(args.model)
    if config.model_type != "qwen3_5":
        raise RuntimeError(f"expected qwen3_5 export, found {config.model_type!r}")
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    prompt = tokenizer.apply_chat_template(
        QUESTIONER_MESSAGES,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )
    validate_rendered_prompt(prompt, False)
    model = LLM(model=str(args.model), tokenizer=str(args.model), seed=args.seed, language_model_only=True)
    sampling = SamplingParams(
        max_tokens=args.max_tokens,
        temperature=args.temperature,
        top_p=args.top_p,
        n=1,
        stop_token_ids=[tokenizer.eos_token_id],
    )
    completions = model.generate([prompt] * args.samples, sampling_params=sampling, use_tqdm=True)
    if len(completions) != args.samples:
        raise RuntimeError(f"generated {len(completions)} rows, expected {args.samples}")
    records = [
        build_record(index, completion.outputs[0], args.max_tokens, thinking_prefilled_closed=True)
        for index, completion in enumerate(completions)
    ]
    provenance = {
        "model_path": str(args.model),
        "model_type": config.model_type,
        "model_state": "questioner_after_one_grpo_step",
        "prompt_variant": "released_rzero_thinking_off",
        "enable_thinking_override": False,
        "thinking_prefilled_closed": True,
        "samples": args.samples,
        "seed": args.seed,
        "temperature": args.temperature,
        "top_p": args.top_p,
        "n": 1,
        "max_tokens": args.max_tokens,
        "stop_token_ids": [tokenizer.eos_token_id],
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "rendered_prompt": prompt,
        "questioner_messages": QUESTIONER_MESSAGES,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = args.output_dir / "qwen35_questioner_step1_thinking_off_raw_64.json"
    summary_path = args.output_dir / "qwen35_questioner_step1_thinking_off_summary.json"
    atomic_json(raw_path, records)
    atomic_json(summary_path, summarize(records, provenance))
    print(f"raw_output={raw_path}")
    print(f"summary_output={summary_path}")


if __name__ == "__main__":
    main()
