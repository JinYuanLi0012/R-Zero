"""One GPU, same production decoding, three questions per completion."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import atomic_json, atomic_jsonl, parse_three, three_messages


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--shard", type=int, required=True)
    parser.add_argument("--requests", type=int, required=True)
    args = parser.parse_args()
    import vllm
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(args.model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token_id = tokenizer.eos_token_id
    model = vllm.LLM(model=args.model, tokenizer=args.model, seed=args.shard)
    chat = three_messages()
    if tokenizer.chat_template:
        prompt = tokenizer.apply_chat_template(chat, tokenize=False, add_generation_prompt=True,
                                                add_special_tokens=True)
    else:
        prompt = "system: " + chat[0]["content"] + "\nuser: " + chat[1]["content"]
    # Deliberately identical to question_generate/question_generate.py: even the cap stays 4096.
    params = vllm.SamplingParams(max_tokens=4096, temperature=1.0, top_p=0.95, n=1,
                               stop_token_ids=[tokenizer.eos_token_id])
    completions = model.generate([prompt] * args.requests, sampling_params=params)
    if len(completions) != args.requests:
        raise RuntimeError("vLLM returned an unexpected request count")
    raw, candidates = [], []
    for index, output in enumerate(completions):
        if len(output.outputs) != 1:
            raise RuntimeError("expected one completion per request")
        completion = output.outputs[0]
        rows, diagnostics = parse_three(completion.text)
        request_id = f"shard{args.shard}-request{index}"
        for row in rows:
            row.update(request_id=request_id, request_index=index, shard=args.shard,
                       sample_id=f"{request_id}-q{row['question_position']}")
        candidates.extend(rows)
        raw.append({"request_id": request_id, "request_index": index, "shard": args.shard,
                    "raw_completion": completion.text, "finish_reason": completion.finish_reason,
                    "completion_token_count": len(completion.token_ids), **diagnostics})
    folder = args.output_dir / "generation"
    atomic_json(folder / f"shard_{args.shard}_prompt.json", {"messages": chat, "rendered_prompt": prompt})
    atomic_jsonl(folder / f"shard_{args.shard}_raw.jsonl", raw)
    atomic_json(folder / f"shard_{args.shard}_candidates.json", candidates)
    print(json.dumps({"shard": args.shard, "requests": len(raw), "parsed_questions": len(candidates)}))


if __name__ == "__main__":
    main()
