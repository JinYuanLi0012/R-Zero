# Gaussian-Population R-Zero

This is an isolated R-Zero experiment. It can apply one operation to either
population role:

\[
\theta_i=\theta+\sigma\epsilon_i,\qquad \epsilon_i\sim\mathcal N(0,I).
\]

It does **not** import RandOpt and does not implement selection, Top-K,
cross-model voting, distillation, or an ES update. The only persistent models
are the central Questioner and central Solver. Set
`SOLVER_POPULATION_ENABLED=false` to keep Gaussian Questioner generation while
restoring standard R-Zero feedback from the unperturbed current Solver.

## Round semantics

For round `t`:

1. With Solver population enabled, logical Solver experts are reconstructed
   around central `S_t`; every expert answers every valid candidate 10 times and
   their within-expert majority rates are averaged. With it disabled, identical
   physical replicas of unperturbed `S_t` split the candidates, so each question
   is evaluated exactly once with the original fixed denominator of 10.
2. Standard Questioner GRPO plus the existing within-batch BLEU penalty creates
   `Q_(t+1)`.
3. Logical Questioner experts are reconstructed around `Q_(t+1)` and split the
   fixed 4000-attempt generation budget. Every attempt receives a distinct,
   deterministic sampling seed derived from its expert seed and attempt index.
4. The unperturbed central `S_t` alone labels all questions with 9 samples and
   the standard valid-answer denominator and score filter builds the Solver
   dataset. The fixed denominator of 10 is specific to Questioner feedback;
   central dataset labeling continues to use the valid-answer denominator.
5. Standard Solver training creates `S_(t+1)` and selects step 15.

Population experts are represented only by seeds and manifests. No expert
checkpoint is written.

On the first invocation, a Hub `BASE_MODEL` is resolved to one immutable local
snapshot. Set `BASE_REVISION` to pin a specific revision; the complete base
file manifest and hashes are verified again on resume.

## Run

From the repository root, in the existing R-Zero environment:

```bash
source env_rzero.sh
bash methods/gaussian_population_rzero/run.sh \
  --config methods/gaussian_population_rzero/config.sh
```

For the Questioner-population-only experiment:

```bash
bash methods/gaussian_population_rzero/run.sh \
  --config methods/gaussian_population_rzero/config_questioner_only.sh
```

Resume or skip benchmark evaluation:

```bash
bash methods/gaussian_population_rzero/run.sh --resume
bash methods/gaussian_population_rzero/run.sh --resume --no-eval
```

Use a new `RUN_NAME` whenever K, sigma, seed, budget, or training settings
change. The state fingerprint rejects incompatible resume attempts.

## Important defaults

```text
run=qwen3_4b_gaussian_kq16_ks6_sq0p001_ss0p001_b4000_vb32_seed42_r5
Kq=16, Ks=6
Solver population enabled=true
sigma_q=1e-3, sigma_s=1e-3
B=4000
Solver expert samples=10
central Solver label samples=9
vLLM generate batch=32
TP=1
```

The four population hyperparameters and `VLLM_SERVER_BATCH_SIZE=32` are fixed
in `config.sh`, so a formal run does not depend on shell exports. Exactly as in
the original R-Zero Solver-feedback server, this limits the number of candidate
question prompts in each `vllm.LLM.generate()` call during Questioner training.
It does not control Questioner-population generation, central Solver labeling,
or any training batch, and it does not change the total questions or samples.

`TP=1` means one complete inference model per physical GPU. K may be larger
than the GPU count; experts are processed in deterministic waves. Each physical
engine retains one CPU center anchor and reconstructs every expert directly
from it, avoiding BF16 add/subtract drift.

The method forces `VLLM_USE_V1=0`. In vLLM 0.9.1 the V1 frontend keeps model
weights in a separate EngineCore process, while Gaussian expert switching
requires direct access to the in-process V0 model parameters.

Solver-population feedback follows standard R-Zero's blocking request
semantics: there is no whole-request HTTP timeout and no automatic population
replay. Per-comparison math grading retains the standard 10-second guard.

Outputs are stored under:

```text
$STORAGE_PATH/gaussian_population_rzero/$RUN_NAME/
  questioners/
  datasets/
  solvers/
  evaluations/
  logs/
  state/
```

The original `scripts/main.sh` and `methods/task_vector_rzero/` are not used or
modified by this method.

## Tests

```bash
python3 -m unittest discover \
  -s methods/gaussian_population_rzero/tests \
  -p 'test_*.py'
```

CPU population/reward tests run in the normal R-Zero environment. The local
checkout may skip dependency-backed tests when torch/mathruler are unavailable.

The GPU smoke profile uses the formal model, standard rollout batches, 10/9
feedback and labeling samples, standard score filtering, token limits, and
four-GPU topology. It reduces the temporary populations to `Kq=Ks=4`, the
Questioner-population generation budget to `B=2048` (512 attempts per expert),
and runs one real update for each center in one round. This is therefore a
shorter formal preflight, not a tiny or minutes-long test:

```bash
export STORAGE_PATH=/engrfs/project/jiaxinh/jinyuan/R-zero-storage
export RUN_NAME=gaussian_population_smoke
bash methods/gaussian_population_rzero/run.sh \
  --config methods/gaussian_population_rzero/tests/smoke_config.sh \
  --no-eval

python3 methods/gaussian_population_rzero/tests/verify_smoke.py \
  "$STORAGE_PATH/gaussian_population_rzero/gaussian_population_smoke"
```

The verifier checks four exact 512-attempt quotas, either all-expert or
single-central-Solver feedback audits with 10 samples, center-only labels with
9 samples, the formal score range, completed stage markers, and that only `Q1`
and `S1` are inheritable checkpoints.

To smoke-test the Questioner-only population mode, use the central-feedback
profile; the same verifier automatically detects its manifest:

```bash
bash methods/gaussian_population_rzero/run.sh \
  --config methods/gaussian_population_rzero/tests/smoke_questioner_only_config.sh \
  --no-eval

python3 methods/gaussian_population_rzero/tests/verify_smoke.py \
  "$STORAGE_PATH/gaussian_population_rzero/gaussian_questioner_only_smoke"
```
