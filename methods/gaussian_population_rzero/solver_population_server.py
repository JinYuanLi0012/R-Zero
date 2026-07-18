#!/usr/bin/env python3
"""One physical TP=1 vLLM engine serving several logical Solver experts."""

from __future__ import annotations

import argparse
import json
import os
import threading
from pathlib import Path
from typing import Any

import torch
import vllm
from flask import Flask, jsonify, request
from transformers import AutoTokenizer

from grading import answers_equivalent, extract_answer
from population import GaussianPopulation, get_vllm_model, make_expert_specs
from reward_math import majority_rate


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--round-index", type=int, required=True)
    parser.add_argument("--population-size", type=int, required=True)
    parser.add_argument("--expert-indices", required=True)
    parser.add_argument("--sigma", type=float, required=True)
    parser.add_argument("--global-seed", type=int, required=True)
    parser.add_argument("--samples", type=int, default=10)
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.8)
    parser.add_argument("--tensor-parallel-size", type=int, default=1)
    return parser.parse_args()


ARGS = parse_args()
if ARGS.tensor_parallel_size != 1:
    raise ValueError("Gaussian Population R-Zero currently requires tensor_parallel_size=1")
if ARGS.samples < 2:
    raise ValueError("--samples must be at least 2")

EXPERT_INDICES = [int(value) for value in ARGS.expert_indices.split(",") if value.strip()]
if not EXPERT_INDICES:
    raise ValueError("this physical service was assigned no experts")
if any(not 0 <= index < ARGS.population_size for index in EXPERT_INDICES):
    raise ValueError("expert index outside population")

TOKENIZER = AutoTokenizer.from_pretrained(ARGS.model_path)
LLM = vllm.LLM(
    model=ARGS.model_path,
    tokenizer=ARGS.model_path,
    tensor_parallel_size=1,
    gpu_memory_utilization=ARGS.gpu_memory_utilization,
    enable_prefix_caching=False,
)
POPULATION = GaussianPopulation(get_vllm_model(LLM))
SPECS = make_expert_specs(
    role="solver",
    round_index=ARGS.round_index,
    population_size=ARGS.population_size,
    sigma=ARGS.sigma,
    global_seed=ARGS.global_seed,
)
MODEL_LOCK = threading.Lock()
APP = Flask(__name__)


def _prompt(question: str) -> str:
    chat = [
        {"role": "system", "content": "Please reason step by step, and put your final answer within \\boxed{}."},
        {"role": "user", "content": question},
    ]
    if TOKENIZER.chat_template:
        return TOKENIZER.apply_chat_template(
            chat, tokenize=False, add_generation_prompt=True, add_special_tokens=True
        )
    return f"system: {chat[0]['content']}\nuser: {question}"


def _atomic_json(path: Path, value: Any) -> None:
    temporary = path.with_name(f"{path.name}.tmp-{os.getpid()}")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


@APP.get("/health")
def health():
    return jsonify(
        {
            "status": "ok",
            "round": ARGS.round_index,
            "experts": EXPERT_INDICES,
            "samples": ARGS.samples,
            "tensor_parallel_size": 1,
        }
    )


@APP.get("/evaluate")
def evaluate():
    path = Path(request.args.get("name", ""))
    if not path.is_file():
        return jsonify({"error": f"request file does not exist: {path}"}), 400
    records = json.loads(path.read_text(encoding="utf-8"))
    valid = [record for record in records if record.get("question") and record.get("answer")]
    prompts = [_prompt(str(record["question"])) for record in valid]
    by_index: dict[int, list[dict[str, Any]]] = {
        int(record["question_index"]): [] for record in valid
    }

    with MODEL_LOCK:
        try:
            for expert_index in EXPERT_INDICES:
                spec = SPECS[expert_index]
                POPULATION.apply(spec)
                sampling = vllm.SamplingParams(
                    max_tokens=ARGS.max_tokens,
                    temperature=1.0,
                    top_p=1.0,
                    top_k=40,
                    n=ARGS.samples,
                    seed=spec.expert_seed % 2_147_483_647,
                    stop_token_ids=[TOKENIZER.eos_token_id],
                )
                outputs = LLM.generate(prompts, sampling_params=sampling, use_tqdm=True)
                if len(outputs) != len(valid):
                    raise RuntimeError("vLLM returned an unexpected number of questions")
                for record, output in zip(valid, outputs):
                    answers = [extract_answer(candidate.text) for candidate in output.outputs]
                    rate = majority_rate(answers, ARGS.samples, answers_equivalent)
                    by_index[int(record["question_index"])].append(
                        {
                            "expert_index": expert_index,
                            "expert_seed": spec.expert_seed,
                            "num_samples": len(output.outputs),
                            "majority_rate": rate,
                        }
                    )
        finally:
            POPULATION.restore()

    result = [
        {"question_index": index, "expert_scores": scores}
        for index, scores in sorted(by_index.items())
    ]
    output_path = path.with_name(path.stem + "_results.json")
    _atomic_json(output_path, result)
    return jsonify({"status": "ok", "output": str(output_path), "experts": EXPERT_INDICES})


if __name__ == "__main__":
    APP.run(host="127.0.0.1", port=ARGS.port, threaded=True)
