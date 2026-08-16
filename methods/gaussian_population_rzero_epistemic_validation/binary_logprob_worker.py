#!/usr/bin/env python3
"""One-GPU worker for analysis generation and binary candidate scoring."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

os.environ.setdefault("VLLM_USE_V1", "0")

from binary_logprob_common import (  # noqa: E402
    EXPERIMENT_VERSION, INVALID_CANDIDATE, VALID_CANDIDATE, VARIANTS,
    build_prompt, candidate_logprob, paired_probability,
)
from common import atomic_json, read_jsonl  # noqa: E402


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--shard-index", type=int, required=True)
    parser.add_argument("--num-shards", type=int, required=True)
    parser.add_argument("--max-analysis-tokens", type=int, default=1024)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--score-batch-size", type=int, default=1)
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.7)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def completed(path: Path, model: str, variant: str, max_analysis_tokens: int) -> bool:
    if not path.is_file():
        return False
    try:
        artifact = json.loads(path.read_text(encoding="utf-8"))
        return (
            artifact.get("status") == "success"
            and artifact.get("model") == model
            and artifact.get("variant") == variant
            and artifact.get("experiment_version") == EXPERIMENT_VERSION
            and artifact.get("max_analysis_tokens") == max_analysis_tokens
        )
    except (OSError, json.JSONDecodeError):
        return False


def generate_analyses(llm, vllm_module, prompts: list[str], args: argparse.Namespace):
    params = vllm_module.SamplingParams(
        max_tokens=args.max_analysis_tokens, temperature=0.0, top_p=1.0, n=1,
        seed=args.seed, stop=["\nVerdict:", "Verdict:"], include_stop_str_in_output=False,
    )
    outputs = llm.generate(prompts, sampling_params=params, use_tqdm=True)
    if len(outputs) != len(prompts):
        raise RuntimeError("vLLM returned an unexpected analysis output count")
    return outputs


def score_candidates(
    llm, vllm_module, tokenizer, contexts: list[str], score_batch_size: int = 1,
):
    valid_ids = tokenizer.encode(VALID_CANDIDATE, add_special_tokens=False)
    invalid_ids = tokenizer.encode(INVALID_CANDIDATE, add_special_tokens=False)
    if not valid_ids or not invalid_ids:
        raise RuntimeError("a verdict candidate tokenized to an empty sequence")
    params = vllm_module.SamplingParams(
        max_tokens=1, temperature=0.0, top_p=1.0, prompt_logprobs=1,
    )
    scores = []
    for batch_start in range(0, len(contexts), score_batch_size):
        for context in contexts[batch_start : batch_start + score_batch_size]:
            context_ids = tokenizer.encode(context, add_special_tokens=True)
            candidate_scores = []
            for candidate_ids in (valid_ids, invalid_ids):
                # Score candidates in separate engine calls. For long contexts,
                # prompt_logprobs materializes a full-sequence vocabulary tensor;
                # batching even these two candidates can exceed an 80 GB GPU.
                outputs = llm.generate(
                    prompts=None, prompt_token_ids=[context_ids + candidate_ids],
                    sampling_params=params, use_tqdm=True,
                )
                if len(outputs) != 1:
                    raise RuntimeError("vLLM returned an unexpected scoring output count")
                candidate_scores.append(
                    candidate_logprob(outputs[0], len(context_ids), candidate_ids)
                )
            valid_lp, invalid_lp = candidate_scores
            valid_score = paired_probability(valid_lp, invalid_lp)
            scores.append(
                {
                    "valid_logprob": valid_lp, "invalid_logprob": invalid_lp,
                    "logprob_margin_valid_minus_invalid": valid_lp - invalid_lp,
                    "valid_score": valid_score,
                    "verdict": "VALID" if valid_lp > invalid_lp else "INVALID",
                    "valid_candidate_token_ids": valid_ids,
                    "invalid_candidate_token_ids": invalid_ids,
                    "context_token_count": len(context_ids),
                }
            )
    return scores


def main() -> None:
    args = arguments()
    if args.num_shards < 1 or not 0 <= args.shard_index < args.num_shards:
        raise ValueError("invalid shard assignment")
    if args.batch_size < 1 or args.score_batch_size < 1 or args.max_analysis_tokens < 1:
        raise ValueError("batch sizes and max analysis tokens must be positive")
    all_items = read_jsonl(args.input)
    if any(set(item) != {"opaque_binary_judge_id", "question"} for item in all_items):
        raise ValueError("worker input is not blind")
    items = [item for index, item in enumerate(all_items) if index % args.num_shards == args.shard_index]
    work = []
    for variant in VARIANTS:
        variant_dir = args.output_dir / variant
        for item in items:
            path = variant_dir / f"{item['opaque_binary_judge_id']}.json"
            if not (
                args.resume
                and completed(path, args.model, variant, args.max_analysis_tokens)
            ):
                work.append((variant, item, path))
    if not work:
        return

    import vllm
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(args.model)
    llm = vllm.LLM(
        model=args.model, tokenizer=args.model, tensor_parallel_size=1,
        # vLLM 0.9.1 V0 can assert inside the sampler when prompt_logprobs
        # and automatic prefix caching are used together. Candidate scoring
        # below requires prompt_logprobs, so keep the cache disabled.
        gpu_memory_utilization=args.gpu_memory_utilization, enable_prefix_caching=False,
    )
    for variant in VARIANTS:
        pending = [(item, path) for work_variant, item, path in work if work_variant == variant]
        for start in range(0, len(pending), args.batch_size):
            batch = pending[start : start + args.batch_size]
            prompts = [build_prompt(item["question"], variant) for item, _ in batch]
            generation_outputs = generate_analyses(llm, vllm, prompts, args)
            analyses = [output.outputs[0].text for output in generation_outputs]
            contexts = [f"{prompt}{analysis}\nVerdict:" for prompt, analysis in zip(prompts, analyses)]
            scores = score_candidates(
                llm, vllm, tokenizer, contexts, score_batch_size=args.score_batch_size,
            )
            for (item, path), analysis, generated, score in zip(
                batch, analyses, generation_outputs, scores
            ):
                completion = generated.outputs[0]
                atomic_json(
                    path,
                    {
                        "status": "success", "experiment_version": EXPERIMENT_VERSION,
                        "opaque_binary_judge_id": item["opaque_binary_judge_id"],
                        "variant": variant, "model": args.model,
                        "analysis": analysis, "analysis_finish_reason": completion.finish_reason,
                        "analysis_stop_reason": completion.stop_reason,
                        "analysis_token_count": len(completion.token_ids),
                        "analysis_truncated": completion.finish_reason == "length",
                        "temperature": 0.0, "top_p": 1.0,
                        "max_analysis_tokens": args.max_analysis_tokens,
                        **score,
                    },
                )


if __name__ == "__main__":
    main()
