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

### Frozen history-context Questioner prompt pilot

`incontext_pilot/run_prompt_pilot.py` provides a generation-only matched P0/P1
test of whether three negative references from a lambda-1 Round-4 archive steer
one frozen Questioner away from historical templates. It is independent of the
semantic-MC reward treatment and does not modify the training path. See
`incontext_pilot/README.md` for the fixed inputs, command, and artifact checks.

### Semantic Monte Carlo diversity treatment

Set `VALIDITY_RZERO_DIVERSITY_MODE=semantic_mc` to replace only the validity
Questioner diversity term. For each Questioner batch, a fixed-seed shared panel
of up to 128 sample indices is drawn without text deduplication. The frozen
`Qwen/Qwen3-4B-Base` judge uses the formal recurring-exercise prompt and the
unchanged v3-max1024 sampling/parser contract for every nonself candidate/panel
pair. Question A is always the candidate and Question B the panel reference.
Strict-parse failures are retried once and final failures are removed from both
numerator and denominator:

```text
semantic_penalty = SAME_TYPE / successfully_parsed_nonself_comparisons
questioner_reward = questioner_base_reward - semantic_penalty
```

GPU 2/3 continue to host the Solver. The reward is launched asynchronously with
Questioner old/ref log-prob computation on GPU 0/1. A per-step barrier prevents
the frozen judge from borrowing GPU 0/1 until old/ref log-probs (and values, if
configured) have completed and their weights have been offloaded. The Solver
then stops and releases GPU 2/3; by default four single-GPU frozen-base workers
run on GPU 0/1/2/3 without stopping the small persistent Ray workers on GPU 0/1.
All semantic subprocesses exit before reward returns, the Solver restarts and
passes health checks, and only then can actor update begin. Failures clean up
semantic workers and still attempt the Solver restart.

The per-step barrier is an optional reward-data field: training batches carry
it, while validation batches may omit it. In semantic mode, the Questioner
configuration's explicit `trainer.val_freq=-1` also disables the otherwise
automatic final validation. If semantic validation is explicitly enabled with
`val_freq>0`, its synchronous generated batch runs without a barrier. Baseline
and BLEU modes retain the trainer's original final-validation behavior.

The online worker shares the tested smoke implementation: submissions default
to 8,192 requests, all first-pass batches finish before failures are collected
into large deferred retry batches, and vLLM prefix caching is explicitly
enabled. Candidate/reference orientation and candidate-contiguous sharding let
comparisons for one candidate reuse the fixed instruction plus Question-A token
prefix. Online logs record first-pass/retry call counts and the observed prefix
cache token hit rate when the installed vLLM exposes it.

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
export VALIDITY_RZERO_SEMANTIC_GPU_IDS=0,1,2,3
export VALIDITY_RZERO_SEMANTIC_GPU_MEMORY_UTILIZATION=0.80
export VALIDITY_RZERO_SEMANTIC_WORKER_BATCH_SIZE=8192
```

`VALIDITY_RZERO_SEMANTIC_GPU_IDS` is deliberately separate from
`VLLM_GPU_IDS=2,3`: the latter remains the Solver topology. The 0.80 semantic
memory fraction leaves headroom for the roughly 2--3 GB persistent Ray process
on each Questioner GPU. Set the semantic GPU list back to `2,3` to reproduce the
previous two-replica execution topology; the reward formula and judge protocol
are identical.

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
