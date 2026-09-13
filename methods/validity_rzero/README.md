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

### Solver negative-only GRPO on the original K8 baseline

`run_solver_negative_k8.sh` starts a separate experiment named
`qwen3_4b_validity_rzero_semantic_novelty_gate_k8_solver_negative_4gpu_v1`.
It fixes the original K8 Questioner settings: 512 prompts x 4 rollouts,
global nonself K=8 references, rejection after one SAME_TYPE hit,
VALID reward `novelty * frontier`, and INVALID reward `0.5 - invalid_votes / 9`.
It uses the clean-validity Step-15 initial Solver and 10% Terra replay.
The candidate pool and Questioner reward implementation are unchanged.

Only Solver task-gradient routing changes, via `SOLVER_NEGATIVE_ONLY=1`:

1. Compute the original full-group GRPO advantages from unchanged rewards.
2. For each `source=rzero` group (identified by uid after token balancing),
   count current rollouts mathematically matching the stored pseudo-answer.
3. If none match, set the entire group's task advantages to zero, including
   any advantages arising from the 10% format reward.
4. Otherwise, keep only unmatched rollouts with **original advantage < 0**.
   All-matching groups consequently have zero task advantages as well.
5. Leave Terra advantages unchanged. Do not re-normalize advantages or change
   response masks, batch size, PPO clipping, or loss denominators.

All samples retain the existing separate reference `low_var_kl` loss with
coefficient **0.01**. Zero task advantage does not imply zero KL gradient or
that the model's probabilities stay fixed. This is not a TTPO reproduction:
there is no OPD/OPSD teacher, token selection, new vote, or replacement label.
Phase B currently stores labels from **nine** pure-math votes; training still
draws **five** new rollouts per question. Both counts remain unchanged.

The flag defaults to zero and is passed only by `scripts/solver_train.sh`.
When enabled, the pipeline fingerprint adds
`solver_gradient_policy=negative_only_zero_agree_skip_full_kl_v1`.
Legacy fingerprints are unchanged; switching treatment when resuming is rejected.

In a fresh Linux shell, with the usual credentials and environment:

```bash
cd /storage1/jiaxinh/Active/jinyuan/R-zero
git pull --ff-only
source env_rzero.sh
bash methods/validity_rzero/run_solver_negative_k8.sh
```

For an interrupted run, use the same script with `--resume`. The script pins
the experiment settings and clears inherited checkpoint/artifact paths; it
does not continue the old K8 experiment. It uses the usual five-round pipeline.

The launcher also sets `SOLVER_EVAL_DUAL=1`: after each merged Solver checkpoint,
the pipeline runs the existing `evaluation/evaluate_models.py` math suite twice,
first with `--judge-prompt-mode rzero-original`, then with `corrected`, using
GPUs 0,1,2,3. These are two separate commands (repeating the CLI option in one
command would only select the last value). Both finish before the next round.
`env_rzero.sh` supplies the `/engrfs` storage and Hugging Face cache paths;
the launcher sets `RECHECK_LOCAL_TMP_ROOT=/tmp` and `RECHECK_STARTUP_TIMEOUT=3600`.

Each mode's latest successful `summary.csv` and `summary.md` are stored under
`$STORAGE_PATH/rzero_runs/$MODEL_ABBR/evaluations/solver_vN/<mode>/`.
Unique `math_<mode>_<id>/` subdirectories retain the manifest, seven benchmark
scores, and evaluator logs; the existing evaluator also copies completed scores
beside the exact merged checkpoint. Failed attempts and their logs are retained.
Each mode has its own completion marker: an evaluation failure stops the pipeline,
and `--resume` skips trained checkpoints and completed modes, rerunning only the
unfinished mode before proceeding. An incomplete mode restarts its evaluation,
not training. Enabling this evaluation option does not change training fingerprints,
so it can be added to an already-started negative-only run on resume. Other launchers
default to `SOLVER_EVAL_DUAL=0` and keep their previous evaluation behavior.

Useful per-step metrics (rates below are over R-Zero samples/groups only):

- `solver_negative_only/zero_agree_group_rate`
- `solver_negative_only/all_agree_group_rate`
- `solver_negative_only/kept_negative_rollout_rate`
- `solver_negative_only/kept_negative_rollout_count`
- `actor/kl_loss` and `actor/kl_coef`

Focused CPU verification, without launching GPU training:

```bash
python -m pytest -q methods/validity_rzero/tests/test_solver_negative_only.py \
  methods/validity_rzero/tests/test_solver_negative_launch.py \
  methods/validity_rzero/tests/test_mixed_reward.py
```

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

### Frozen Step-15 validity / no-replay K8 ablation

`bash methods/validity_rzero/run_frozen_validity_k8.sh` selects the original
global K8 treatment (one SAME hit rejects, legacy INVALID negative reward,
no domain curriculum, legacy box filter), with two changes: a fixed validity
judge for both Phase A and Phase B, and zero Terra replay. The mathematical
Solver starts from the same validity-RL Step-15 checkpoint and continues from
its previous round's checkpoint. The Questioner still starts from Base. The
semantic judge remains the unchanged frozen `Qwen/Qwen3-4B-Base`.

The independent general controls are:

```bash
export VALIDITY_RZERO_VALIDITY_JUDGE_MODE=frozen  # default: current_solver
export VALIDITY_RZERO_VALIDITY_JUDGE_MODEL=/path/to/global_step_15/actor/huggingface
export VALIDITY_RZERO_INITIAL_SOLVER="$VALIDITY_RZERO_VALIDITY_JUDGE_MODEL"
export TERRA_REPLAY_RATIO=0
```

`current_solver` retains the original model routing. Nonzero replay retains the
original dataset construction. Zero replay never loads Terra: it keeps all
filtered R-Zero rows, uses their existing source/prompt/reward, and records zero
Terra rows in the receipt. Freezing the judge and replay ratio are independent
controls, allowing a frozen-judge experiment with replay as well. Frozen-mode
fields are only added to that run's fingerprint; old fingerprints are unchanged.

Phase A first stops the current Solver services on GPU 2/3, executes fixed-judge
9-vote workers on those GPUs, waits for exit and GPU release, and restarts the
current Solver. The Solver consumes question/model-bound vote records, performs
only the usual math evaluation for VALID questions, and never falls back to
its own validity judgment. Missing/mismatched records fail the run. The existing
old/ref barrier and four-GPU semantic handoff then proceed as before. Phase B
does the fixed-judge prepass on the evaluation GPUs before launching its math
Solver evaluators. No extra GPU is required; model reloads add overhead.

This retains the validity prompt, sampling, nine votes, 5/9 threshold, INVALID
reward, math vote counts, and K8 semantic protocol. Judge weights stay fixed;
sampling remains stochastic. The frontier is the original answer-cluster
majority fraction transformed by `min(p, 1-p)`, not ground-truth accuracy.

In a fresh Linux shell, after sourcing `env_rzero.sh`, first run a one-step
smoke under a separate name (do not run concurrently with another four-GPU job):

```bash
unset MODEL_ABBR
unset RZERO_NUM_ROUNDS QUESTIONER_MAX_STEPS QUESTIONER_MERGE_STEP
unset SOLVER_MAX_STEPS SOLVER_MERGE_STEP SOLVER_GENERATE_SAMPLES
bash methods/validity_rzero/run_frozen_validity_k8.sh --smoke
```

The launcher uses 2,500 generated candidates per GPU, preserving enough data
for the filtered Solver batch. It defaults to checkpoint
`$STORAGE_PATH/models/qwen3_4b_validity_rl_terra_clean_v1/global_step_15/actor/huggingface`.
After smoke succeeds, with the same clean parent-shell configuration:

```bash
bash methods/validity_rzero/run_frozen_validity_k8.sh
```

Default formal run: `qwen3_4b_validity_rzero_k8_frozenstep15_noreplay_v1`.
Default smoke run: `qwen3_4b_validity_rzero_k8_frozenstep15_noreplay_smoke_v1`.
Only use `--resume` to resume the same new experiment. Never reuse an old
experiment's name/checkpoint state for this ablation. The launcher explicitly
sets the original K8 options in its child shell; it does not change the parent's
environment or the behavior of other experiment entrypoints.

Inspect `[validity_rzero][frozen_validity]` for phase/model/invalid-count and
artifact paths; raw nine-vote records and worker logs are kept in
`$STORAGE_PATH/temp_results/frozen_validity_*`. The final dataset receipt must
show `terra_replay_sample_count=0` and `actual_replay_ratio=0`. A fixed-judge
worker failure/timeout is fatal, cleaned up, and reported with log tails;
semantic parse-failure behavior is unchanged.

This is a combined fixed-evaluator/no-replay ablation. Dataset size decreases
when replay is removed; no replacement questions are added. It does not isolate
the individual causal effect of each of those two changes.

Keep the implementation minimal, clear, and maintainable. Solve the confirmed
training-path requirements without adding speculative abstractions or broad
fallback layers. Prioritize correct core training logic, reuse the original
R-Zero code, make only necessary changes, and preserve baseline interfaces and
behavior. Edge cases without a realistic path to affect this experiment should
be recorded for later rather than expanding this integration.

### Balanced domain Questioner

`VALIDITY_RZERO_DOMAIN_MODE=balanced_v1` adds the optional 8-domain / 28-leaf
prompt curriculum to both Questioner GRPO and Phase B generation. Default `none`
keeps existing runs unchanged. It does not change K8 rewards or Terra replay.
See [the protocol and pinned K8 launch script](domain_curriculum/README.md).
