# Clean-formal V1–V4 question audit

This pipeline samples globally unique questions from selected Phase-B rounds in
`qwen3_4b_validity_rzero_clean_formal_v1` and measures two things independently:

1. question validity under the strict Terra A–F rubric;
2. correctness of the source nine-solver majority answer on Terra-VALID questions.

It uses `gpt-5.6-terra`, high reasoning, structured Responses, and eight concurrent
standard Responses API calls by default. This avoids the Batch queue and prints
continuous per-pass progress. It only analyzes data; it does not alter the source
files, publish a dataset, or start training.

## Protocol

Sampling is fixed before annotation with seed 42. Question text is normalized and
globally deduplicated in V1→V4 order; the earliest round and first source row own a
duplicate. Each round then contributes exactly 300 uniformly sampled unique
questions. Duplicate and conflicting-answer counts are recorded in the manifest.
Empty question strings are retained as malformed questioner outputs (and globally
deduplicated like any other text) rather than silently removed.

The three dependent annotation passes are:

1. **Validity:** opaque ID + question only. A means VALID; B–F mean INVALID.
2. **Canonical answer:** only A questions; opaque ID + question only. Terra solves
   independently and verifies the answer without seeing source votes or answers.
3. **Majority judge:** only verified VALID questions with a non-empty source
   majority answer. It sees opaque ID, question, canonical answer, and majority
   answer, but no round, score, vote count, source validity result, or filter flag.

This ordering prevents the source majority answer from anchoring either validity
or canonical-answer generation. Missing source answers are handled locally and are
not sent to Pass 3.

## Run on Linux

From the repository root:

```bash
git pull --ff-only
export OPENAI_API_KEY="..."

export DATA_DIR=/engrfs/project/jiaxinh/jinyuan/R-zero-storage/rzero_runs/qwen3_4b_validity_rzero_clean_formal_v1/datasets
export OUTPUT_DIR=analysis_results/clean_formal_v1_question_audit_terra_sync_300
export PER_ROUND=300
export ROUNDS=1,2,3,4
export SEED=42
export ANNOTATION_MODE=sync
export MODEL=gpt-5.6-terra
export CONCURRENCY=8

bash methods/clean_formal_question_audit/run.sh
```

To annotate only 200 V5 questions after an earlier V1–V4 run, use a separate
output directory:

```bash
export OUTPUT_DIR=analysis_results/clean_formal_v1_question_audit_v5_terra_sync_200
export ROUNDS=5
export PER_ROUND=200
export ANNOTATION_MODE=sync
export MODEL=gpt-5.6-terra
export CONCURRENCY=64

bash methods/clean_formal_question_audit/run.sh
```

`ROUNDS=5` still scans V1–V4 locally before sampling, so V5 questions duplicated
from earlier rounds are excluded. Only the 200 selected V5 questions are sent to
the API; the preceding rounds are not re-annotated.

For a 40-question smoke run, use a fresh output directory and `PER_ROUND=10`.
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

## Metrics

The report gives overall and per-round Terra valid rates, the source validity-vote
confusion matrix, and majority-answer accuracy. Two accuracy definitions are kept
separate:

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
