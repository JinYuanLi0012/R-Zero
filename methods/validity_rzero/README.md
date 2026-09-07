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

### Frozen LOPE Questioner prompt pilot

`frozen_lope_pilot/run_frozen_lope_pilot.py` provides the generation-only
paired 8,000/8,000 P0/PLOPE test on the frozen Semantic-MC Round-2 Questioner.
Every treatment request receives an independent exact 100--300 Qwen-token
python-lorem-compatible prefix before a fixed boundary and the original prompt. Generation
seeds and all decoding settings are paired. The output directly reports
numeric-normalized repeated-template share, surface duplicate share, Top-5
normalized-template mass, and parse success. It does not train or call a
Solver. Four independent single-GPU vLLM workers are used by default; paired
fixed/LOPE requests always remain on the same worker. The exact 63-word pool
and shuffle behavior are vendored, so no new runtime package is required. See
`frozen_lope_pilot/README.md` for the Linux command and artifacts.

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

### Semantic novelty-gate experiment

`VALIDITY_RZERO_DIVERSITY_MODE=semantic_novelty_gate` is an independent,
opt-in hard-gate treatment. It does not alter `semantic_mc`: instead of one
shared 128-reference panel and a continuous density penalty, every Questioner
candidate deterministically samples its own K nonself sample indices from the
current generation batch. Text is not deduplicated, so identical text at a
different sample index remains a valid comparison. The default is K=8, a
one-hit rejection threshold, and seed 43. Set
`VALIDITY_RZERO_NOVELTY_MIN_SAME_HITS=2` to require two successfully parsed
`SAME_TYPE` votes before rejection.

The frozen judge, formal recurring-exercise prompt, candidate-to-reference
orientation, v3-max1024 generation contract, strict parser, deferred one-retry
policy, large submission batches, prefix cache, and four-GPU service handoff
are exactly the existing semantic protocol. Final parse failures fail open for
their individual comparisons. The binary gate and Questioner reward are:

```text
novelty = 0  if same_count >= VALIDITY_RZERO_NOVELTY_MIN_SAME_HITS
novelty = 1  otherwise

INVALID: questioner_reward = 0.5 - invalid_votes / 9  (default: legacy)
VALID:   questioner_reward = novelty * R_frontier
Questioner format failure: questioner_reward = -1
```

Novelty is computed once from each generated question and never from Solver
responses, validity votes, or pure-math rollouts. The Solver and novelty paths
meet only when the final Questioner reward is composed. Existing GRPO grouping,
advantage calculation, and actor update remain unchanged.

The existing reward/W&B path records validity pass rate, novelty pass rate
among valid candidates, valid-and-novel rate, mean SAME hits, semantic parse
failure rate, and survivor counts based on the batch's real `uid` prompt/group
identifier. `zero_survivor_grpo_group_rate` counts groups with no VALID + novel
candidate; it is not a zero-advantage metric. A group can still have unequal
rewards because of INVALID or format-failure penalties.

Recommended experiment-specific settings are:

```bash
export VALIDITY_RZERO_DIVERSITY_MODE=semantic_novelty_gate
export VALIDITY_RZERO_NOVELTY_K=8
export VALIDITY_RZERO_NOVELTY_MIN_SAME_HITS=1
export VALIDITY_RZERO_NOVELTY_SEED=43

export VALIDITY_RZERO_SEMANTIC_MODEL=Qwen/Qwen3-4B-Base
export VALIDITY_RZERO_SEMANTIC_LOCAL_FILES_ONLY=1
export VALIDITY_RZERO_SEMANTIC_GPU_IDS=0,1,2,3
export VALIDITY_RZERO_SEMANTIC_GPU_MEMORY_UTILIZATION=0.80
export VALIDITY_RZERO_SEMANTIC_WORKER_BATCH_SIZE=8192
```

`VALIDITY_RZERO_SEMANTIC_PANEL_SIZE` is intentionally ignored in this mode.
Changing it cannot change novelty K.

### K8 INVALID-zero reward ablation

The only algorithmic change in this opt-in experiment is the final Questioner
reward for an INVALID decision. Select it with:

```bash
export VALIDITY_RZERO_NOVELTY_INVALID_REWARD=zero
```

This parameter is read only when validity is enabled and the diversity mode is
`semantic_novelty_gate`. Its default is `legacy`; other diversity modes and pure
R-Zero ignore it. Existing K8/1, K16/1 and K16/2 experiments remain reproducible.

| Questioner outcome | `legacy` (default) | `zero` |
|---|---:|---:|
| INVALID, at least 5 of the same 9 votes | `0.5 - invalid_votes / 9` | `0` |
| VALID + novel | `math_frontier_score` | unchanged |
| VALID + redundant | `0` | unchanged |
| Questioner format parsing failure | `-1` | unchanged |

The Solver, prompts, nine-vote validity decision (4/9 remains VALID, 5/9 becomes
INVALID), frozen judge, K references, successful SAME_TYPE hit threshold,
sampling seeds, retry/fail-open protocol and GPU scheduling are unchanged.
GRPO advantage computation, KL, learning rate, update budgets, Phase B filtering,
Terra replay and Solver rewards are also unchanged. There is no advantage mask,
Questioner reset, memory, or deduplication in this ablation.

The experiment tests removing the ordering INVALID < VALID-but-redundant.
Because format failures still score -1, zero-reward rejected questions can
still have positive group-relative advantage. This is not an all-failures-zero
multiplicative gate, and improved downstream performance is not assumed.

For auditing, the original `questioner_base_reward`, `validity_penalty`, and
votes are retained. Per-question logs include `novelty_invalid_reward` and the
final reward; the existing reward/W&B path also reports the numeric flag
`reward/novelty_invalid_reward_zero` (1 for this ablation, 0 for legacy).
Startup prints `semantic novelty INVALID final reward: zero`.

Only `zero` adds `semantic_novelty_invalid_reward=zero` to the run-state
configuration/fingerprint. Legacy omits the new field, preserving old fingerprints
and resume compatibility. A new/old reward mismatch refuses resume in both
directions; use a new `MODEL_ABBR` for the ablation. To resume this new experiment
later, retain `zero` and every original setting, then add `--resume`.

After syncing the code, run this in a fresh Linux shell using the same environment
and credentials as the original K8 experiment. First invocation has no `--resume`:

```bash
cd /storage1/jiaxinh/Active/jinyuan/R-zero
source env_rzero.sh

# Do not reuse a previous run's explicit artifact/checkpoint paths.
unset RZERO_RUN_ROOT VALIDITY_RZERO_ARTIFACT_DIR
unset QUESTIONER_OUTPUT_DIR QUESTIONER_LOAD_CHECKPOINT SOLVER_LOAD_CHECKPOINT
unset VALIDITY_RZERO_DIVERSITY_LAMBDA VALIDITY_RZERO_SEMANTIC_PANEL_SIZE
unset VALIDITY_RZERO_SEMANTIC_PANEL_SEED

export BASE_MODEL=Qwen/Qwen3-4B-Base
export MODEL_ABBR=qwen3_4b_validity_rzero_semantic_novelty_gate_k8_invalidzero_4gpu_v1
export VALIDITY_RZERO_INITIAL_SOLVER=/engrfs/project/jiaxinh/jinyuan/R-zero-storage/models/qwen3_4b_validity_rl_terra_clean_v1/global_step_15/actor/huggingface
export TERRA_REPLAY_DATASET=jinyuan222/rzero-validity-rl-terra-v1-clean-v1
export TERRA_REPLAY_CONFIG=default
export TERRA_REPLAY_RATIO=0.1
export TERRA_REPLAY_SEED=1

export VALIDITY_RZERO_DIVERSITY_MODE=semantic_novelty_gate
export VALIDITY_RZERO_NOVELTY_K=8
export VALIDITY_RZERO_NOVELTY_MIN_SAME_HITS=1
export VALIDITY_RZERO_NOVELTY_SEED=43
export VALIDITY_RZERO_NOVELTY_INVALID_REWARD=zero

export VALIDITY_RZERO_SEMANTIC_MODEL=Qwen/Qwen3-4B-Base
export VALIDITY_RZERO_SEMANTIC_LOCAL_FILES_ONLY=1
export VALIDITY_RZERO_SEMANTIC_GPU_IDS=0,1,2,3
export VALIDITY_RZERO_SEMANTIC_GPU_MEMORY_UTILIZATION=0.80
export VALIDITY_RZERO_SEMANTIC_WORKER_BATCH_SIZE=8192
export QUESTIONER_TRAIN_GPU_IDS=0,1
export VLLM_GPU_IDS=2,3
export QUESTION_GPU_IDS=0,1,2,3

# Original K8 update and generation budgets.
export RZERO_NUM_ROUNDS=5
export QUESTIONER_MAX_STEPS=5 QUESTIONER_MERGE_STEP=5
export QUESTIONER_ROLLOUT_BATCH_SIZE=512 QUESTIONER_ROLLOUT_N=4
export QUESTIONER_GLOBAL_BATCH_SIZE=4 QUESTIONER_MAX_RESPONSE_LENGTH=4096
export SOLVER_MAX_STEPS=15 SOLVER_MERGE_STEP=15
export SOLVER_ROLLOUT_BATCH_SIZE=512 SOLVER_MAX_RESPONSE_LENGTH=4096
export SOLVER_GENERATE_SAMPLES=2500
export SOLVER_TOTAL_EPOCHS=100 SOLVER_VAL_FREQ=4
export SOLVER_UPLOAD_MIN_SCORE=0.3 SOLVER_UPLOAD_MAX_SCORE=0.8

bash methods/validity_rzero/run.sh
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
