# R-Zero Validity-RL Terra dataset

This directory builds the preregistered V1-V5 dataset for validity-aware GRPO
mid-training. It only constructs and audits data; it does not run GRPO or alter
the source datasets.

The pipeline fixes the sample before annotation, globally deduplicates normalized
question text, and gives Terra only an opaque ID and the question. It never
exposes round, historical score, pseudo-answer, or split. Terra runs two passes:

1. The existing strict A-F rubric from
   `methods/gaussian_population_rzero_epistemic_validation/judge.py`.
2. A fresh solution and canonical-answer verification for A questions only.

By default both passes use `gpt-5.6-sol` through the OpenAI Batch API's
`/v1/responses` endpoint. The validity batch must finish before the A-only answer
batch is constructed. Batch output order is ignored; opaque `custom_id` values
are used for every join.

A maps to `VALID`; B-F map to `INVALID`. An A question enters `train.jsonl` or
`validation.jsonl` only if the second pass returns a non-empty verified answer at
or above the configured confidence threshold (0.8 by default). Other A questions
go to `failed_or_uncertain.jsonl`. Thus the annotated sample is always 2000 train
+ 300 validation, while the RL-eligible files can be smaller.

## 50-question smoke run

From the repository root on Linux:

```bash
export OPENAI_API_KEY=...
# If these private datasets are not already cached, also log in with `hf auth login`
# or export an HF_TOKEN that can read jinyuan222's five source datasets.
export OUTPUT_DIR=analysis_results/validity_rl_terra_dataset_smoke_50
export PER_ROUND=10
export TRAIN_PER_ROUND=8
bash methods/validity_rl_terra_dataset/run.sh
```

This samples 10 questions from each round (8 train and 2 validation), for 50
Terra validity calls plus one answer-verification call per A label. Inspect
`analysis/report.md`, a few raw responses, and every failed/uncertain row before
launching the full run.

## Full run

```bash
export OPENAI_API_KEY=...
export OUTPUT_DIR=analysis_results/validity_rl_terra_dataset_v1
export PER_ROUND=460
export TRAIN_PER_ROUND=400
bash methods/validity_rl_terra_dataset/run.sh
```

Defaults are seed 42, model `gpt-5.6-sol`, Batch mode, high reasoning effort,
16,384 maximum output tokens, three attempts, and a 60-second polling interval.
Override `MODEL` or `BATCH_POLL_SECONDS` through the environment. The terminal
prints each pipeline stage plus the OpenAI batch ID, status, completed count, and
failed count on every poll. The five default sources are:

- `jinyuan222/qwen3_4b_fullrun_authorsettings_solver_v1`
- `jinyuan222/qwen3_4b_fullrun_authorsettings_solver_v2`
- `jinyuan222/qwen3_4b_fullrun_authorsettings_solver_v3`
- `jinyuan222/qwen3_4b_fullrun_authorsettings_solver_v4`
- `jinyuan222/qwen3_4b_fullrun_authorsettings_solver_v5`

For local mirrors or tests, replace all five sources:

```bash
bash methods/validity_rl_terra_dataset/run.sh \
  --source v1=/data/v1.jsonl --source v2=/data/v2.jsonl \
  --source v3=/data/v3.jsonl --source v4=/data/v4.jsonl \
  --source v5=/data/v5.jsonl
```

The question column is detected from `problem`, `question`, or `prompt`; chat
prompts use the final user message. Use `--question-field FIELD` only if the
actual schema differs. Hugging Face revision SHAs and detected fields are stored
in `prepare_manifest.json`.

## Resume and audit behavior

Batch IDs and lifecycle state are written atomically under `batch/`. If the
terminal disconnects, the remote batch continues; rerunning the same command
retrieves the saved batch ID and resumes polling/downloading. Per-question,
per-pass artifacts are written atomically under `artifacts/`. Parse errors,
request errors, expired requests, and unverified answers are resubmitted in a
smaller follow-up batch, up to three attempts. A failed or cancelled entire
batch stops the pipeline for inspection instead of blindly resubmitting it.

A changed model, prompt version, question set, or annotation configuration is
rejected instead of silently mixing annotations; use a new `OUTPUT_DIR` for a
changed experiment. The Batch API completion window is 24 hours per pass, so the
two dependent passes can take up to roughly 48 hours. For debugging only, the old
synchronous path remains available with `ANNOTATION_MODE=sync` and
`CONCURRENCY=4`.

The final directory contains:

```text
sampled_questions.jsonl
terra_blind_input.jsonl
terra_raw_results.jsonl
train.jsonl
validation.jsonl
failed_or_uncertain.jsonl
manifest.json
analysis/dataset_statistics.json
analysis/report.md
artifacts/validity/*.json
artifacts/answer/*.json
batch/validity/state.json
batch/validity/input_*.jsonl
batch/validity/output_*.jsonl
batch/answer/state.json
batch/answer/input_*.jsonl
batch/answer/output_*.jsonl
```

`terra_raw_results.jsonl` retains every parsed attempt and the complete raw API
response for audit. Each eligible row has `validity_rl_target`, equal to the
canonical math answer for VALID or the literal `INVALID` for INVALID.
`train.jsonl` and `validation.jsonl` contain no historical R-Zero answer or score.
Do not rebalance or resample after seeing Terra labels.

## VALID-answer consistency audit

After the full dataset has been finalized, run the independent third-pass audit
to screen all Terra A/VALID answers before using them for reward computation.
The audit reads `terra_raw_results.jsonl`, joins question/round/split metadata
from `sampled_questions.jsonl`, and verifies the expected accounting (2,300 raw,
983 VALID, 973 verified canonical answers, and 10 preexisting unverified).

Only the 973 verified rows are submitted. The exact blind model input is saved
in `audit_input.jsonl` and contains only opaque `id`, `question`, Pass 1
`derived_answer`, and Pass 2 `canonical_final_answer`. Round, split, historical
score/answer, pseudo-answer, labels, and known problem IDs are never sent. The
remaining 10 VALID rows are recorded directly as `PREEXISTING_UNVERIFIED`
suspects, so final accounting still covers all 983 VALID questions.

From the repository root on Linux:

```bash
export OPENAI_API_KEY="..."
export CONSISTENCY_MODEL=gpt-5.6-luna
export CONSISTENCY_OUTPUT_DIR=analysis_results/validity_rl_terra_dataset_v1_answer_consistency_audit_v1

bash methods/validity_rl_terra_dataset/run_answer_consistency_audit.sh \
  analysis_results/validity_rl_terra_dataset_v1
```

The defaults are high reasoning effort, 8,192 maximum output tokens, a 0.8 PASS
confidence threshold, three attempts, and a 60-second poll interval. Override
them with `CONSISTENCY_REASONING_EFFORT`, `CONSISTENCY_MAX_OUTPUT_TOKENS`,
`CONSISTENCY_CONFIDENCE_THRESHOLD`, `CONSISTENCY_MAX_ATTEMPTS`, and
`BATCH_POLL_SECONDS`. If `gpt-5.6-luna` is unavailable, set
`CONSISTENCY_MODEL=gpt-5.6-terra`.

Batch input/output/error files and `batch/state.json` are durable. Rerunning the
same command resumes an already-submitted batch by ID; parse failures and
per-request failures enter smaller retry batches and output order is joined by
`custom_id`. Cached state is rejected if the model, reasoning effort, token
limit, attempt limit, confidence threshold, prompt, question text, either input
answer, or complete audited ID set changes. Use a new output directory for a
changed experiment.

The audit writes:

```text
audit_input.jsonl
audit_results.jsonl
suspect.jsonl
passed.jsonl
preexisting_unverified.jsonl
manifest.json
batch/state.json
batch/input_*.jsonl
batch/output_*.jsonl
batch/errors_*.jsonl
artifacts/q_*.json
analysis/statistics.json
analysis/report.md
```

Only rows satisfying the deterministic PASS rule are placed in `passed.jsonl`:
the question is clear, the canonical answer is correct and responsive, the two
answers do not conflict, deep review is not requested, parsing succeeded, and
confidence meets the threshold. `NOT_COMPARABLE` and a missing derived answer do
not fail an otherwise high-confidence canonical verification. This stage only
reports suspects; it does not modify train/validation files, replace answers,
call Sol, vote, upload a dataset, or start GRPO.
