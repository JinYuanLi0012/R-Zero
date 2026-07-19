# Gaussian-Population R-Zero

This is an isolated R-Zero experiment. It adds one operation only:

\[
\theta_i=\theta+\sigma\epsilon_i,\qquad \epsilon_i\sim\mathcal N(0,I).
\]

It does **not** import RandOpt and does not implement selection, Top-K,
cross-model voting, distillation, or an ES update. The only persistent models
are the central Questioner and central Solver.

## Round semantics

For round `t`:

1. Logical Solver experts are reconstructed around central `S_t`.
2. Every Solver expert answers every valid central-Questioner candidate 10
   times. Majority rates are computed inside each expert and then averaged.
3. Standard Questioner GRPO plus the existing within-batch BLEU penalty creates
   `Q_(t+1)`.
4. Logical Questioner experts are reconstructed around `Q_(t+1)` and split the
   fixed 4000-attempt generation budget. Every attempt receives a distinct,
   deterministic sampling seed derived from its expert seed and attempt index.
5. The unperturbed central `S_t` alone labels all questions with 9 samples and
   the standard valid-answer denominator and score filter builds the Solver
   dataset. The fixed denominator of 10 is specific to Solver-expert feedback.
6. Standard Solver training creates `S_(t+1)` and selects step 15.

Experts are represented only by seeds and manifests. No expert checkpoint is
written.

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

The four population hyperparameters, `VLLM_SERVER_BATCH_SIZE=32`, the storage
path, and math-only evaluation are committed in `config.sh`; no per-run exports
are needed. `env_rzero.sh` is still required to activate the environment and
configure caches.

For GPT rechecking of locally incorrect math answers, create the ignored
repository-root file `tokens.json` with a newly issued key and restrict its
permissions:

```json
{
  "openai": "REPLACE_WITH_A_NEW_KEY"
}
```

```bash
chmod 600 tokens.json
```

Never commit `tokens.json`. The evaluation records local math scores even when
the OpenAI key is absent; only the optional GPT recheck is skipped.

Resume or skip benchmark evaluation:

```bash
bash methods/gaussian_population_rzero/run.sh --resume
bash methods/gaussian_population_rzero/run.sh --resume --no-eval
```

Resume is stage-granular. A completed Questioner marker skips Questioner
training and continues with that round's dataset and Solver stages; a completed
dataset marker continues directly with Solver training. An interruption inside
an unfinished training stage preserves its partial directory as `.stale.*` and
reruns that stage rather than resuming an individual optimizer checkpoint.

After every completed Solver stage, evaluation runs automatically. With
`EVAL_MATH_ONLY=1` in the formal config it runs the seven math benchmarks and
the optional GPT recheck, then stops before SuperGPQA, BBEH, and MMLU-Pro.

Use a new `RUN_NAME` whenever K, sigma, seed, budget, or training settings
change. The state fingerprint rejects incompatible resume attempts.

## Important defaults

```text
Kq=16, Ks=6
sigma_q=1e-3, sigma_s=1e-3
B=4000
Solver expert samples=10
central Solver label samples=9
vLLM request batch=32
TP=1
```

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

The verifier checks four exact 512-attempt quotas, all-expert feedback audits
with 10 samples, center-only labels with 9 samples, the formal score range,
completed stage markers, and that only `Q1` and `S1` are inheritable
checkpoints.
