# Single-GPU raw judge probe

Run only inside a single allocated GPU job, in the existing R-Zero environment.
No training, Ray, external API, reward changes, uploads, or automatic retries.
Default input: 20 unique questions sampled with seed 43 from clean Terra **train**,
paired into 10 disjoint pairs. These are not the original training pairs and have
no same-type gold labels. VALID/INVALID metadata is saved but not sent to the model.

```bash
# From the repository root, with the existing Python environment active.
# Preserve the scheduler's CUDA_VISIBLE_DEVICES when it already exposes one GPU.
python -m methods.validity_rzero.probe_octothinker_judge \
  --questions 20 \
  --output-dir "$STORAGE_PATH/diagnostics/octo_judge_$(date +%Y%m%d_%H%M%S)"
```

If your allocated environment exposes several GPUs, explicitly select ONE of
those allocated GPUs via CUDA_VISIBLE_DEVICES. Never run this on a login node.
Use `--model /path/to/OctoThinker-Hybrid-Base/snapshot` to reuse local weights.
Do not use the validity step10 or the trained Questioner: this probes the frozen base.
Use `--train-parquet /path/to/validity_run/data/train.parquet` to avoid a dataset
download. Otherwise the loader explicitly reads train.jsonl from
`jinyuan222/rzero-validity-rl-terra-v1-clean-v1`.

The default `current` condition imports the production prompt, sampler and parser.
It uses raw completion (no chat wrapper), native tokenizer and EOS, the exact
boxed stop strings, temperature 0.6, top_p 0.95, top_k 20, presence_penalty 1.5,
and max_tokens 1024. It measures **first attempts**, unlike online metrics after
one retry; different batch sizes also mean outputs need not match training exactly.
Single GPU, TP=1, batch size 4, memory utilization 0.6, context cap 8192. Long
inputs are rejected rather than silently truncated. Increase --max-model-len
explicitly if needed; it is a memory limit, not a prompt-format change.

Optional second condition in the SAME model load:

```bash
python -m methods.validity_rzero.probe_octothinker_judge \
  --conditions current no-box-stop --questions 20 \
  --output-dir "$STORAGE_PATH/diagnostics/octo_judge_compare_$(date +%Y%m%d_%H%M%S)"
```

This generates 20 responses total, not 20 per question. `no-box-stop` only removes
the two boxed early-stop strings; EOS and output length limits remain. Inspect
raw continuations rather than interpreting either condition as semantic accuracy.

Artifacts (new directory required; partial results are retained on interruption):

- `pairs.jsonl`: exact sampled rows and production prompts.
- `manifest.json`: source, selection hash, tokenizer and sampling settings.
- `raw_outputs.jsonl`: prompt/output token IDs, text, special-token-inclusive
  decode, finish_reason, stop_reason, output length and strict parser result.
- `report.txt`: complete readable prompts and outputs, no display truncation.
- `summary.json`: parse failures, length stops and label counts, not accuracy.

Send back report.txt and summary.json first. If responses hit the token limit,
test a few pairs with --max-tokens 2048; do not change the live gate based only
on this tiny random sample. This entry does not alter automatic artifact cleanup
in the production training pipeline.
