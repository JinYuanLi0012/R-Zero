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
