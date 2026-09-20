# Paired validity repair — stage 1

Repair the INVALID questions in the **original Terra train export (1,993 rows:
852 VALID + 1,141 INVALID)**. Compare an unchanged arm with a repaired arm at the
same IDs and positions. This stage creates **question-only** data, not solver
pseudo-labels or GRPO training runs. Do not pass the clean 1,943-row export.

The source is the earlier `jinyuan222/rzero-validity-rl-terra-v1` train split,
normally already saved as `analysis_results/validity_rl_terra_dataset_v1/train.jsonl`.
The original sampling split had 2,000 train questions; seven were excluded during
answer verification. This experiment uses the agreed 1,993-row export, without
recovering the seven or adding validation rows.

## Protocol

- Leave all originally VALID questions untouched.
- Sol independently checks each selected INVALID question and either proposes
  1–3 exact, non-overlapping substring replacements or abstains. Historical
  labels are not treated as ground truth by the repairer.
- Preserve mathematical objects, target, and task type. Only local correction,
  necessary missing conditions, and disambiguation are allowed. No unrelated
  rewriting, answer hints, or deletion of core constraints to simplify the task.
- A separate Sol call receives only ID, original question, and candidate question:
  **no repair reasoning, proposed answer, round, split, source pseudo-label or
  historical invalid subtype**. It independently checks validity and edit scope.
- Accept only an original judged B/C/D/E, a repaired question judged A, all six
  scope checks true, and review confidence >= 0.8. F/uncertain does not pass.
- Keep the exact original text on abstention, rejected review, malformed output,
  or API request failure. An `already_valid` observation is recorded but does not
  relabel or replace the source. No source rows are deleted or independently filtered.
- One semantic proposal and one review at most per selected question. Rejections
  are not repeatedly regenerated until they pass. Request-level failed/missing
  outputs are recorded and retained unchanged rather than silently resampled.
- Defaults: **gpt-5.6-sol**, **high**, **16,384 max output tokens**, **synchronous concurrent Responses API**
  (default concurrency 16). Batch remains available with `ANNOTATION_MODE=batch`. Both stages use the same model; the review is a separate call,
  not an independent model family. This does not guarantee mathematical correctness.

`protocol.py` contains the fixed prompts and strict schemas. Raw Responses outputs
and Batch inputs/outputs are retained for inspection. API mathematical checks are
stored only in audit files and never exported as training answers.

## Linux smoke (10 INVALID questions, synchronous mode)

Activate the existing R-Zero Python environment (with the `openai` package), then:

```bash
cd /storage1/jiaxinh/Active/jinyuan/R-zero
git pull --ff-only
git rev-parse --short HEAD

export OPENAI_API_KEY="your-key"
export INPUT_JSONL=analysis_results/validity_rl_terra_dataset_v1/train.jsonl
export OUTPUT_DIR=analysis_results/validity_repair_sol_sync_smoke10_v1
export ANNOTATION_MODE=sync
export CONCURRENCY=16
export REPAIR_MODEL=gpt-5.6-sol
export REPAIR_REASONING_EFFORT=high
export REPAIR_MAX_OUTPUT_TOKENS=16384
export REPAIR_LIMIT=10
export BATCH_POLL_SECONDS=60

# Optional: validate source and selection without any API requests.
bash methods/validity_repair/run.sh --prepare-only

# Real smoke: concurrent repair calls, then concurrent review calls, then paired exports.
bash methods/validity_repair/run.sh
```

If the dataset is elsewhere, change `INPUT_JSONL` to its actual **Linux** location.
For the locally downloaded file, upload `train (2).jsonl` to Linux and point
`INPUT_JSONL` there. Do not put `/Users/...` paths in the Linux command.

The smoke selects 10 INVALID IDs with seed 42; it still exports all 1,993 rows
in each arm. Other INVALID rows have `not_selected` status. Smoke valid-rate
changes therefore use the whole dataset denominator; see acceptance rate among
selected questions to evaluate repair quality. Each completed sync call is saved
and progress is printed. Run in tmux if convenient.

## Full run (after reviewing smoke)

Keep the same input/model settings, use a fresh output directory, and remove the
smoke limit:

```bash
export OUTPUT_DIR=analysis_results/validity_repair_sol_sync_full_v1
export REPAIR_LIMIT=0
bash methods/validity_repair/run.sh
```

`0` processes all 1,141 INVALID questions. The review stage contains only
successfully parsed proposals, so its request count can be smaller. The separate
full run includes the smoke questions again; it does not splice pilot artifacts
into the final run. If the protocol is changed after smoke, use a new directory.

## Resume and output

Synchronous mode is now the default. It sends ordinary `responses.create` calls
through a bounded thread pool (default 16). You may lower `CONCURRENCY` for rate
limits; concurrency can change on resume. The SDK's default transport retries
apply to transient API failures. A completed semantic rejection is never retried.
Every response, including failed requests, is persisted per item. A rerun skips
all persisted outcomes, including failures. A request interrupted before its
artifact is saved can be submitted again; already saved items are not resampled.

Use a **new output directory when switching between Batch and sync**. If an old
Batch was already submitted, switching modes does not cancel that remote Batch.
For the old behavior explicitly set `ANNOTATION_MODE=batch`; existing Batch
manifests from the first release remain resumable in that mode.


In Batch mode, re-run the same command with the same input, model, protocol and output directory
to resume a submitted Batch. Saved Batch IDs are reused. One process may own an
output directory at a time. Changed settings/input are rejected to avoid mixing
results. A failed/cancelled whole Batch stops the run for inspection; the script
will not silently resubmit it. Expired/missing individual outputs remain failures.

Inspect:

```bash
cat "$OUTPUT_DIR/analysis/report.md"
cat "$OUTPUT_DIR/analysis/statistics.json"
```

| File | Contents |
|---|---|
| `original_questions.jsonl` | Original arm: only ID, question, round, train split |
| `repaired_questions.jsonl` | Same IDs/order/size; accepted repairs substituted |
| `repair_audit.jsonl` | Every source row, outcome, original/candidate/final text, repair/review judgments |
| `accepted_repairs.jsonl` | Accepted pairs for manual inspection |
| `unresolved.jsonl` | Originally INVALID rows not replaced, including smoke-unselected rows |
| `analysis/report.md`, `statistics.json` | Counts, acceptance rate, nominal validity, per-round counts, exact uniqueness |
| `manifest.json`, `prepare_manifest.json` | Source/selection hashes, selected IDs, settings, prompts/schemas |
| `sync/` or `batch/`, `artifacts/` | Persisted mode-specific state, raw requests/responses, parsed per-question artifacts |

The reported repaired validity rate is **nominal**: inherited original VALID
labels plus accepted repairs, divided by all rows. It is not a new independent
validity audit of every question. Exact duplicates introduced by repair are
reported, not dropped. The next stage must generate solver majority-vote answers
and share labels for unchanged questions; it is not implemented here.

## Local checks

```bash
python -m unittest discover -s methods/validity_repair/tests -v
bash -n methods/validity_repair/run.sh
```

Tests use fake Batch clients and temporary fixtures; they do not need credentials,
call paid APIs, upload datasets or load GPU models. The prepare-only check supports
the real source data without importing OpenAI.

Batch transport/atomic IO helpers are reused from `methods/validity_rl_terra_dataset/`.
API format reference: https://developers.openai.com/api/docs/guides/batch

## Stage 2: matched arms and base-Solver majority labels

`label_pairs.sh` consumes the completed stage-1 output. It retains **all**
`accepted` repairs and `unchanged_valid` rows, without new manual selection.
Every other original INVALID ID is removed from both arms. For the supplied
full run this is **1,546 pairs = 852 shared + 694 changed**, requiring **2,240
question-version generations** (20,160 completions at nine samples each).

The default model is **Qwen/Qwen3-4B-Base**, not a Terra mid-trained checkpoint.
Set `LABEL_MODEL` to the unchanged base model's local Linux directory if desired.
Do not use a fine-tuned Solver checkpoint. For a Hub model, `--revision COMMIT`
can pin its version; a local model directory should remain immutable during a run.

We extracted the existing ordered answer clustering from
`question_evaluate/evaluate.py` into `question_evaluate/majority.py`, which is now
shared by both entry points. This preserves mathruler boxed extraction, exact
matching, the historical `no ` shortcut, bidirectional mathematical equivalence
with a 10-second comparison timeout, first-group tie breaking, and agreement
score over nonempty extracted answers. “Majority” means the largest answer group;
it need not exceed 50%. Scores are agreement, not correctness.

Generation matches the ordinary R-Zero base-Solver prompt and sampling defaults:
9 completions, temperature 1.0, top_p 1.0, top_k 40, max response 4096 tokens,
EOS stop. It directly calls vLLM without validity prompts/gates or Terra answers.
Each job gets a deterministic seed derived from its ID and seed 42. The two
unchanged-arm entries reuse a single saved job. Changed versions have separate
jobs. No API key is needed in stage 2.

No [0.3,0.8] score filter or legacy question-type filter is applied. Score=1 and
low-agreement questions are retained. If either version has no usable majority
answer (empty / mathruler `None` sentinel / literal `INVALID`), the ID is excluded
from **both** arms and recorded. “No solution” remains a possible mathematical
pseudo-answer. Generation/grader execution errors stop the script so they cannot
silently cause content-dependent deletions; fix the environment and resume.

Run in a GPU allocation with the existing R-Zero environment. Single-GPU smoke:

```bash
cd /storage1/jiaxinh/Active/jinyuan/R-zero
git pull --ff-only
export REPAIR_DIR=analysis_results/validity_repair_sol_sync_full_v1
export LABEL_MODEL=Qwen/Qwen3-4B-Base
export LABEL_OUTPUT_DIR=analysis_results/validity_repair_labels_smoke8_v1
export PAIR_LIMIT=8
export LABEL_BATCH_SIZE=16
export LABEL_TP_SIZE=1

# CPU-only source validation; no model download or GPU initialization:
bash methods/validity_repair/label_pairs.sh --prepare-only

# Use a GPU assigned to your job (this example uses visible device 0):
CUDA_VISIBLE_DEVICES=0 bash methods/validity_repair/label_pairs.sh
cat "$LABEL_OUTPUT_DIR/analysis/report.md"
```

After smoke, full labeling:

```bash
export PAIR_LIMIT=0
export LABEL_OUTPUT_DIR=analysis_results/validity_repair_labels_full_v1
CUDA_VISIBLE_DEVICES=0 bash methods/validity_repair/label_pairs.sh
```

If allocating four GPUs for one tensor-parallel model, explicitly set
`LABEL_TP_SIZE=4` and `CUDA_VISIBLE_DEVICES=0,1,2,3`. This is optional, not required.
Default context length is 8192. Overlong prompts cause an error rather than silent
truncation. Tune memory/batch settings after smoke if needed; use a fresh directory
when changing saved generation settings. Completed runs can be finalized again
without initializing a GPU model. Partial runs resume saved per-job artifacts;
in-flight unsaved chunks may be regenerated. Same seeds do not guarantee bitwise
identical GPU results across environments.

Main outputs:

- `original_train.jsonl`, `repaired_train.jsonl`: identical retained IDs/order;
  fields include `problem`, `answer`, `score`, and audit identifiers. Shared rows
  have exactly the same answers and scores. No HF upload or GRPO run occurs here.
- `pairs.jsonl`, `label_jobs.jsonl`: paired selection and deduplicated shared work.
- `excluded_repair_ids.jsonl`: 447 IDs excluded by the agreed stage-1 status rule.
- `excluded_label_ids.jsonl`: additional paired exclusions due to unusable labels.
- `artifacts/`: raw nine completions, extracted answers, vote groups, finish
  reasons, and input/configuration hashes for every job.
- `label_results.jsonl`, `analysis/report.md`, `analysis/statistics.json`:
  label outputs and retained counts/score summaries.
- `pair_manifest.json`, `label_manifest.json`: selection and generation settings.

Send back the report, both `*_train.jsonl`, and `excluded_label_ids.jsonl` to
check the labeling result before implementing the two 10-step GRPO runs.
Local tests use fake vLLM/tokenizer/grader modules. Real GPU generation must be
validated by the Linux smoke; it has not been run on the Mac.

### Four GPU data parallel labeling (recommended)

Use `label_pairs_4gpu.sh` for four independent base-model replicas, each TP=1.
The coordinator prepares paired inputs once, partitions the 2,240 jobs by fixed
index modulo four (**560 jobs per GPU**), then merges only after all workers
succeed. Shared questions still have exactly one job. Each worker writes disjoint
per-job artifacts. Interrupted runs reuse completed artifacts; a worker failure
stops the remaining workers and prevents an incomplete final export.

Within an allocation containing four GPUs:

```bash
git pull --ff-only
export REPAIR_DIR=analysis_results/validity_repair_sol_sync_full_v1
export LABEL_MODEL=Qwen/Qwen3-4B-Base
export LABEL_BATCH_SIZE=16
export PAIR_LIMIT=8
export LABEL_OUTPUT_DIR=analysis_results/validity_repair_labels_4gpu_smoke8_v1
bash methods/validity_repair/label_pairs_4gpu.sh --gpus 0,1,2,3
cat "$LABEL_OUTPUT_DIR/analysis/report.md"

# Full run after smoke:
export PAIR_LIMIT=0
export LABEL_OUTPUT_DIR=analysis_results/validity_repair_labels_4gpu_full_v1
bash methods/validity_repair/label_pairs_4gpu.sh --gpus 0,1,2,3
```

Use your allocation's actual device IDs. Without `--gpus`, the launcher uses
`LABEL_GPU_IDS`, then inherited `CUDA_VISIBLE_DEVICES`, then `0,1,2,3`. GPU UUIDs
are accepted. Each worker sees only its assigned device. `LABEL_TP_SIZE` is ignored
by this entry point because each replica always uses one GPU. You may run
`--prepare-only` to check input without loading models. Use a new output directory
when switching between single-worker and four-worker execution.

Progress is saved separately in `logs/worker_0.log` through `worker_3.log`:

```bash
tail -f "$LABEL_OUTPUT_DIR"/logs/worker_*.log
```

Sampling parameters, prompts, majority logic, pair filtering, and final filenames
are the same as the single-worker entry point. The coordinator does not submit a
Slurm allocation; start it inside your existing GPU allocation.
