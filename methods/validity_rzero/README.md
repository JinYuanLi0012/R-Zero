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
