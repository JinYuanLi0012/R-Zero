# Validity-aware R-Zero

This integration keeps the original R-Zero math path intact and adds a strict
two-stage validity gate.

## Round flow

Phase A uses nine validity-aware Solver rollouts. An INVALID majority stops the
math path and gives the Questioner `0.5 - invalid_votes / 9` before the existing
similarity penalty. A VALID decision starts a fresh set of ten pure-math
rollouts and uses the original R-Zero frontier reward.

Phase B also uses nine validity-aware rollouts. INVALID-majority questions are
discarded. VALID questions start a fresh set of nine pure-math rollouts and use
the original answer clustering, pseudo-answer, and score-range filter.

The mixed Solver dataset tags generated rows with `source=rzero` and replay
rows with `source=terra`. R-Zero rows use the original Solver prompt and math
reward. Terra rows use `validity_solver.jinja` and the existing validity reward.
Only the Terra train split is accepted.

## Running

Set the formal replay dataset and ratio, source the normal R-Zero environment,
then run:

```bash
export TERRA_REPLAY_DATASET=<dataset-id>
export TERRA_REPLAY_RATIO=<formal-ratio>
bash methods/validity_rzero/run.sh
```

The initial Solver defaults to the requested clean-validity Step-10 checkpoint
and can be overridden with `VALIDITY_RZERO_INITIAL_SOLVER`.

### Semantic Monte Carlo diversity treatment

Set `VALIDITY_RZERO_DIVERSITY_MODE=semantic_mc` to replace only the validity
Questioner diversity term. For each Questioner batch, a fixed-seed shared panel
of up to 128 sample indices is drawn without text deduplication. The frozen
`Qwen/Qwen3-4B-Base` v3-max1024 judge compares every nonself candidate/panel
pair. Strict-parse failures are retried once and final failures are removed from
both numerator and denominator:

```text
semantic_penalty = SAME_TYPE / successfully_parsed_nonself_comparisons
questioner_reward = questioner_base_reward - semantic_penalty
```

GPU 2/3 are reused sequentially. The Solver first finishes all validity/math
rollouts and base rewards. Its recorded process groups are then stopped and GPU
release is verified; two single-GPU frozen-base workers run the semantic panel;
they are stopped and release is verified; finally the same Solver services are
restarted and health-checked before the next Questioner step. Failures clean up
workers and still attempt the Solver restart.

The mode is opt-in. `VALIDITY_RZERO_ENABLED=0` retains the original
`min(score, 1-score) - BLEU_cluster_share` path and never imports the semantic
judge. `bleu_lambda5` remains the validity default, while `bleu_legacy` restores
the older unscaled validity BLEU penalty.

Recommended semantic-mode settings are:

```bash
export VALIDITY_RZERO_DIVERSITY_MODE=semantic_mc
export VALIDITY_RZERO_SEMANTIC_MODEL=Qwen/Qwen3-4B-Base
export VALIDITY_RZERO_SEMANTIC_LOCAL_FILES_ONLY=1
export VALIDITY_RZERO_SEMANTIC_PANEL_SIZE=128
export VALIDITY_RZERO_SEMANTIC_PANEL_SEED=43
```

Run CPU tests in the normal R-Zero environment with:

```bash
pytest -q methods/validity_rl/tests/test_validity_reward.py methods/validity_rzero/tests
```

For the one-round GPU smoke, choose a dedicated run name and a candidate count
large enough to survive both filters and still form one complete Solver batch:

```bash
export MODEL_ABBR=qwen3_4b_validity_rzero_smoke
export SOLVER_GENERATE_SAMPLES=<safe-per-shard-count>
bash methods/validity_rzero/tests/gpu_smoke.sh
```

## Implementation principles

Keep the implementation minimal, clear, and maintainable. Solve the confirmed
training-path requirements without adding speculative abstractions or broad
fallback layers. Prioritize correct core training logic, reuse the original
R-Zero code, make only necessary changes, and preserve baseline interfaces and
behavior. Edge cases without a realistic path to affect this experiment should
be recorded for later rather than expanding this integration.
