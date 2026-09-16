# Small judge SFT, v2_clear

Run on exactly one allocated A100/H100, with existing torch/transformers/peft
and authenticated W&B. No Ray, TRL, quantization or automatic deployment.

```bash
python -m methods.validity_rzero.train_judge_sft \
  --model /path/to/OctoThinker-3B-Hybrid-Base/snapshot \
  --data-dir /path/to/semantic_judge_200/v2_clear \
  --output-dir /path/to/new/judge_sft_run
```

Defaults: 160 train / 40 development holdout, 3 epochs, batch 2 × accumulation 4,
60 optimizer updates, BF16, LoRA all-linear rank16/alpha32/dropout0.05,
AdamW lr1e-4/weight_decay0.01, 10% warmup, linear decay, gradient clipping1.
W&B online is explicit; missing credentials must be resolved, not silently ignored.
Data validation must be run separately with the data package's validate.py.

The saved tokenizer has the repository's Octo plain role template. Render only
system+user with add_generation_prompt=True, encode without extra special tokens,
then append target assistant tokens and EOS. This avoids the existing full-chat
template's different assistant separator. Prompt and padding labels are -100.
The manifest and system_prompt.txt define the inference protocol; no few-shot.
No sequence is silently truncated. Max training length2048; evaluation greedy
max256 new tokens with EOS stopping (no stop-at-box), so length_stops also tests
whether the model learned to finish. This differs from earlier vLLM probes;
baseline epoch0 is recomputed with this same protocol, not reused from old probes.

Epoch0 evaluates the base; epochs1–3 save adapters and evaluate all40 rows.
eval_epoch_N.json contains full responses. best_adapter.json chooses by balanced
accuracy then parse rate then earlier epoch. Do not treat this selection set as
an unbiased test set; it has small sample size and family/domain shift.
Checkpoint directories contain adapters, not merged full weights or optimizer
resume state. completed.json indicates success. Never replace the frozen online
judge automatically. Merge/export and production wiring require a later decision.
