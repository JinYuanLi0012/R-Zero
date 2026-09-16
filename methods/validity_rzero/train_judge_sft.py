"""Single-GPU BF16 LoRA judge SFT. No Ray, quantization, merging or deployment."""
import argparse
import hashlib
import json
import math
import random
import sys
import time
from pathlib import Path

from .judge_sft_data import read_messages, encode_example, metrics
from .semantic_judge_offline.run_pair_judge_v3_vllm import parse_response_v3


def save_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", required=True)
    p.add_argument("--data-dir", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--epochs", type=int, default=3)
    p.add_argument("--batch-size", type=int, default=2)
    p.add_argument("--grad-accum", type=int, default=4)
    p.add_argument("--eval-batch-size", type=int, default=4)
    p.add_argument("--max-length", type=int, default=2048)
    p.add_argument("--max-new-tokens", type=int, default=256)
    p.add_argument("--learning-rate", type=float, default=1e-4)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--wandb-project", default="rzero-semantic-judge-sft")
    p.add_argument("--run-name", default="octo-hybrid-3b-judge-v2-clear-lora")
    args = p.parse_args()
    if min(args.epochs, args.batch_size, args.grad_accum, args.eval_batch_size, args.max_new_tokens) < 1:
        p.error("Positive epoch/batch/token settings required")
    import torch
    import transformers
    import peft
    import wandb
    from transformers import AutoModelForCausalLM, AutoTokenizer, get_linear_schedule_with_warmup, set_seed
    from peft import LoraConfig, get_peft_model

    if torch.cuda.device_count() != 1 or not torch.cuda.is_bf16_supported():
        p.error("Expose exactly one BF16-capable GPU")
    set_seed(args.seed)
    train_path = args.data_dir / "messages.train.jsonl"
    holdout_path = args.data_dir / "messages.holdout.jsonl"
    train_rows, holdout_rows = read_messages(train_path), read_messages(holdout_path)
    if (len(train_rows), len(holdout_rows)) != (160, 40):
        raise ValueError("This small run expects v2_clear 160 train / 40 holdout")
    if {r["messages"][1]["content"] for r in train_rows} & {r["messages"][1]["content"] for r in holdout_rows}:
        raise ValueError("Train/holdout prompt overlap")
    template_path = Path(__file__).parents[1] / "validity_rl" / "octothinker_chat.jinja"
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    tokenizer.chat_template = template_path.read_text()
    if tokenizer.bos_token != "<|begin_of_text|>" or tokenizer.eos_token_id is None:
        raise ValueError("Unexpected Octo tokenizer")
    tokenizer.pad_token = tokenizer.eos_token
    train = [encode_example(tokenizer, r, args.max_length) for r in train_rows]
    holdout = [encode_example(tokenizer, r, args.max_length) for r in holdout_rows]
    if any(len(r["prompt_ids"]) + args.max_new_tokens > args.max_length for r in holdout):
        raise ValueError("Evaluation prompt+generation exceeds max-length")
    if len({r["messages"][0]["content"] for r in train_rows + holdout_rows}) != 1:
        raise ValueError("Expected a single shared system instruction")
    args.output_dir.mkdir(parents=True, exist_ok=False)
    tokenizer.save_pretrained(args.output_dir / "tokenizer")
    (args.output_dir / "system_prompt.txt").write_text(train_rows[0]["messages"][0]["content"])
    manifest = {"args": {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
                "torch": torch.__version__, "transformers": transformers.__version__, "peft": peft.__version__,
                "gpu": torch.cuda.get_device_name(0), "data_version": "v2_clear",
                "data_sha256": {x.name: hashlib.sha256(x.read_bytes()).hexdigest() for x in (train_path, holdout_path)},
                "template": tokenizer.chat_template, "max_train_tokens": max(len(r["input_ids"]) for r in train),
                "max_holdout_tokens": max(len(r["input_ids"]) for r in holdout),
                "loss": "assistant target and EOS only; prompt and padding masked",
                "protocol": "render system+user with add_generation_prompt; append assistant tokens then EOS; no few-shot"}
    save_json(args.output_dir / "manifest.json", manifest)
    # Online is explicit: never silently substitute offline logging.
    run = wandb.init(project=args.wandb_project, name=args.run_name, mode="online", config=manifest,
                     dir=str(args.output_dir))
    try:
        model = AutoModelForCausalLM.from_pretrained(args.model, torch_dtype=torch.bfloat16,
                                                    attn_implementation="sdpa").to("cuda")
        model.config.pad_token_id = tokenizer.pad_token_id
        model.config.use_cache = False

        def evaluate(epoch):
            model.eval()
            records = []
            began = time.monotonic()
            for start in range(0, len(holdout), args.eval_batch_size):
                batch = holdout[start:start + args.eval_batch_size]
                width = max(len(r["prompt_ids"]) for r in batch)
                ids = torch.tensor([[tokenizer.pad_token_id] * (width-len(r["prompt_ids"])) + r["prompt_ids"] for r in batch], device="cuda")
                mask = torch.tensor([[0] * (width-len(r["prompt_ids"])) + [1] * len(r["prompt_ids"]) for r in batch], device="cuda")
                with torch.inference_mode():
                    generated = model.generate(input_ids=ids, attention_mask=mask, do_sample=False,
                                               temperature=1.0, top_p=1.0, top_k=0, repetition_penalty=1.0,
                                               max_new_tokens=args.max_new_tokens, use_cache=True,
                                               eos_token_id=tokenizer.eos_token_id, pad_token_id=tokenizer.pad_token_id)
                for i, row in enumerate(batch):
                    tokens = generated[i, width:].tolist()
                    ended = tokenizer.eos_token_id in tokens
                    if ended:
                        tokens = tokens[:tokens.index(tokenizer.eos_token_id)]
                    response = tokenizer.decode(tokens, skip_special_tokens=True)
                    records.append({"index": start+i, "expected_label": row["expected_label"],
                                    "prediction": parse_response_v3(response)["parsed_label"],
                                    "prompt": row["prompt"], "response": response, "tokens": len(tokens),
                                    "length_stop": not ended and len(tokens) >= args.max_new_tokens})
            result = metrics(records)
            result.update(epoch=epoch, seconds=time.monotonic()-began,
                          mean_output_tokens=sum(r["tokens"] for r in records)/len(records))
            save_json(args.output_dir / f"eval_epoch_{epoch}.json", {"metrics": result, "records": records})
            run.log({"epoch": epoch, **{f"eval/{k}": v for k, v in result.items() if isinstance(v, (int, float))},
                     "eval/same_recall": result["SAME_TYPE"]["recall"], "eval/different_recall": result["DIFFERENT"]["recall"]})
            print(json.dumps(result), flush=True)
            return result

        history = [evaluate(0)]
        model = get_peft_model(model, LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05,
                                               target_modules="all-linear", bias="none", task_type="CAUSAL_LM"))
        model.enable_input_require_grads()
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
        model.print_trainable_parameters()
        optimizer = torch.optim.AdamW((x for x in model.parameters() if x.requires_grad), lr=args.learning_rate, weight_decay=0.01)
        batches = math.ceil(len(train)/args.batch_size)
        updates_per_epoch = math.ceil(batches/args.grad_accum)
        scheduler = get_linear_schedule_with_warmup(optimizer, max(1, math.ceil(0.1*updates_per_epoch*args.epochs)), updates_per_epoch*args.epochs)
        step = 0
        for epoch in range(1, args.epochs+1):
            model.train()
            order = list(range(len(train)))
            random.Random(args.seed+epoch).shuffle(order)
            optimizer.zero_grad(set_to_none=True)
            window_loss = 0.0
            for batch_no, start in enumerate(range(0, len(order), args.batch_size)):
                rows = [train[i] for i in order[start:start+args.batch_size]]
                width = max(len(r["input_ids"]) for r in rows)
                ids = torch.tensor([r["input_ids"] + [tokenizer.pad_token_id]*(width-len(r["input_ids"])) for r in rows], device="cuda")
                labels = torch.tensor([r["labels"] + [-100]*(width-len(r["labels"])) for r in rows], device="cuda")
                mask = torch.tensor([[1]*len(r["input_ids"]) + [0]*(width-len(r["input_ids"])) for r in rows], device="cuda")
                divisor = min(args.grad_accum, batches-(batch_no//args.grad_accum)*args.grad_accum)
                with torch.autocast("cuda", dtype=torch.bfloat16):
                    loss = model(input_ids=ids, attention_mask=mask, labels=labels).loss
                if not torch.isfinite(loss):
                    raise RuntimeError("Nonfinite loss")
                window_loss += loss.item()/divisor
                (loss/divisor).backward()
                if (batch_no+1) % args.grad_accum == 0 or batch_no+1 == batches:
                    norm = torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0, error_if_nonfinite=True)
                    optimizer.step()
                    scheduler.step()
                    optimizer.zero_grad(set_to_none=True)
                    step += 1
                    run.log({"train/loss": window_loss, "train/grad_norm": float(norm), "train/lr": scheduler.get_last_lr()[0], "optimizer_step": step})
                    print(f"epoch={epoch} step={step} loss={window_loss:.5f}", flush=True)
                    window_loss = 0.0
            checkpoint = args.output_dir / f"epoch_{epoch}"
            model.save_pretrained(checkpoint)
            tokenizer.save_pretrained(checkpoint)
            history.append(evaluate(epoch))
            save_json(args.output_dir / "history.json", history)
            best = max(history[1:], key=lambda x: (x["balanced_accuracy"], x["parse_rate"], -x["epoch"]))
            save_json(args.output_dir / "best_adapter.json", {"path": str(args.output_dir / f"epoch_{best['epoch']}"),
                       "metrics": best, "baseline": history[0], "note": "Selected on 40-row development holdout; not independently tested or deployed."})
        save_json(args.output_dir / "completed.json", {"optimizer_steps": step, "epochs": args.epochs, "wandb_url": run.url})
    finally:
        run.finish(exit_code=1 if sys.exc_info()[0] is not None else 0)


if __name__ == "__main__":
    main()
