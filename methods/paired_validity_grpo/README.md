# Independent paired validity GRPO pilot

Available on `main`. All changes are new files in this
directory relative to `4ab22dc`; no original R-Zero source is modified.
Existing `verl.trainer.main`, Solver prompt, math reward, and checkpoint merger
are called read-only. The experiment has its own entry point and output directory.

Two independent Qwen3-4B-Base runs, original then repaired, each using all four
allocated GPUs. This is not two simultaneous two-GPU runs. Both start from the
same resolved model snapshot, with the same data shuffle and rollout seed.
No Questioner, API, relabeling, Terra replay, dynamic/negative-only update or
validity gate runs here. Label scores do not weight or filter training data.

## Configuration

The new `train.yaml` is a copy of the existing R-Zero example defaults; the
launcher writes fully resolved per-arm configs before training. Key settings:

* GRPO, 10 global rollout steps, 512 questions/step, 5 responses/question.
* Actor global batch 128, update/experience microbatch 1 per GPU, LR 1e-6.
* Original math reward: 0.9 answer accuracy + 0.1 format reward.
* KL loss 0.01; rollout temperature 1, top-p 0.99; TP=2 on four GPUs.
* Prompt limit 2048, answer limit 4096, rollout GPU utilization 0.7;
  gradient checkpointing and original offload settings retained for A100 80GB.
* Same seeds (default 1), same paired row order, original shuffled drop-last
  dataloader semantics. All rows are available; each epoch drops its incomplete
  batch as in R-Zero. Ten steps are not ten full epochs or ten optimizer minibatches.
* Abort both arms on overlong prompts; disable per-arm filtering/truncation in
  practice by checking exact training tokenization first.
* Checkpoints and merged Hugging Face weights at steps 5 and 10.
* A shared subset of up to 64 unchanged training questions provides diagnostic
  validation at steps 5/10. It is NOT held-out evaluation or paper evidence.
  Downstream benchmark evaluation is a separate subsequent step.
* Console logs only. Each arm has its own working/output directory; local Ray
  starts independently, and the launcher never executes `ray stop` or kills
  unrelated processes. Use an exclusive four-GPU allocation.

## Linux

Run from the existing main checkout; no separate branch or worktree is required:

```bash
cd /storage1/jiaxinh/Active/jinyuan/R-zero
git pull --ff-only origin main

# Activate the same working rzero-py310 environment as the labeling run.
export LABELS_DIR=/storage1/jiaxinh/Active/jinyuan/R-zero/analysis_results/validity_repair_labels_4gpu_full_b64_v1
export GRPO_OUTPUT_DIR=/storage1/jiaxinh/Active/jinyuan/R-zero-storage/paired_validity_grpo_v1

# CPU preparation: check pairs, tokenizer lengths and config; write local parquet.
bash methods/paired_validity_grpo/run.sh \
  --labels-dir "$LABELS_DIR" --output-dir "$GRPO_OUTPUT_DIR" --prepare-only

# Inside the allocated four-A100 session (prefer tmux): original then repaired.
bash methods/paired_validity_grpo/run.sh \
  --labels-dir "$LABELS_DIR" --output-dir "$GRPO_OUTPUT_DIR"
```

GPU IDs inherit `CUDA_VISIBLE_DEVICES`, otherwise default to 0,1,2,3. You may pass
`--gpus 0,1,2,3` when appropriate. `--model /absolute/base/snapshot` can reuse the
same local BASE model used for labeling. Hub model names are resolved to one
snapshot path before either arm starts; do not use a Terra or trained Solver.

Monitor `$GRPO_OUTPUT_DIR/{original,repaired}/train.log`. Final step-10 models:
`$GRPO_OUTPUT_DIR/{original,repaired}/checkpoints/global_step_10/actor/huggingface`.
`completed.json` appears for each arm only after both checkpoint merges succeed.

Rerun with `--resume` after interruption; completed arms are skipped, and an
incomplete arm resumes from its latest saved step (or restarts if none was saved).
Keep inputs, source checkout, model and settings fixed. `--arm repaired` or
`--arm original` selects a single arm with the same frozen protocol. Do not run
two launcher instances on the same output directory. No automatic benchmark
evaluation, remote dataset upload, training submission, or main-branch update.

Tests: `python -m unittest discover -s methods/paired_validity_grpo/tests -v`.
