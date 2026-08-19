# Validity-aware GRPO mid-training

This method gives `Qwen/Qwen3-4B-Base` the option to finish normal mathematical
solutions with `\boxed{answer}` and genuinely invalid problems with
`\boxed{INVALID}`. It reuses R-Zero's existing dataset loader, rollout workers,
GRPO advantage computation, reference-policy KL loss, reward manager, and
checkpoint manager. It does not add a separate validity classifier. The
independent Terra evaluator documented below adds a held-out validity benchmark
without changing R-Zero's existing math evaluation.

## Dataset mapping

The formal Hugging Face dataset is
`jinyuan222/rzero-validity-rl-terra-v1`, config `default`. It has `train` (1,993
rows: 852 VALID, 1,141 INVALID) and `validation` (297 rows: 121 VALID, 176
INVALID). Both splits contain:

`id`, `round`, `question`, `terra_label`, `terra_validity`,
`canonical_final_answer`, `answer_verified`, `answer_confidence`,
`invalid_type`, `validity_rl_target`, and `split`.

The existing trainer can consume it directly:

- `data.prompt_key=question`
- `data.answer_key=validity_rl_target`
- train data: `...@train` only
- validation data: `...@validation` (reward-only; never used for gradients)

For VALID rows, `validity_rl_target` equals the verified canonical answer. For
INVALID rows, it is exactly `INVALID`. `prepare_dataset.py` checks these
invariants and can export very small local parquet files for the GPU smoke test.

```bash
python3 methods/validity_rl/prepare_dataset.py
```

## Reward

Only the final content returned by mathruler's `extract_boxed_content()` is
examined. Mathematical equivalence uses the same `grade_answer()` as R-Zero's
math reward. The outcome table is fixed:

| Target | Final boxed output | Overall reward |
| --- | --- | ---: |
| VALID | correct math | 1.0 |
| VALID | wrong math | 0.0 |
| VALID | `INVALID` | -0.5 |
| INVALID | `INVALID` | 1.0 |
| INVALID | math | 0.0 |
| either | missing/empty box | -0.1 |

There is no positive format reward. Diagnostic fields are logged by the
existing trainer as batch means: `correct`, `reward_positive`, `reward_zero`,
`reward_false_invalid`, `reward_malformed`, `pred_invalid`, `false_invalid`,
`format_ok`, and `format_failure`. `reward/overall` is the mean optimized
outcome reward. Mixed-reward group rate is intentionally omitted because the
current reward interface does not receive group IDs.

Run deterministic reward tests:

```bash
pytest -q methods/validity_rl/tests/test_validity_reward.py
```

## Minimal GPU smoke test

The smoke test is deliberately one step: two prompts, two rollouts per prompt,
a 256-token response cap, one logged validation generation, console-only
logging, and a checkpoint at step 1. Use the same configured training
environment and GPUs as R-Zero:

```bash
bash methods/validity_rl/tests/gpu_smoke.sh
```

The smoke checkpoint is under
`${STORAGE_PATH}/models/qwen3_4b_validity_rl_smoke/global_step_1` unless
`VALIDITY_SAVE_PATH` is set. Inspect the logged generation and reward before the
formal run; the deterministic tests cover every reward-table branch.

## Formal 15-step run

```bash
bash methods/validity_rl/train_validity_grpo.sh
```

Defaults are GRPO, 512 unique prompts per step, 8 rollouts per prompt,
temperature 1.0, top-p 0.99, 4,096 response tokens, actor global batch 128,
learning rate `1e-6`, reference-policy KL loss coefficient `1e-2`, 15 steps,
and saves every 5 steps. Pre-training and periodic validation are disabled; the
existing trainer performs its final reward-only validation after training.

Formal checkpoints are:

- `${STORAGE_PATH}/models/qwen3_4b_validity_rl_terra_v1/global_step_5`
- `${STORAGE_PATH}/models/qwen3_4b_validity_rl_terra_v1/global_step_10`
- `${STORAGE_PATH}/models/qwen3_4b_validity_rl_terra_v1/global_step_15`

Set `VALIDITY_DRY_RUN=1` to print the fully resolved command. All important
settings have `VALIDITY_*` environment overrides; see
`train_validity_grpo.sh` for their names.

## Terra held-out validity evaluation

`evaluate_terra_validation.py` evaluates the published 297-row `validation`
split as a normal solver task, not as a VALID/INVALID classifier. It renders
the same `validity_solver.jinja` instruction used during training and exactly
matches the original R-Zero math generation protocol:

- one response per question (`n=1`, pass@1)
- `temperature=0.0`
- `max_tokens=4096`
- vLLM generation stopped by the tokenizer EOS token

Only the final boxed content is scored. On Terra-INVALID rows, only a final
normalized `\boxed{INVALID}` is correct. On Terra-VALID rows,
`mathruler.grade_answer()` runs first; only locally incorrect non-empty math
answers go to the existing style of Yes/No API equivalence recheck. The API is
never asked to decide whether a problem is valid.

First merge steps 5, 10, and 15 into Hugging Face format as described below.
Then run Base and all three checkpoints under one timestamped result tag:

```bash
cd /storage1/jiaxinh/Active/jinyuan/R-zero
git pull --ff-only
source env_rzero.sh

export STORAGE_PATH=/engrfs/project/jiaxinh/jinyuan/R-zero-storage
RUN_ROOT="${STORAGE_PATH}/models/qwen3_4b_validity_rl_terra_v1"
read -rsp "OpenAI API key: " OPENAI_API_KEY
echo
export OPENAI_API_KEY

export VALIDITY_TERRA_EVAL_TAG="terra_pass1_$(date +%Y%m%d_%H%M%S)"
bash methods/validity_rl/evaluate_terra_validation.sh
```

The wrapper preflights every requested merged checkpoint and then evaluates
`Qwen/Qwen3-4B-Base`, step 5, step 10, and step 15 sequentially with the same
297 examples and settings. By default it uses GPUs `0,1,2,3` as one vLLM
tensor-parallel group. Useful overrides are:

```bash
# Print the commands without loading a model or calling the API.
VALIDITY_TERRA_DRY_RUN=1 \
bash methods/validity_rl/evaluate_terra_validation.sh

# Evaluate only Base, or only selected checkpoints.
VALIDITY_TERRA_MODELS="base" \
bash methods/validity_rl/evaluate_terra_validation.sh

VALIDITY_TERRA_MODELS="5 10 15" \
bash methods/validity_rl/evaluate_terra_validation.sh

# Use a single GPU instead of the four-GPU default.
VALIDITY_TERRA_GPU_IDS=0 \
VALIDITY_TERRA_TENSOR_PARALLEL_SIZE=1 \
bash methods/validity_rl/evaluate_terra_validation.sh
```

The API judge defaults to the same cost-sensitive configuration used by the
Validity-RL math wrapper: `gpt-5.6-luna`, reasoning effort `none`, and an
eight-token completion cap. Override it with `RECHECK_JUDGE_MODEL`,
`RECHECK_REASONING_EFFORT`, and `RECHECK_MAX_COMPLETION_TOKENS`. Setting
`VALIDITY_TERRA_SKIP_API_RECHECK=1` is available for a local-only diagnostic,
but that run no longer follows the full R-Zero recheck protocol.

Results are written under the formal model run root:

```text
${RUN_ROOT}/evaluations/terra_validation_<tag>/base/results.jsonl
${RUN_ROOT}/evaluations/terra_validation_<tag>/base/summary.json
${RUN_ROOT}/evaluations/terra_validation_<tag>/step_5/results.jsonl
${RUN_ROOT}/evaluations/terra_validation_<tag>/step_5/summary.json
${RUN_ROOT}/evaluations/terra_validation_<tag>/step_10/results.jsonl
${RUN_ROOT}/evaluations/terra_validation_<tag>/step_10/summary.json
${RUN_ROOT}/evaluations/terra_validation_<tag>/step_15/results.jsonl
${RUN_ROOT}/evaluations/terra_validation_<tag>/step_15/summary.json
${RUN_ROOT}/evaluations/terra_validation_<tag>/comparison.json
```

Each JSONL line keeps the raw response, extracted final answer, local/API score
decisions, and final correctness. Each summary contains overall accuracy,
VALID math accuracy, INVALID recall and precision, false-INVALID rate, the
requested counts, and a simple per-round breakdown. The wrapper prints the
four-model comparison table when it finishes.

## Checkpoint locations and standard math evaluation

This section is the durable runbook for finding, merging, and evaluating this
experiment after training. The examples assume the Linux storage root used by
the formal run:

```bash
cd /storage1/jiaxinh/Active/jinyuan/R-zero
git pull --ff-only
git rev-parse --short HEAD
source env_rzero.sh

export STORAGE_PATH=/engrfs/project/jiaxinh/jinyuan/R-zero-storage
RUN_ROOT="${STORAGE_PATH}/models/qwen3_4b_validity_rl_terra_v1"
```

### 1. Find the training checkpoints

The resumable FSDP checkpoints are stored at:

```text
${RUN_ROOT}/global_step_5
${RUN_ROOT}/global_step_10
${RUN_ROOT}/global_step_15
```

Each directory should contain `actor/` and `dataloader.pt`. Check them with:

```bash
for step in 5 10 15; do
  CHECKPOINT="${RUN_ROOT}/global_step_${step}"
  test -d "${CHECKPOINT}/actor" || { echo "Missing actor: ${CHECKPOINT}"; exit 1; }
  test -s "${CHECKPOINT}/dataloader.pt" || { echo "Missing dataloader: ${CHECKPOINT}"; exit 1; }
done
```

### 2. Merge each FSDP checkpoint into Hugging Face format

The R-Zero evaluator expects a normal Hugging Face model directory. Run once
for each saved step:

```bash
for step in 5 10 15; do
  python scripts/model_merger.py \
    --local_dir "${RUN_ROOT}/global_step_${step}/actor"
done
```

The merged models are written in place at:

```text
${RUN_ROOT}/global_step_5/actor/huggingface
${RUN_ROOT}/global_step_10/actor/huggingface
${RUN_ROOT}/global_step_15/actor/huggingface
```

Verify that all three contain a config and weights:

```bash
for step in 5 10 15; do
  MODEL_PATH="${RUN_ROOT}/global_step_${step}/actor/huggingface"
  test -s "${MODEL_PATH}/config.json" || { echo "Missing config: ${MODEL_PATH}"; exit 1; }
  compgen -G "${MODEL_PATH}/*.safetensors" >/dev/null || {
    echo "Missing safetensors: ${MODEL_PATH}"
    exit 1
  }
done
```

### 3. Configure the API recheck safely

The benchmark first uses the local math grader. Only locally incorrect samples
are sent to an API judge for a Yes/No mathematical-equivalence recheck. The
Validity-RL wrapper defaults to `gpt-5.6-luna` with reasoning effort `none` and
an eight-token completion cap. The generic R-Zero evaluator keeps its existing
`gpt-4o` default unless these environment variables are supplied.
[GPT-5.6 Luna](https://developers.openai.com/api/docs/models/gpt-5.6-luna)
is OpenAI's cost-sensitive, high-volume tier; consult the
[API pricing page](https://developers.openai.com/api/docs/pricing) for current
rates rather than copying a price into experiment notes.

Do not paste API keys into scripts, README files, Git, or shell history. Set a
fresh key interactively:

```bash
read -rsp "OpenAI API key: " OPENAI_API_KEY
echo
export OPENAI_API_KEY
```

### 4. Run all standard R-Zero math evaluations

The method wrapper validates all merged checkpoints and then evaluates steps 5,
10, and 15 sequentially:

```bash
export VALIDITY_EVAL_TAG="validity_rl_math_$(date +%Y%m%d_%H%M%S)"
bash methods/validity_rl/evaluate_math_checkpoints.sh
```

`EVAL_MATH_ONLY=1` means the seven standard math suites (`math`, `gsm8k`,
`amc`, `minerva`, `olympiad`, `aime2024`, and `aime2025`) while skipping
SuperGPQA, BBEH, and MMLU-Pro. Tasks within one checkpoint are scheduled across
the requested GPUs; checkpoints are evaluated one after another.

Useful overrides:

```bash
# Evaluate only step 5 first.
VALIDITY_EVAL_STEPS="5" \
bash methods/validity_rl/evaluate_math_checkpoints.sh

# Select different GPUs and keep a memorable result tag.
VALIDITY_EVAL_GPU_IDS=4,5,6,7 \
VALIDITY_EVAL_TAG=validity_rl_math_20260819 \
bash methods/validity_rl/evaluate_math_checkpoints.sh

# Print resolved commands without launching vLLM or API requests.
VALIDITY_EVAL_DRY_RUN=1 \
bash methods/validity_rl/evaluate_math_checkpoints.sh
```

The wrapper also accepts `VALIDITY_RUN_ROOT`, `RECHECK_JUDGE_MODEL`,
`RECHECK_REASONING_EFFORT`, and `RECHECK_MAX_COMPLETION_TOKENS`. Keep the default
Luna configuration unless a comparison specifically requires another judge.

### 5. Find logs and scores

Every invocation gets a timestamped evaluation tag so reruns do not silently
append duplicate summaries. Outputs are stored under the model run root:

```text
${RUN_ROOT}/logs/evaluation_<tag>/
${RUN_ROOT}/evaluations/<tag>_step_5/final_results.jsonl
${RUN_ROOT}/evaluations/<tag>_step_10/final_results.jsonl
${RUN_ROOT}/evaluations/<tag>_step_15/final_results.jsonl
```

The raw per-example generations remain in R-Zero's existing location under
`${STORAGE_PATH}/evaluation/`. To print the three summaries after a run:

```bash
for step in 5 10 15; do
  echo "===== Step ${step} ====="
  cat "${RUN_ROOT}/evaluations/${VALIDITY_EVAL_TAG}_step_${step}/final_results.jsonl"
done
```

The wrapper prints the effective tag and every final-results path at startup and
completion. Save that tag in the experiment notes when comparing Base, step 5,
step 10, and step 15.
