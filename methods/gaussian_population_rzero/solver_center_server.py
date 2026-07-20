#!/usr/bin/env python3
"""One unperturbed central Solver replica for standard R-Zero feedback."""

from __future__ import annotations

import argparse
import json
import os
import threading
from pathlib import Path
from typing import Any

os.environ["VLLM_USE_V1"] = "0"

import vllm
from flask import Flask, jsonify, request
from transformers import AutoTokenizer

from grading import answers_equivalent, extract_answer
from reward_math import majority_rate


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--samples", type=int, default=10)
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.8)
    parser.add_argument("--tensor-parallel-size", type=int, default=1)
    return parser.parse_args()


ARGS = parse_args()
if ARGS.tensor_parallel_size != 1:
    raise ValueError("central Solver feedback currently requires tensor_parallel_size=1")
if ARGS.samples < 2:
    raise ValueError("--samples must be at least 2")
if ARGS.batch_size < 1:
    raise ValueError("--batch-size must be at least 1")

TOKENIZER = AutoTokenizer.from_pretrained(ARGS.model_path)
LLM = vllm.LLM(
    model=ARGS.model_path,
    tokenizer=ARGS.model_path,
    tensor_parallel_size=1,
    gpu_memory_utilization=ARGS.gpu_memory_utilization,
    enable_prefix_caching=False,
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
            "feedback_mode": "central",
            "samples": ARGS.samples,
            "batch_size": ARGS.batch_size,
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
    sampling = vllm.SamplingParams(
        max_tokens=ARGS.max_tokens,
        temperature=1.0,
        top_p=1.0,
        top_k=40,
        n=ARGS.samples,
        stop_token_ids=[TOKENIZER.eos_token_id],
    )
    with MODEL_LOCK:
        outputs = []
        for start in range(0, len(prompts), ARGS.batch_size):
            outputs.extend(
                LLM.generate(
                    prompts[start : start + ARGS.batch_size],
                    sampling_params=sampling,
                    use_tqdm=True,
                )
            )
    if len(outputs) != len(valid):
        raise RuntimeError("central Solver returned an unexpected number of questions")
    result = []
    for record, output in zip(valid, outputs):
        answers = [extract_answer(candidate.text) for candidate in output.outputs]
        result.append(
            {
                "question_index": int(record["question_index"]),
                "num_samples": len(output.outputs),
                "majority_rate": majority_rate(answers, ARGS.samples, answers_equivalent),
            }
        )
    output_path = path.with_name(path.stem + "_results.json")
    _atomic_json(output_path, result)
    return jsonify({"status": "ok", "output": str(output_path), "feedback_mode": "central"})


if __name__ == "__main__":
    APP.run(host="127.0.0.1", port=ARGS.port, threaded=True)
