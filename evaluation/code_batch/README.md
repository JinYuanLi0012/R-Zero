# code eval final — main-table protocol

The recommended main-table entry is now `run_final.sh` (also the default of
`run.sh`). **All Qwen/Octo Base and Solver models use direct completion** through
one evaluator. No chat templates or CoT instructions are applied. Historical
legacy and matched modes remain available for reproducing earlier experiments.

```bash
git pull --ff-only origin main
export STORAGE_PATH=/storage1/jiaxinh/Active/jinyuan/R-zero-storage
if [[ ! -f "${CODE_EVAL_TOOLS:-$STORAGE_PATH/code_eval_tools}/environment.json" ]]; then
  bash evaluation/code_eval/setup.sh
fi
EVAL_BATCH_DIR="$STORAGE_PATH/code_eval/qwen_octo_42_code_eval_final_v1"
mkdir -p "$EVAL_BATCH_DIR"
nohup bash evaluation/code_batch/run_final.sh \
  --manifest evaluation/code_batch/manifests/qwen_octo_42_final.json \
  --gpus 0,1,2,3 --workers 4 --output "$EVAL_BATCH_DIR" \
  > "$EVAL_BATCH_DIR/console.log" 2>&1 &
echo "PID: $!"
tail -f "$EVAL_BATCH_DIR/console.log"
# In another terminal:
cat "$STORAGE_PATH/code_eval/qwen_octo_42_code_eval_final_v1/summary.txt"
```

The final manifest contains the exact same 42 checkpoints (31 Qwen + 11 Octo).
All 11 `（重新评）` models are first. The first four queued models are Qwen Base,
R-Zero v2, semantic novelty v2 (the three original paper-table entries), then
R-Zero v1. Four GPUs take models from this ordered queue; completion order can vary.
Labels remain visible in the console and summaries. All 42 models are regenerated
in this new directory, not just the marked models. Reuse this directory only to
resume this final experiment; use another directory for a fresh rerun.

Optional `--family qwen` or `--family octo` filters the final manifest. Preview:

```bash
bash evaluation/code_batch/run_final.sh \
  --manifest evaluation/code_batch/manifests/qwen_octo_42_final.json \
  --output /tmp/code-eval-final-preview --dry-run
```

See [the final protocol specification](../final_code_eval/README.md) for exact
settings and the differences from the first completion implementation.

---

# Explicit Qwen / Octo multi-model code evaluation

An additive mixed-family queue. Existing single-model and Octo-only entries are
unchanged. Default: GPUs 0,1,2,3, TP=1, one model per GPU, HumanEval+ and MBPP+ only.
Each lane completes generation and CPU scoring, then takes another model. Failures
are reported and the queue continues. The existing official CPU environment is reused.

## Ready-to-run user list: 31 models

`manifests/qwen_octo_31.json` contains the requested exact groups:

| Family | Group | Count |
|---|---|---:|
| Qwen | OCNR Solver v1–v5 | 5 |
| Qwen | R-Diverse rounds 1–5, attempt_1/global_step_15 | 5 |
| Qwen | validity clean formal r10 initstep15, Solver v1–v5 | 5 |
| Qwen | K8 frozenstep15 noreplay, Solver v1–v5 | 5 |
| Octo | original Hybrid Base | 1 |
| Octo | pure R-Zero 8k five-round Solver v1–v5 | 5 |
| Octo | semantic novelty gate K8 SFT judge Solver v1–v5 | 5 |

R-Diverse entries name the complete `actor/huggingface` directory, not an individual
weight shard. `/storage1/...` and `/engrfs/...` are preserved exactly as provided.
Both mounts must be accessible on the execution node. The Mac implementation does
not establish that the Linux files exist or contain merged weights.

From an activated R-Zero environment in the repository root:

```bash
git pull --ff-only origin main
export STORAGE_PATH=/storage1/jiaxinh/Active/jinyuan/R-zero-storage
# First installation only; skip if this CPU evaluator is already installed:
bash evaluation/code_eval/setup.sh

EVAL_BATCH_DIR="$STORAGE_PATH/code_eval/qwen_octo_31_v1"
mkdir -p "$EVAL_BATCH_DIR"
nohup bash evaluation/code_batch/run.sh --protocol legacy \
  --manifest evaluation/code_batch/manifests/qwen_octo_31.json \
  --qwen-prompt-style base \
  --gpus 0,1,2,3 --workers 4 \
  --output "$EVAL_BATCH_DIR" \
  > "$EVAL_BATCH_DIR/console.log" 2>&1 &

tail -f "$EVAL_BATCH_DIR/console.log"
# Final table (also printed at completion):
cat "$EVAL_BATCH_DIR/summary.txt"
```

Use a GPU allocation that lasts long enough; nohup does not extend scheduler time.
The GPUs are literal CUDA_VISIBLE_DEVICES values for your allocation. Model jobs
share the same four lanes; this does not launch four Qwen plus four Octo jobs.
Inference defaults: BF16, greedy, one sample, 4096 output tokens, 16384 context,
batch size 32, seed 42 and GPU utilization 0.85. CPU judge workers default to 4 per
model. Optional `--job-timeout-hours 4` marks an overlong model FAILED and continues.

## Select a family

With a manifest, `--family` filters the list:

```bash
# Only the 20 Qwen models:
bash evaluation/code_batch/run.sh --protocol legacy --family qwen \
  --manifest evaluation/code_batch/manifests/qwen_octo_31.json \
  --output "$STORAGE_PATH/code_eval/qwen_20_v1"

# Only the 11 Octo models, including Base:
bash evaluation/code_batch/run.sh --protocol legacy --family octo \
  --manifest evaluation/code_batch/manifests/qwen_octo_31.json \
  --output "$STORAGE_PATH/code_eval/octo_11_v1"
```

Without a manifest, explicitly specify the family for your paths:

```bash
bash evaluation/code_batch/run.sh --protocol legacy --family qwen --output /output/qwen \
  /path/to/solver_v1 /path/to/solver_v2
bash evaluation/code_batch/run.sh --protocol legacy --family octo --output /output/octo \
  --base-model OctoThinker/OctoThinker-3B-Hybrid-Base \
  /path/to/octo_solver_v1 /path/to/octo_solver_v2
```

`--models-file FILE` accepts one path per line; use `--family` with it. A manifest
is a JSON list with explicit `family`, `model`, optional `label` and boolean
`base_model`. No family is guessed from checkpoint names. Paths may name a merged
model, a global_step directory, or a run root; the latest numeric step must have
complete merged weights. A pasted `.safetensors`/`.bin` path is normalized to its
parent model directory. No automatic weight merging is performed.

## Protocols and results

- `qwen` calls the original `evaluation/code_eval/run.py`. Default
  `--qwen-prompt-style base` preserves its original benchmark-completion protocol.
  Set `--qwen-prompt-style chat` explicitly if using saved Qwen chat templates;
  this changes the evaluation protocol and requires matching comparisons.
- `octo` calls `evaluation/octo_code_eval/run.py`, using the matched training
  role template and explicit single-BOS token inputs for Base and trained Solver.
  The Qwen prompt-style option has no effect on Octo.
- The manifest contains only the requested Octo Base, not an additional Qwen Base.
  All Qwen checkpoints in one invocation share the chosen Qwen mode. The summary
  records family/protocol and does not combine scores across model families.

Each model prints scores when finished. `summary.txt`, `summary.csv`, `summary.json`
are refreshed as jobs finish; `logs/` and `models/` preserve detailed per-model
artifacts. Stable hashed paths include family/protocol to prevent collisions.
Rerun the same command/output directory to reuse completed generations and scores
after the child evaluator validates its configuration. Failures have no scores and
produce a nonzero final exit code. Ctrl-C/SIGTERM stops child process groups.

Preview selections without loading models, creating outputs or checking remote paths:

```bash
bash evaluation/code_batch/run.sh --protocol legacy \
  --manifest evaluation/code_batch/manifests/qwen_octo_31.json \
  --output /tmp/preview --dry-run
```

Tests: `python -m unittest discover -s evaluation/code_batch/tests -v`.
These validate routing/queue behavior on CPU, not model inference or Linux mounts.

## Historical alternative: matched Base/Solver chat protocol

For the separate chat-protocol sensitivity experiment, use `run_matched.sh`. It selects
`--protocol matched` and the shared `evaluation/matched_code_eval` evaluator.
Within each family, original Base and trained Solver receive identical formatting.
Both families receive the same code instructions; only training templates/tokens
vary. Do not pass `--qwen-prompt-style` to this entry. `run.sh` now defaults to final; select `--protocol legacy` explicitly for historical routing. Old scores must not be mixed with matched scores.

```bash
export STORAGE_PATH=/storage1/jiaxinh/Active/jinyuan/R-zero-storage
EVAL_BATCH_DIR="$STORAGE_PATH/code_eval/qwen_octo_31_matched_v1"
mkdir -p "$EVAL_BATCH_DIR"
nohup bash evaluation/code_batch/run_matched.sh \
  --manifest evaluation/code_batch/manifests/qwen_octo_31.json \
  --gpus 0,1,2,3 --workers 4 --output "$EVAL_BATCH_DIR" \
  > "$EVAL_BATCH_DIR/console.log" 2>&1 &
# Optional: add --family qwen or --family octo to select one family.
cat "$EVAL_BATCH_DIR/summary.txt"
```

See `evaluation/matched_code_eval/README.md` for exact role organization, thinking,
BOS/EOS, tokenization and training-source audit. GPU scheduling, failure continuation
and summaries remain the same. The 31-model manifest includes Octo Base but no Qwen
Base; a Qwen-only run can add `--base-model Qwen/Qwen3-4B-Base --family qwen`.

## Expanded 42-model matched rerun

`manifests/qwen_octo_42.json` preserves all 31 original entries and appends:
Qwen/Qwen3-4B-Base, five Qwen R-Zero 8k Solver rounds, and five Qwen semantic
novelty gate Solver rounds. Total: 31 Qwen + 11 Octo, including both original
Base models. The 11 appended labels end in `（重新评）`; this appears in the
terminal table and summary.txt / summary.csv / summary.json. It is a display
annotation, not a different evaluation protocol.

From the Linux repository root, with the R-Zero environment active and four GPUs:

```bash
git pull --ff-only origin main
export STORAGE_PATH=/storage1/jiaxinh/Active/jinyuan/R-zero-storage
if [[ ! -f "${CODE_EVAL_TOOLS:-$STORAGE_PATH/code_eval_tools}/environment.json" ]]; then
  bash evaluation/code_eval/setup.sh
fi
EVAL_BATCH_DIR="$STORAGE_PATH/code_eval/qwen_octo_42_matched_v1"
mkdir -p "$EVAL_BATCH_DIR"
nohup bash evaluation/code_batch/run_matched.sh \
  --manifest evaluation/code_batch/manifests/qwen_octo_42.json \
  --gpus 0,1,2,3 --workers 4 --output "$EVAL_BATCH_DIR" \
  > "$EVAL_BATCH_DIR/console.log" 2>&1 &
echo "PID: $!"
# Progress:
tail -f "$EVAL_BATCH_DIR/console.log"
# Final table (also updated while running):
cat "$EVAL_BATCH_DIR/summary.txt"
```

Use this new output directory to rerun every model under the matched protocol.
Optional `--family qwen` selects 31 models; `--family octo` selects 11. Both
/storage1 and /engrfs checkpoint locations must be accessible on the Linux host.
The R-diverse entries point at complete huggingface directories, not one shard.
