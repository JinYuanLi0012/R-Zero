# Clean-formal V1–V4 question audit

This pipeline samples 300 globally unique questions from each Phase-B audit in
`qwen3_4b_validity_rzero_clean_formal_v1` and measures two things independently:

1. question validity under the strict Terra A–F rubric;
2. correctness of the source nine-solver majority answer on Terra-VALID questions.

It uses `gpt-5.6-sol`, high reasoning, structured Responses, and the discounted
OpenAI Batch API by default. It only analyzes data; it does not alter the source
files, publish a dataset, or start training.

## Protocol

Sampling is fixed before annotation with seed 42. Question text is normalized and
globally deduplicated in V1→V4 order; the earliest round and first source row own a
duplicate. Each round then contributes exactly 300 uniformly sampled unique
questions. Duplicate and conflicting-answer counts are recorded in the manifest.
Empty question strings are retained as malformed questioner outputs (and globally
deduplicated like any other text) rather than silently removed.

The three dependent Batch passes are:

1. **Validity:** opaque ID + question only. A means VALID; B–F mean INVALID.
2. **Canonical answer:** only A questions; opaque ID + question only. Sol solves
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
export OUTPUT_DIR=analysis_results/clean_formal_v1_question_audit_300
export PER_ROUND=300
export SEED=42

bash methods/clean_formal_question_audit/run.sh
```

For a 40-question smoke run, use a fresh output directory and `PER_ROUND=10`.
Rerunning the same command with the same output directory resumes saved Batch IDs,
downloads completed output, and retries individual parse/request/uncertain results
up to three attempts. Every poll prints the active batch ID and its own
completed/total/failed counters. A small denominator on a later line is a retry
batch, not the total sample.

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
batch/{validity,answer,majority}/{state.json,input_*.jsonl,output_*.jsonl,errors_*.jsonl}
```

`sampled_questions.jsonl` and `annotated_sample.jsonl` retain source vote metadata
for offline analysis. The two blind input files are the exact data exposed to the
model at their respective stages.
