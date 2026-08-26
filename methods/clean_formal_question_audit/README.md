# Clean-formal V1–V5 raw-output question audit

This pipeline samples original output rows from selected Phase-B rounds in
`qwen3_4b_validity_rzero_clean_formal_v1` and measures two things independently:

1. question validity under the strict Terra A–F rubric;
2. correctness of the source nine-solver majority answer on Terra-VALID questions.

It uses `gpt-5.6-terra`, high reasoning, structured Responses, and 64 concurrent
standard Responses API calls by default. This avoids the Batch queue and prints
continuous per-pass progress. It only analyzes data; it does not alter the source
files, publish a dataset, or start training.

## Protocol

Sampling is fixed before annotation with seed 42. The sampling unit is one original
row from `round_{n}_phase_b.jsonl`. Each of V1–V5 contributes exactly 200 rows,
sampled uniformly without replacement within that round. There is no within-round
or cross-round question deduplication: repeated questions participate once per
source occurrence and can appear multiple times in the 1,000-row sample. Empty
question strings are likewise retained as raw questioner outputs.

`SAMPLING_PROTOCOL` selects the sampling population:

- `raw_row` (default): no deduplication; every source occurrence is eligible.
- `unique_question`: normalize question text, deduplicate within and across rounds
  in round order, and assign each repeated question to its earliest round and first
  source row before sampling. This is the novel/unique-question analysis protocol.

Each ID contains round, original zero-based source index, and a short question hash,
for example `q_v5_000012_ab12cd34`. This keeps repeated question rows distinct. The
Terra validity and answer inputs contain exactly `id` and `question`; source answer,
votes, score, filter state, and other metadata remain hidden.

The three dependent annotation passes are:

1. **Validity:** opaque ID + question only. A means VALID; B–F mean INVALID.
2. **Canonical answer:** only A questions; opaque ID + question only. Terra solves
   independently and verifies the answer without seeing source votes or answers.
3. **Majority judge:** only verified VALID rows with a non-empty source
   majority answer. It sees opaque ID, question, canonical answer, and majority
   answer, but no separate round field, score, vote count, source validity result,
   or filter flag.

This ordering prevents the source majority answer from anchoring either validity
or canonical-answer generation. Missing source answers are handled locally and are
not sent to Pass 3.

## Run on Linux

From the repository root:

```bash
git pull --ff-only
export OPENAI_API_KEY="..."

export DATA_DIR=/engrfs/project/jiaxinh/jinyuan/R-zero-storage/rzero_runs/qwen3_4b_validity_rzero_clean_formal_v1/datasets
export OUTPUT_DIR=analysis_results/clean_formal_v1_v5_raw_row_audit_terra_sync_200
export PER_ROUND=200
export ROUNDS=1,2,3,4,5
export SEED=42
export ANNOTATION_MODE=sync
export MODEL=gpt-5.6-terra
export CONCURRENCY=64

bash methods/clean_formal_question_audit/run.sh
```

For the ten-round `r10_initstep15_v1` unique-question experiment:

```bash
export DATA_DIR=/engrfs/project/jiaxinh/jinyuan/R-zero-storage/rzero_runs/qwen3_4b_validity_rzero_clean_formal_r10_initstep15_v1/datasets
export OUTPUT_DIR=analysis_results/clean_formal_r10_initstep15_v1_unique_question_terra_sync_200
export ROUNDS=1,2,3,4,5,6,7,8,9,10
export PER_ROUND=200
export SEED=42
export SAMPLING_PROTOCOL=unique_question
export MODEL=gpt-5.6-terra
export ANNOTATION_MODE=sync
export CONCURRENCY=64

bash methods/clean_formal_question_audit/run.sh
```

The unique-question manifest records `sampling_unit=unique_question` and
`deduplication=normalized_question_text_within_and_across_rounds`.

To annotate only V5, select just that round and still use a new output directory:

```bash
export OUTPUT_DIR=analysis_results/clean_formal_v1_v5_raw_row_audit_v5_only_terra_sync_200
export ROUNDS=5
export PER_ROUND=200
export ANNOTATION_MODE=sync
export MODEL=gpt-5.6-terra
export CONCURRENCY=64

bash methods/clean_formal_question_audit/run.sh
```

Because the protocol does not deduplicate, `ROUNDS=5` reads and samples V5 directly;
V5 questions that also appeared in earlier rounds remain eligible.

For a 50-question smoke run, use a fresh output directory and `PER_ROUND=10`.
Rerunning the same command with the same model and output directory reuses completed
per-question artifacts. Each pass prints completed/total plus complete, uncertain,
and failed counts. `CONCURRENCY` can be lowered if the project encounters API rate
limits.

The former discounted Batch path remains available as an explicit fallback:

```bash
export ANNOTATION_MODE=batch
bash methods/clean_formal_question_audit/run.sh
```

Use a new `OUTPUT_DIR` when switching model or mode for an existing run. Standard
Responses calls do not receive the Batch discount; the default instead saves cost
by using the lower-cost Terra model and saves wall-clock queue time through direct
concurrent calls.

## Relationship to the earlier deduplicated audit

Existing outputs produced by commits before this raw-row protocol are preserved.
They sampled novel/unique questions after within- and cross-round deduplication and
remain useful as a unique-question analysis. They must not be interpreted as the
questioner's actual per-round raw-output validity rate. Never reuse one of those
output directories for this protocol: the artifact IDs and sampling population are
different.

## Metrics

The report gives overall and per-round raw-output Terra valid rates, the source
validity-vote confusion matrix, and majority-answer accuracy. Because duplicate
rows are retained, every metric is occurrence-weighted. Two accuracy definitions
are kept separate:

- **Strict accuracy:** correct / every Terra-VALID question with a verified
  canonical reference. Missing or unjudgeable majority answers are not correct.
- **Judged-answer accuracy:** correct / successfully judged present answers. This
  excludes missing answers and judge failures, so coverage is reported beside it.

Accuracy is also stratified by the original solver support score and whether the
row passed the original R-Zero filter. INVALID questions are excluded from answer
accuracy because they do not have a well-defined correct mathematical answer.

The output directory contains:

```text
sampled_questions.jsonl
terra_blind_input.jsonl
majority_blind_input.jsonl
terra_raw_results.jsonl
annotated_sample.jsonl
failed_or_uncertain.jsonl
prepare_manifest.json
annotation_manifest.json
manifest.json
analysis/dataset_statistics.json
analysis/report.md
artifacts/{validity,answer,majority}/*.json
batch/{validity,answer,majority}/{state.json,input_*.jsonl,output_*.jsonl,errors_*.jsonl}  # Batch mode only
```

`sampled_questions.jsonl` and `annotated_sample.jsonl` retain source vote metadata
for offline analysis. The two blind input files are the exact data exposed to the
model at their respective stages.
