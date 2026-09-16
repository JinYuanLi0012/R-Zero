"""Read-only single-GPU inference of a saved judge adapter on fixed pairs."""
import argparse
import hashlib
import json
import time
from pathlib import Path
from .judge_sft_data import metrics
from .semantic_judge_offline.run_pair_judge_v3_vllm import parse_response_v3


def pair_messages(pair, system_prompt):
    return [{"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Question A:\n{pair['a']['question']}\n\nQuestion B:\n{pair['b']['question']}"}]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", required=True)
    p.add_argument("--adapter", type=Path, required=True)
    p.add_argument("--system-prompt", type=Path, required=True)
    p.add_argument("--pairs-file", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--batch-size", type=int, default=4)
    p.add_argument("--max-new-tokens", type=int, default=256)
    p.add_argument("--max-length", type=int, default=2048)
    args = p.parse_args()
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM, set_seed
    from peft import PeftModel
    if torch.cuda.device_count() != 1 or args.batch_size < 1:
        p.error("Exactly one GPU and positive batch size required")
    pairs = [json.loads(line) for line in args.pairs_file.read_text().splitlines() if line.strip()]
    if not pairs or len({r["pair_id"] for r in pairs}) != len(pairs):
        raise ValueError("Empty pairs or duplicate IDs")
    if any(r.get("expected_label") not in {"SAME_TYPE", "DIFFERENT"} for r in pairs):
        raise ValueError("Each diagnostic pair needs a preassigned expected_label")
    system = args.system_prompt.read_text()
    tokenizer = AutoTokenizer.from_pretrained(args.adapter)
    prompts = [tokenizer.apply_chat_template(pair_messages(r, system), tokenize=False, add_generation_prompt=True) for r in pairs]
    ids_list = [tokenizer.encode(text, add_special_tokens=False) for text in prompts]
    if any(len(ids)+args.max_new_tokens > args.max_length for ids in ids_list):
        raise ValueError("Prompt+output exceeds max-length; no truncation allowed")
    if any(ids[0] != tokenizer.bos_token_id or ids.count(tokenizer.bos_token_id) != 1 for ids in ids_list):
        raise ValueError("Expected exactly one initial BOS")
    args.output_dir.mkdir(parents=True, exist_ok=False)
    set_seed(42)
    base = AutoModelForCausalLM.from_pretrained(args.model, torch_dtype=torch.bfloat16, attn_implementation="sdpa").to("cuda")
    model = PeftModel.from_pretrained(base, args.adapter, is_trainable=False).eval()
    records = []
    began = time.monotonic()
    for start in range(0, len(pairs), args.batch_size):
        batch = ids_list[start:start+args.batch_size]
        width = max(map(len, batch))
        ids = torch.tensor([[tokenizer.pad_token_id]*(width-len(x))+x for x in batch], device="cuda")
        mask = torch.tensor([[0]*(width-len(x))+[1]*len(x) for x in batch], device="cuda")
        with torch.inference_mode():
            output = model.generate(input_ids=ids, attention_mask=mask, do_sample=False,
                                    temperature=1.0, top_p=1.0, top_k=0, repetition_penalty=1.0,
                                    max_new_tokens=args.max_new_tokens, use_cache=True,
                                    eos_token_id=tokenizer.eos_token_id, pad_token_id=tokenizer.pad_token_id)
        for i in range(len(batch)):
            tokens = output[i, width:].tolist()
            ended = tokenizer.eos_token_id in tokens
            if ended:
                tokens = tokens[:tokens.index(tokenizer.eos_token_id)]
            response = tokenizer.decode(tokens, skip_special_tokens=True)
            records.append({**pairs[start+i], "prompt": prompts[start+i], "response": response,
                            "prediction": parse_response_v3(response)["parsed_label"], "tokens": len(tokens),
                            "length_stop": not ended and len(tokens) >= args.max_new_tokens})
    summary = metrics(records)
    summary.update(seconds=time.monotonic()-began, mean_output_tokens=sum(r["tokens"] for r in records)/len(records))
    summary["categories"] = {c: metrics([r for r in records if r.get("category", "unspecified") == c])
                             for c in sorted({r.get("category", "unspecified") for r in records})}
    def write(name, obj):
        (args.output_dir / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2)+"\n")
    write("results.json", {"metrics": summary, "records": records})
    write("manifest.json", {"model": args.model, "adapter": str(args.adapter),
        "pairs_sha256": hashlib.sha256(args.pairs_file.read_bytes()).hexdigest(),
        "adapter_sha256": hashlib.sha256((args.adapter / "adapter_model.safetensors").read_bytes()).hexdigest(),
        "system_prompt": system, "chat_template": tokenizer.chat_template,
        "decoding": "greedy, EOS stopping, no stop-at-box", "max_new_tokens": args.max_new_tokens,
        "batch_size": args.batch_size, "gpu": torch.cuda.get_device_name(0), "training": False})
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
