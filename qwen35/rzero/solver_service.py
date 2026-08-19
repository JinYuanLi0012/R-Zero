"""Frozen Solver HTTP service used by the Challenger batch reward."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from qwen35.rzero.prompts import solver_messages
from qwen35.rzero.rewards.common import majority_vote


def create_app(model_path: str, samples: int, gpu_memory_utilization: float):
    from flask import Flask, jsonify, request
    from mathruler.grader import extract_boxed_content, grade_answer
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
                # Keep the released truthy "None" sentinel as a real vote;
                # majority_vote still removes explicit empty-box results.
                answers.append(extract_boxed_content(output.text))
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


def publish_service_receipt(path: Path, host: str, port: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps({"host": host, "port": port}) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--port-file", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=10)
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.8)
    args = parser.parse_args()
    app = create_app(args.model, args.samples, args.gpu_memory_utilization)
    from werkzeug.serving import make_server

    host = "127.0.0.1"
    server = make_server(host, args.port, app, threaded=False)
    publish_service_receipt(args.port_file, host, server.server_port)
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
