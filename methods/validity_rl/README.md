# Validity-aware GRPO mid-training

This method gives `Qwen/Qwen3-4B-Base` the option to finish normal mathematical
solutions with `\boxed{answer}` and genuinely invalid problems with
`\boxed{INVALID}`. It reuses R-Zero's existing dataset loader, rollout workers,
GRPO advantage computation, reference-policy KL loss, reward manager, and
checkpoint manager. It does not add a classifier or an evaluation pipeline.

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
