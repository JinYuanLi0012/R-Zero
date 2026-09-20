# Overnight Octo code evaluation queue

Evaluate any number of Octo Solver checkpoints on HumanEval+ and MBPP+ using
the matched training-template protocol from `evaluation/octo_code_eval/`.
Default: four independent lanes on GPUs 0,1,2,3, one model per GPU (TP=1).
A lane finishes generation and CPU scoring before taking the next queued model.
At most four model jobs and 16 CPU scoring workers (4 per model) run concurrently.
LiveCodeBench is not downloaded or evaluated by this entry.

## Paste checkpoint paths

Activate your existing R-Zero environment, set `STORAGE_PATH`, and run from the
repository root. If not already installed, first run
`bash evaluation/code_eval/setup.sh` once.

```bash
git pull --ff-only origin main
bash evaluation/octo_code_batch/run.sh \
  --output "$STORAGE_PATH/code_eval/octo_batch_01" \
  /path/to/solver_v1 \
  /path/to/solver_v2 \
  /path/to/solver_v3 \
  /path/to/solver_v4 \
  /path/to/solver_v5
```

Supply 10, 20 or more paths the same way. Each may be a complete merged HF model,
a `global_step_N` directory, or a Solver run directory. For a run directory, the
highest-numbered `global_step_N` is selected and its merged checkpoint must be
complete. No automatic merge or fallback to an earlier step is performed. Paths
with spaces must be shell-quoted. Invalid paths are reported as FAILED and do not
prevent other models from running. Duplicate resolved checkpoints are queued once.

To include the original Base with the identical template and generation settings:

```bash
bash evaluation/octo_code_batch/run.sh \
  --output "$STORAGE_PATH/code_eval/octo_batch_with_base" \
  --base-model OctoThinker/OctoThinker-3B-Hybrid-Base \
  /path/to/solver_v1 /path/to/solver_v2
```

## Read many paths from a file and leave overnight

Create `octo_checkpoints.txt`, one path per line, without shell quotes. Blank
lines and lines beginning with `#` are ignored. Relative paths resolve from the
directory where you launch the command. Then:

```bash
mkdir -p "$STORAGE_PATH/code_eval/octo_batch_01"
nohup bash evaluation/octo_code_batch/run.sh \
  --models-file octo_checkpoints.txt \
  --output "$STORAGE_PATH/code_eval/octo_batch_01" \
  > "$STORAGE_PATH/code_eval/octo_batch_01/console.log" 2>&1 &

# Check progress, or read the final table the next morning:
tail -f "$STORAGE_PATH/code_eval/octo_batch_01/console.log"
cat "$STORAGE_PATH/code_eval/octo_batch_01/summary.txt"
```

On a managed cluster, launch inside your GPU allocation (e.g. a scheduler job or
tmux attached to an allocation). `nohup` does not extend an expired allocation.
`--gpus 0,1,2,3` is the default; override it with the actual IDs available to your
job, e.g. `--gpus 0,3`. These values are assigned directly to CUDA_VISIBLE_DEVICES,
not remapped relative to an inherited CUDA_VISIBLE_DEVICES list.

## Results and restart

Each completion immediately prints its two scores. Final screen output is a table
with model path, status, GPU, HumanEval+, MBPP+, and elapsed minutes. Scores are
percentages (0–100). Missing/failed scores are `--`, never zero or an old result.

The batch directory contains:

- `summary.txt`, `summary.csv`, `summary.json`, refreshed after each completion.
- `logs/`: one appended log per model, including the exact child command.
- `models/`: original per-model artifacts and resumable generation/scoring results.
  Paths include a hash so repeated names such as `huggingface` cannot collide.
- `cache/`: per-GPU caches, reused sequentially on a lane and isolated across lanes
  to avoid concurrent initial EvalPlus cache writes.

Rerun the same command/output directory after interruption. The child evaluator
reuses completed generations and scores; it still validates configuration/data
and tokenizer metadata. You may add new checkpoint paths; the latest invocation
determines the rows in the batch summary, while older per-model artifacts remain.
Changed evaluation settings require a new batch output directory because each
child rejects incompatible resume configurations. Checkpoints must not be updated
in place while evaluating.

One failure does not stop the queue. The final exit status is nonzero if any model
failed. Ctrl-C/SIGTERM stops active child process groups and marks unfinished jobs
CANCELLED. Optional `--job-timeout-hours 4` prevents a single model from occupying
a lane indefinitely (default 0, no wall timeout); a timeout is FAILED and the lane
continues. Under `nohup`, send SIGTERM to the launcher PID to stop it cleanly.

Defaults match the single-model Octo entry: 4096 output tokens, 16384 total context,
BF16, greedy one-sample decoding, batch size 32, seed 42, GPU utilization 0.85.
You can override `--max-new-tokens`, `--max-model-len`, `--batch-size`,
`--gpu-memory-utilization`, `--seed`, and `--workers` for the entire batch. Base and
Solver always receive the same settings. No new GPU/pip dependencies are added.

CPU queue tests (fake inference; not GPU benchmark validation):

```bash
python -m unittest discover -s evaluation/octo_code_batch/tests -v
```

This directory is additive. Neither the old code evaluator nor the single-model
Octo evaluator or their resume fingerprints is changed.
