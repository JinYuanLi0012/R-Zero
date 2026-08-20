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
`mathruler.grade_answer()` runs first; locally incorrect responses go to the
existing style of Yes/No API equivalence recheck using the complete model
response, including responses that omitted the required box.
An explicit final `INVALID` prediction on a VALID row remains wrong without an
API call. The API is never asked to decide whether a problem is valid.

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
VALIDITY_TERRA_GPU_IDS=0 \
VALIDITY_TERRA_TENSOR_PARALLEL_SIZE=1 \
bash methods/validity_rl/evaluate_terra_validation.sh
```

The wrapper preflights every requested merged checkpoint and then evaluates
`Qwen/Qwen3-4B-Base`, step 5, step 10, and step 15 sequentially with the same
297 examples and settings. A single A100 is sufficient for Qwen3-4B and is the
recommended launch configuration above. Using one GPU instead of four changes
only the inference device count; the prompt, pass@1 generation, scoring, and
results are unchanged. Useful overrides are:

```bash
# Print the commands without loading a model or calling the API.
VALIDITY_TERRA_DRY_RUN=1 \
bash methods/validity_rl/evaluate_terra_validation.sh

# Evaluate only Base, or only selected checkpoints.
VALIDITY_TERRA_MODELS="base" \
VALIDITY_TERRA_GPU_IDS=0 \
VALIDITY_TERRA_TENSOR_PARALLEL_SIZE=1 \
bash methods/validity_rl/evaluate_terra_validation.sh

VALIDITY_TERRA_MODELS="5 10 15" \
VALIDITY_TERRA_GPU_IDS=0 \
VALIDITY_TERRA_TENSOR_PARALLEL_SIZE=1 \
bash methods/validity_rl/evaluate_terra_validation.sh
```

The wrapper's unset defaults remain GPUs `0,1,2,3` with tensor parallel size 4.
On servers where `env_rzero.sh` places `TMPDIR` on the shared `/engrfs` file
system, four vLLM ranks can race during Triton/TorchInductor compilation and
fail with `OSError: [Errno 16] Device or resource busy` while renaming cache
files. Prefer the single-GPU command above. If tensor parallelism is required,
an optional workaround is to keep compilation caches on node-local storage:

```bash
export TMPDIR="/tmp/rzero-${USER}"
export TORCHINDUCTOR_CACHE_DIR="${TMPDIR}/torchinductor"
export TRITON_CACHE_DIR="${TMPDIR}/triton"
mkdir -p "${TORCHINDUCTOR_CACHE_DIR}" "${TRITON_CACHE_DIR}"
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

## Terra majority-vote architecture simulation

`simulate_terra_majority_vote.py` is an independent inference experiment for
choosing between two possible future R-Zero integrations. It does not modify
VERL, training, or the R-Zero loop:

- **Two-stage 8+8:** eight validity-aware rollouts vote INVALID versus
  non-INVALID. More than four INVALID votes stops with `INVALID`, exactly four
  produces `TIE`, and fewer than four runs eight additional rollouts using the
  original pure-math R-Zero prompt. The second-stage boxed answers are clustered
  by R-Zero mathematical equivalence before selecting the majority answer.
- **One-stage 16:** sixteen validity-aware rollouts vote together. More than
  eight INVALID votes stops with `INVALID`, exactly eight produces `TIE`, and
  fewer than eight discards INVALID outputs and clusters the remaining boxed
  mathematical answers.

Validity-vote ties are never silently assigned to either class. Mathematical
cluster ties retain the earliest representative, matching R-Zero's existing
deterministic `max()` behavior, and are flagged in the per-question artifact.
For Terra-VALID rows with a final majority math answer, scoring exactly matches
the pass@1 Terra protocol: `mathruler.grade_answer` runs first; locally correct
answers are accepted directly, while locally incorrect answers go to the same
API mathematical-equivalence judge for a possible rescue. The judge receives
only the question, Terra canonical answer, and majority prediction, and is
explicitly forbidden from judging problem validity. Terra-INVALID rows are
scored directly from the final INVALID action; `TIE` and missing math answers
fail without an API call. The simulation never calls Terra or changes its
labels.

This is a population-vote experiment, so generation uses R-Zero's sampled
Solver settings rather than the deterministic pass@1 settings above:

```text
temperature=1.0, top_p=1.0, top_k=40, max_tokens=4096
```

After merging steps 5, 10, and 15, run all four models in parallel, one model
per GPU:

```bash
cd /storage1/jiaxinh/Active/jinyuan/R-zero
git pull --ff-only
source env_rzero.sh

export STORAGE_PATH=/engrfs/project/jiaxinh/jinyuan/R-zero-storage
RUN_ROOT="${STORAGE_PATH}/models/qwen3_4b_validity_rl_terra_v1"
export VALIDITY_VOTE_EVAL_TAG="terra_vote_$(date +%Y%m%d_%H%M%S)"
read -rsp "OpenAI API key: " OPENAI_API_KEY
echo
export OPENAI_API_KEY

VALIDITY_VOTE_GPU_IDS=0,1,2,3 \
VALIDITY_VOTE_TENSOR_PARALLEL_SIZE=1 \
bash methods/validity_rl/simulate_terra_majority_vote.sh
```

The assignment follows `VALIDITY_VOTE_MODELS` order, so the default launch is
GPU 0 = Base, GPU 1 = step 5, GPU 2 = step 10, and GPU 3 = step 15. Each vLLM
process uses tensor parallel size 1; parallelism changes only scheduling, not
the sampling or scoring protocol. The wrapper waits for every process and
builds the comparison only if all four succeed. Per-model logs are written to
`<output-root>/logs/`.

Each process also receives an isolated node-local compile cache under
`/tmp/rzero_validity_vote_<tag>/<model>`. This avoids the Triton/TorchInductor
`Device or resource busy` failures seen when multiple ranks compile into a
shared `/engrfs` cache. Override its parent with `VALIDITY_VOTE_CACHE_ROOT` if
needed.

The full run generates many more responses than pass@1. Run one model first if
desired, while retaining the formal 8+8 and 16-rollout protocol:

```bash
VALIDITY_VOTE_MODELS="base" \
VALIDITY_VOTE_GPU_IDS=0 \
VALIDITY_VOTE_TENSOR_PARALLEL_SIZE=1 \
bash methods/validity_rl/simulate_terra_majority_vote.sh

# Print all resolved commands without loading a model.
VALIDITY_VOTE_DRY_RUN=1 \
bash methods/validity_rl/simulate_terra_majority_vote.sh
```

Useful overrides are `VALIDITY_VOTE_MODELS`, `VALIDITY_VOTE_GPU_IDS`,
`VALIDITY_VOTE_TENSOR_PARALLEL_SIZE`, `VALIDITY_VOTE_SEED`,
`VALIDITY_VOTE_BATCH_SIZE`, `VALIDITY_VOTE_MAX_TOKENS`,
`VALIDITY_VOTE_RUN_ROOT`, `VALIDITY_VOTE_OUTPUT_ROOT`,
`VALIDITY_VOTE_CACHE_ROOT`, `RECHECK_JUDGE_MODEL`,
`RECHECK_REASONING_EFFORT`, and `RECHECK_MAX_COMPLETION_TOKENS`. Keep
`VALIDITY_VOTE_MAX_TOKENS=4096` and the same judge configuration as the pass@1
Terra evaluation for formal comparisons. `VALIDITY_VOTE_SKIP_API_RECHECK=1`
enables a local-only diagnostic, but its accuracy is not formally comparable.

Artifacts are stored under:

```text
${RUN_ROOT}/evaluations/terra_vote_simulation_<tag>/base/results.jsonl
${RUN_ROOT}/evaluations/terra_vote_simulation_<tag>/base/summary.json
${RUN_ROOT}/evaluations/terra_vote_simulation_<tag>/step_5/{results.jsonl,summary.json}
${RUN_ROOT}/evaluations/terra_vote_simulation_<tag>/step_10/{results.jsonl,summary.json}
${RUN_ROOT}/evaluations/terra_vote_simulation_<tag>/step_15/{results.jsonl,summary.json}
${RUN_ROOT}/evaluations/terra_vote_simulation_<tag>/comparison.json
${RUN_ROOT}/evaluations/terra_vote_simulation_<tag>/comparison.md
```

Each question records both methods' extracted rollout outputs, INVALID vote
counts, validity decision, answer clusters, final prediction, and correctness.
For final math predictions it also records the local score and, when a locally
incorrect result triggers recheck, the API verdict and any API error.
Each model summary reports final outcome accuracy, valid-math accuracy, INVALID
recall and precision, false-INVALID rate, tie rate, average INVALID votes, vote
histograms for VALID and INVALID gold, rollout cost, and V1–V5 breakdowns.
`comparison.md` contains the requested overall and per-checkpoint tables.

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
