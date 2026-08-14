#!/usr/bin/env python3
"""Generate raw completions for a fixed subset of Gaussian Solver experts."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

os.environ["VLLM_USE_V1"] = "0"

import pyarrow as pa
import pyarrow.parquet as pq
import vllm
from transformers import AutoTokenizer

HERE = Path(__file__).resolve().parent
GAUSSIAN_METHOD = HERE.parent / "gaussian_population_rzero"
sys.path.insert(0, str(GAUSSIAN_METHOD))

from grading import extract_answer  # noqa: E402
from population import GaussianPopulation, get_vllm_model, make_expert_specs  # noqa: E402

from common import read_jsonl, sigma_key  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--round-index", type=int, required=True)
    parser.add_argument("--worker-index", type=int, required=True)
    parser.add_argument("--expert-indices", required=True)
    parser.add_argument("--sigmas", required=True)
    parser.add_argument("--population-size", type=int, required=True)
    parser.add_argument("--global-seed", type=int, required=True)
    parser.add_argument("--samples", type=int, required=True)
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--top-p", type=float, default=1.0)
    parser.add_argument("--top-k", type=int, default=40)
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.8)
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def render_prompt(tokenizer: AutoTokenizer, question: str) -> str:
    messages = [
        {"role": "system", "content": "Please reason step by step, and put your final answer within \\boxed{}."},
        {"role": "user", "content": question},
    ]
    if tokenizer.chat_template:
        return tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True, add_special_tokens=True
        )
    return f"system: {messages[0]['content']}\nuser: {question}"


def atomic_parquet(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.tmp-{os.getpid()}")
    pq.write_table(pa.Table.from_pylist(rows), temporary, compression="zstd")
    os.replace(temporary, path)


def main() -> None:
    args = parse_args()
    if args.samples < 1 or args.batch_size < 1:
        raise ValueError("samples and batch size must be positive")
    expert_indices = [int(value) for value in args.expert_indices.split(",") if value]
    sigmas = [float(value) for value in args.sigmas.split(",") if value]
    questions = read_jsonl(args.input)
    if not questions or not expert_indices or not sigmas:
        raise ValueError("input questions, expert indices, and sigmas must be non-empty")

    tokenizer = AutoTokenizer.from_pretrained(args.model)
    llm = vllm.LLM(
        model=args.model,
        tokenizer=args.model,
        tensor_parallel_size=1,
        gpu_memory_utilization=args.gpu_memory_utilization,
        enable_prefix_caching=False,
    )
    population = GaussianPopulation(get_vllm_model(llm))
    prompts = [render_prompt(tokenizer, str(row["question"])) for row in questions]

    try:
        for sigma in sigmas:
            specs = make_expert_specs(
                role="solver",
                round_index=args.round_index,
                population_size=args.population_size,
                sigma=sigma,
                global_seed=args.global_seed,
            )
            for expert_index in expert_indices:
                output_path = args.output_dir / f"sigma_{sigma_key(sigma)}" / f"expert_{expert_index}.parquet"
                if args.resume and output_path.is_file():
                    expected = len(questions) * args.samples
                    if pq.read_metadata(output_path).num_rows == expected:
                        continue
                spec = specs[expert_index]
                population.apply(spec)
                records: list[dict] = []
                sampling = vllm.SamplingParams(
                    max_tokens=args.max_tokens,
                    temperature=args.temperature,
                    top_p=args.top_p,
                    top_k=args.top_k,
                    n=args.samples,
                    seed=spec.expert_seed % 2_147_483_647,
                    stop_token_ids=[tokenizer.eos_token_id],
                )
                outputs = []
                for start in range(0, len(prompts), args.batch_size):
                    outputs.extend(
                        llm.generate(
                            prompts[start : start + args.batch_size],
                            sampling_params=sampling,
                            use_tqdm=True,
                        )
                    )
                if len(outputs) != len(questions):
                    raise RuntimeError("vLLM returned an unexpected number of question outputs")
                for question, output in zip(questions, outputs):
                    if len(output.outputs) != args.samples:
                        raise RuntimeError("vLLM returned an unexpected number of samples")
                    for sample_index, candidate in enumerate(output.outputs):
                        answer = extract_answer(candidate.text)
                        records.append(
                            {
                                "question_id": question["question_id"],
                                "round": int(question["round"]),
                                "sigma": float(sigma),
                                "expert_index": expert_index,
                                "expert_seed": int(spec.expert_seed),
                                "sample_index": sample_index,
                                "sampling_seed": int(spec.expert_seed % 2_147_483_647),
                                "raw_text": candidate.text,
                                "extracted_answer": answer,
                                "valid": bool(answer),
                                "historical_answer": question.get("historical_answer"),
                            }
                        )
                atomic_parquet(output_path, records)
    finally:
        population.restore()


if __name__ == "__main__":
    main()
