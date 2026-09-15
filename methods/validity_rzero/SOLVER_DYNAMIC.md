# Solver-only dynamic voting and TTPO token masking

The first-round launcher starts the Solver from `qwen3_4b_validity_rl_terra_clean_v1/global_step_15/actor/huggingface`
and reuses the existing mixed dataset
`$HUGGINGFACENAME/qwen3_4b_validity_rzero_semantic_novelty_gate_k8_solver_negative_4gpu_v1_solver_v1@train`.
It keeps the original first-round questions and Terra rows. It never runs the
Questioner, uploads a replacement dataset, or loads the degraded Solver as its
initial weights. Old pseudo-labels are retained for comparison only.

## Run on Linux

```bash
cd /storage1/jiaxinh/Active/jinyuan/R-zero
git pull --ff-only
source env_rzero.sh
bash methods/validity_rzero/run_solver_dynamic_k8.sh
```

The run name is
`qwen3_4b_validity_rzero_semantic_novelty_gate_k8_solver_dynamic_mask_4gpu_v1`;
the checkpoint experiment appends `_solver_v1`. Uses GPUs 0,1,2,3, one Solver
round with 15 rollout steps, and saves FSDP checkpoints at 3,6,9,12,15 (all five
retained). Step 15 is merged to Hugging Face format and evaluated with both
`rzero-original` and `corrected` judge prompts. Intermediate checkpoints retain
their model/optimizer shards; use the existing `scripts/model_merger.py` if an
intermediate Hugging Face export is needed.

```bash
bash methods/validity_rzero/run_solver_dynamic_k8.sh --resume
```

Resume uses only this experiment's latest saved checkpoint and verifies its
run configuration. If training has completed, it only retries unfinished
evaluation modes. Failed evaluation attempt directories are retained. A fresh
invocation refuses an existing model directory. For another fresh experiment,
set `SOLVER_DYNAMIC_RUN_NAME` to a new name.

## Continue rounds 2–5 after a successful first round

```bash
git pull --ff-only
source env_rzero.sh
bash methods/validity_rzero/continue_solver_dynamic_k8.sh
```

This continues the same experiment name and run directory. Round 2 starts from:

- Solver: `$STORAGE_PATH/models/${RUN}_solver_v1/global_step_15/actor/huggingface`,
  where `RUN` is the dynamic experiment name above.
- Questioner: `$STORAGE_PATH/models/qwen3_4b_validity_rzero_semantic_novelty_gate_k8_solver_negative_4gpu_v1_questioner_v1/global_step_5/actor/huggingface`,
  which generated the questions reused for the first dynamic Solver round.

Each round trains the Questioner using the preceding Solver, prepares a fresh
mixed dataset, trains the Solver from its preceding checkpoint, and evaluates
with both judge modes before advancing. Models are numbered v2 through v5;
round 1 is not repeated. Questioner validity rewards and global novelty K=8
(one matching hit rejects) are unchanged. Solver dynamic voting, negative token
masking, Terra replay, and steps/checkpoint cadence match the first round.

If this continuation is interrupted, use:

```bash
bash methods/validity_rzero/continue_solver_dynamic_k8.sh --resume
```

The continuation has its own pipeline state under the existing run directory;
the first-round launcher's `--resume` only handles round 1. Completed stages
are skipped, interrupted training uses its latest complete checkpoint, and
failed evaluation modes are retried before the next round. For a custom first
round name, set the same `SOLVER_DYNAMIC_RUN_NAME` used for that run.

Evaluation summaries are at
`$STORAGE_PATH/rzero_runs/$RUN/evaluations/solver_v{2,3,4,5}/{rzero-original,corrected}/summary.md`
and `summary.csv`. Logs and vote audits follow the round-1 paths below with
`solver_v1` replaced by the corresponding round.

### Four-GPU Questioner reward generation

The continuation launcher now defaults `VALIDITY_RZERO_REWARD_BORROW_GPUS=1`.
After Questioner generation and old/reference log-prob computation have finished
and its models have been offloaded, two temporary single-GPU Solver services
join the permanent GPU 2,3 services on the Questioner's GPU 0,1. The batch is
split into four ordered shards. Each shard uses the same nine validity samples,
ten fresh math samples for valid questions, prompts, sampling parameters, and
reward aggregation as before. This changes scheduling, not the reward rule;
individual stochastic samples need not be identical to the two-GPU run.

Temporary services use separate ports (by default 5002,5003) and a separate PID
file. They are stopped before the existing four-GPU semantic judge phase, and
the Questioner processes remain alive. The implementation waits for all four
reward shards before semantic judging and for semantic completion before the
Questioner update. It deliberately waits for the Questioner-ready barrier
before submitting any phase-A reward requests, trading the earlier two-GPU
overlap for a simpler four-GPU phase. Other launchers retain the old behavior
unless the flag is explicitly enabled, and frozen-validity mode is unsupported.

Questioner logs include `[reward_gpu_borrow]` wait/startup/reward/release timing;
each Solver-service log includes `[phase_a_timing]` validity, math generation,
and CPU answer-clustering timing. The temporary service logs contain
`_reward_gpu0_port5002` or `_reward_gpu1_port5003` in their filenames. Failed
reward shard files are retained under `$STORAGE_PATH/temp_results/reward_gpu_borrow_*`.

The scheduling flag is excluded from the training configuration fingerprint,
so an existing continuation can resume with it enabled. To disable it:

```bash
VALIDITY_RZERO_REWARD_BORROW_GPUS=0 bash methods/validity_rzero/continue_solver_dynamic_k8.sh --resume
```

Pull the update when the training pipeline is stopped, then run the continuation
with `--resume`. It skips committed stages and resumes Questioner training from
the latest saved checkpoint, not from a partially computed reward batch. The
Questioner still saves every five steps by default: if interrupted before its
first checkpoint, the current five-step Questioner stage starts again. This
change does not alter the checkpoint cadence.

## Exact update rule

1. Generate 16 responses for each R-Zero question and 5 for each Terra question
   from the current policy. Source batches use the same rollout parameters
   except `n`; dispatcher padding is discarded before statistics are computed.
   The actor's `rollout.n=5` and update batch size remain unchanged.
2. R-Zero answers use the original reward's last-box extraction and mathruler
   mathematical equivalence. Missing, empty or malformed answers do not vote.
   A label requires a **unique largest cluster with at least two members**.
   No absolute-majority threshold is used. Ties with size >=2, singleton-only
   groups, and groups with no answers are rejected separately.
3. Replace R-Zero targets with that batch's voted label, retain the original
   accuracy/format reward, and compute the original GRPO mean/std from **all
   16 responses**. Terra retains its true label, reward and five-response GRPO.
4. Route R-Zero task advantages: keep only nonmatching responses with original
   advantage <0 and a valid full-group vote. All other R-Zero task advantages
   are zero, including every response in rejected or all-agree groups.
5. Select two matching and three nonmatching responses uniformly without
   replacement within each class. Backfill from the other class if necessary;
   never duplicate responses or prefer shorter responses. Rejected groups
   select five uniformly, with task advantages zero. Keep all five Terra rows.
   This fixed class allocation intentionally changes weighting relative to
   uniform selection from all 16; it is not an unbiased full-group estimator.
6. Compute old-policy and reference log-probabilities only for selected update
   rows. Balance tokens across devices after selection; all labels, advantages
   and eligibility travel with the rows. Never revote or recenter advantages
   on the five-row subset, including during subsequent PPO minibatches.
7. Apply the token mask below only to eligible R-Zero negative task advantages.
   Keep all selected valid tokens in the original KL loss and loss denominator.
   Positive R-Zero rows and no-consensus rows still receive KL. Terra task
   gradients, KL coefficient 0.01, learning rate, and PPO clipping are unchanged.

More voting increases generation work; it does not expand the actor/reference
update batch beyond five responses per question. Full-vocabulary entropy adds
detached computation during actor updates. This experiment combines dynamic
voting and token selection, so its comparison against the previous run cannot
isolate their individual effects.

## Token mask definition

At each actor update, use current temperature-scaled token probabilities and
the **full vocabulary entropy** `H_t = -sum_v p_v log p_v`. Compute it in FP32
chunks of 64 token positions to avoid allocating a full extra FP32
sequence-by-vocabulary tensor. Entropy and mask have no gradient.

For each response, only over its valid response positions (including its first
EOS, as in the existing response mask): clip entropy at its 98th percentile,
then min-max normalize using the valid minimum and clipped maximum. When this
range is <1e-8, normalized entropy is zero. Score each token as
`s_t = -log p(y_t | prefix) * (1 - normalized_H_t)` and keep scores >= the valid
median. Equal scores are retained, so ties can retain more than half. Masking
sets the other eligible negative advantages to zero and **does not change the
response mask, KL inputs or denominator**, nor normalize advantages again.

This follows the probability x low-entropy rule in TTPO section 3.4 and the
q98 normalization in its [public implementation](https://github.com/ZJU-REAL/TTPO/blob/main/TTPO/ttpo_trainer.py#L712-L723).
TTPO's public median/normalization range is the valid tokens of a microbatch;
ours is explicitly per response. They coincide for this launcher's update
microbatch size of one. This is not a replication of TTPO's complete training
recipe or of the unverified Fig.3 negative-only ablation configuration. No
OPD/OPSD, LoRA, extra loss weight, or first-1024-token restriction is introduced.

## Inspect results

With `RUN=qwen3_4b_validity_rzero_semantic_novelty_gate_k8_solver_dynamic_mask_4gpu_v1`:

- Training log: `$STORAGE_PATH/rzero_runs/$RUN/artifacts/${RUN}_solver_v1/solver_*.log`.
- Vote audit: `$STORAGE_PATH/models/${RUN}_solver_v1/solver_vote_audit/step_*.jsonl`.
  Includes a few complete groups per step, old/new labels, extracted answers,
  raw advantages, selected rows, prompts and untrimmed responses. This permits
  inspection of answer changes and repetitive tails without new inference.
- Evaluation summaries:
  `$STORAGE_PATH/rzero_runs/$RUN/evaluations/solver_v1/{rzero-original,corrected}/summary.md`
  and `summary.csv`. Per-attempt directories contain full evaluator results.
- W&B `solver_dynamic/`: largest cluster fraction, valid/tie/singleton/no-answer
  and all-agree group rates, invalid answer rate, old-label agreement **among
  valid votes**, selected positive/negative/no-consensus counts, effective
  negatives, full 16-rollout response length and clip rate, repeated-tail rate.
  The repeated-tail diagnostic is a nonblank unit of 1-100 characters repeated
  at least 10 times, covering >=200 characters in the final 1000 characters;
  it is not an extra reward or a comprehensive repetition detector.
- `actor/negative_mask_retained_fraction`: retained/eligible negative response
  tokens, aggregated across equal-size DP partitions. Existing response-length
  metrics describe the selected five, whereas `solver_dynamic/` length metrics
  describe the full R-Zero voting pool. `full_group/solver_negative_only/` is
  routing before selection; use `solver_dynamic/effective_negative_count` for
  actual selected negative trajectories. `reward/` metrics describe update rows.

CPU verification covers mixed-source generation/dispatch padding, mathematical
voting, shuffled uid alignment, class shortages, no-consensus/all-agree cases,
full-group advantages, actual sparse mixed reward metrics, exact entropy,
actor forward alignment and PG/KL gradients, and launcher evaluation resume.
No GPU training is launched by these tests.
