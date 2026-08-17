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
export CONCURRENCY=4
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
export CONCURRENCY=4
bash methods/validity_rl_terra_dataset/run.sh
```

Defaults are seed 42, model `gpt-5.6`, high reasoning effort, 16,384 maximum
output tokens, three attempts, and four concurrent calls. Override `MODEL` or
`CONCURRENCY` through the environment. The five default sources are:

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

Per-question, per-pass artifacts are written atomically under `artifacts/`.
Rerunning the same command reuses completed artifacts. A changed model, prompt
version, or question is rejected instead of silently mixing annotations; use a
new `OUTPUT_DIR` for a changed experiment.

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
```

`terra_raw_results.jsonl` retains every parsed attempt and the complete raw API
response for audit. Each eligible row has `validity_rl_target`, equal to the
canonical math answer for VALID or the literal `INVALID` for INVALID.
`train.jsonl` and `validation.jsonl` contain no historical R-Zero answer or score.
Do not rebalance or resample after seeing Terra labels.
