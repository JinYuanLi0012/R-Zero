"""Frozen Solver HTTP service used by the Challenger batch reward."""

from __future__ import annotations

import argparse
from typing import Any

from qwen35.rzero.prompts import solver_messages
from qwen35.rzero.rewards.common import extract_boxed, majority_vote


def create_app(model_path: str, samples: int, gpu_memory_utilization: float):
    from flask import Flask, jsonify, request
    from mathruler.grader import grade_answer
    from transformers import AutoTokenizer
    from vllm import LLM, SamplingParams

    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = LLM(
        model=model_path,
        tokenizer=model_path,
        gpu_memory_utilization=gpu_memory_utilization,
        language_model_only=True,
    )
    sampling = SamplingParams(
        max_tokens=4096,
        temperature=1.0,
        top_p=1.0,
        top_k=40,
        n=samples,
        stop_token_ids=[tokenizer.eos_token_id],
    )
    app = Flask(__name__)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.post("/score")
    def score():
        payload: dict[str, Any] = request.get_json(force=True)
        items = payload.get("items", [])
        valid_positions = [index for index, item in enumerate(items) if item.get("question") and item.get("answer")]
        prompts = [
            tokenizer.apply_chat_template(
                solver_messages(items[index]["question"]), tokenize=False, add_generation_prompt=True
            )
            for index in valid_positions
        ]
        responses = model.generate(prompts, sampling_params=sampling, use_tqdm=False) if prompts else []
        results: list[dict[str, Any]] = [
            {"question": item.get("question", ""), "answer": item.get("answer", ""), "score": -1.0, "results": []}
            for item in items
        ]
        for position, response in zip(valid_positions, responses):
            answers = []
            for output in response.outputs:
                boxed = extract_boxed(output.text)
                answers.append(boxed[-1] if boxed else "")
            majority, count, valid = majority_vote(answers, grade_answer)
            denominator = len(answers)
            results[position] = {
                "question": items[position]["question"],
                "answer": majority,
                "score": count / denominator if denominator else 0.0,
                "results": valid,
            }
        return jsonify({"results": results})

    return app


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--samples", type=int, default=10)
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.8)
    args = parser.parse_args()
    app = create_app(args.model, args.samples, args.gpu_memory_utilization)
    app.run(host="127.0.0.1", port=args.port, threaded=False)


if __name__ == "__main__":
    main()
