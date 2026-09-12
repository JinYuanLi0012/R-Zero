# OCNR: minimal paper-described R-Zero baseline

An independent implementation of **OCNR: Stabilizing Self-Play by Mitigating
Iteration-Collapse With One-Class Novelty Rewards** (Lee et al., user-provided
25-page PDF, `27123_OCNR_Stabilizing_Self_Pl.pdf`). This is not the authors' code,
not a claimed numerical reproduction, and not R-Diverse. No unpublished details
are inferred from the reported benchmark results.

The backbone is Chengsong-Huang's original R-Zero algorithm, running on the
existing four-GPU verl/vLLM infrastructure. **Validity-RZero, Terra replay,
frozen validity/semantic judges, domain prompts, history-context prompts,
Gaussian populations, task vectors and novelty gates are not enabled.** The
runner removes inherited `VALIDITY_RZERO_*` / `TERRA_REPLAY_*` settings, explicitly
sets `VALIDITY_RZERO_ENABLED=0` and selects the legacy question-format filter.
It does not invoke `scripts/main.sh` or `methods/validity_rzero/run.sh`.

## Run on Linux

From your existing repository and Python environment:

```bash
cd /storage1/jiaxinh/Active/jinyuan/R-zero
git pull --ff-only
source env_rzero.sh
bash methods/ocnr/run.sh
```

Default: Qwen3-4B-Base, five rounds, GPUs 0/1/2/3, ports 5200-5202.
The model is resolved to a local HF snapshot and its path is recorded.
No separate GPU smoke, offline pilot, or dataset upload is required.
The existing environment needs `torch`, `transformers` with Qwen3 support,
`vllm`, `datasets`, `numpy`, `flask`, `requests`, `nltk`, `scikit-learn`, and
`stopit`, already used by the repository's R-Zero environment.

Resume the same configuration:

```bash
bash methods/ocnr/run.sh --resume
```

Completed stages are reused. Interrupted Q/S training resumes the latest
complete checkpoint when available. Unfinished candidate labeling is rerun
from preserved generation shards. An existing run is never silently treated as
a fresh experiment. Logs live inside the run, not only in the terminal.

To change a setting, copy `methods/ocnr/config.json`, give it a **new run_name**,
edit the relevant explicit fields, and use `--config /path/to/config.json`.
Inherited experiment flags do not override these OCNR settings.

## Exact loop and reward

For each round t:

1. Train Q_t from Q_(t-1) against frozen S_(t-1). At t=1 the novelty coefficient
   is zero and no SD service is loaded. At t>=2 use the saved w_(t-1), whose
   embedding model is exactly S_(t-1).
2. Generate 2 x 8,000 = **16,000 candidates in total** (4,000 per GPU), label
   with S_(t-1) using **10 answers per question**, retain the original malformed
   question exclusions and the paper's majority count **3 through 7 inclusive**.
3. Shuffle the curated rows with seed 42+t and split 1:1 without looking at SD.
   One random final row is dropped for an odd count. Only `seen.parquet` enters
   the Solver trainer. `unseen.json` is used only for SD fitting, never Solver
   training or Solver validation.
4. Train S_t from S_(t-1), then compute h(q) for both splits with **S_t**.
5. Fit the single prototype with BCE, then perform cross-round EMA. Save w_t
   for Q_(t+1). History is carried by the vector, not an added replay dataset.

Following Eq. (7), (8), (17), (20):

```text
seen(q)    = exp(-sum((h(q) - w)^2) / tau)
novelty(q) = 1 - seen(q)
base(q)    = 2 * min(p_majority, 1 - p_majority) - BLEU_cluster_share(q)
R_Q(q)     = base(q) + 0.3 * novelty(q)       # t >= 2
```

Malformed outputs keep the upstream negative format branch and receive no
novelty bonus. BLEU is the original within-batch average-linkage clustering,
distance threshold 0.5; its implementation is pinned from upstream commit
`5699329d018d79535b7910abdedf5a6eebf355fd`. No new Phase-B semantic/BLEU dedup
algorithm is invented from the appendix's phrase "diversity filtering".

The existing Phase-B evaluator divides majority count by the number of nonempty
answers. We recover the integer count from its stored `results` and `score`,
filter by [3,7], and save `score=count/10`. `baseline_nonempty_score` is retained
for auditing. This prevents silently implementing a different band when some
rollouts have no extracted answer.

Solver GRPO retains the original repository math reward (0.9 answer correctness
+ 0.1 format), original prompts, optimizer, KL, and rollout settings. It does
not adopt the separate validity-aware reward. Training datasets are local
Parquet; publishing private HF datasets is unnecessary for this baseline.

## Disclosed settings and minimal choices

| Item | Implementation | Paper / reason |
|---|---|---|
| Novelty coefficient | 0.3 | Figure 7 explicitly identifies the default |
| Prototype count | 1 | Table 4 / Sec. 5.3 |
| Features | frozen Solver final hidden state, mean over bare task tokens | B.2.4 |
| Wrappers / answer | none in feature input | task tokens only, wrappers excluded |
| Feature normalization | none | no normalization disclosed; no added L2/whitening |
| SD learning rate | 0.007 | B.2.4 |
| tau | 0.5 | one of disclosed {0.1,0.5}; main-run selection unspecified |
| EMA new-vector weight alpha | 0.05 | Eq.16; one of disclosed {0.05,0.2} |
| SD optimizer / steps | one full-batch SGD step each round | Eq.15-16 say gradient step; optimizer schedule unspecified |
| Initialization | centroid of round-1 curated embeddings after S1, then BCE+EMA | follow explicit warm-start in B.2.1 over inconsistent B.2.4 wording |
| Update timing | Q_t uses S_(t-1), w_(t-1); SD refreshed after S_t | explicit Q2 uses w1 statement in B.2.1; avoids main-text indexing ambiguity |
| Candidate count | 8,000 nominal x 2 = 16,000 actual | interpret listed N=16000 as the over-generated pool, not 32,000 |
| Odd split / seed | drop final shuffled row; 42+t | unspecified bookkeeping, no quality selection |
| Qwen checkpoint | Qwen3-4B-Base | requested base; appendix links Qwen3-4B without resolving this distinction |
| Q/S update steps | 5 / 15 | existing selected R-Zero checkpoint steps; paper gives no per-round steps |
| Q/S global batch | 4 / 128 | preserve the user's Q four-GPU adaptation |
| Q/S rollouts | 4 / 5 | existing repository settings |
| LR / weight decay / KL | 1e-6 / 1e-2 / 1e-2 | B.2.4 and existing config |
| Response limit | 4096 | B.2.4 |
| Embedding batch / cap | 4 / 4096 tokens, right truncation counted | engineering choice; no feature-length cap disclosed |
| Solver input | 2048-token inherited right truncation; no post-split row deletion | retains every assigned seen row in the eligible training pool |
| Questioner input rows | local constant placeholders, same fixed prompt | no need to download math12k to generate identical Q prompts |
| Validation | 32 rows from same training source, never SD holdout | lightweight inherited final validation; not a held-out performance claim |

**Reward scale discrepancy:** the original R-Zero source implements
`min(p,1-p)` (maximum 0.5); the OCNR paper explicitly writes
`1-2*abs(p-0.5)` (maximum 1). Default `uncertainty_scale=2.0` follows the paper.
Setting it to 1.0 reproduces the upstream scale but is a distinct configured
variant; label it accordingly rather than treating the two as identical.

The split is over **row instances**, as a direct random split. Exact repeated
text can land on both sides; the count is reported rather than hidden by an
unpublished dedup rule. "Seen" means assigned to the solver training pool;
the inherited shuffled, finite-step, drop-last loader does not guarantee that
every assigned row is sampled. Neither SD training-set accuracy nor its
held-out-from-Solver labels constitute a held-out SD evaluation.

**No silent repair of SD saturation.** With raw high-dimensional features,
small tau can make all novelty rewards approximately 1. This implementation
logs that behavior and continues the declared algorithm; it does not rescale
features, change tau, train an extra network, enlarge SD steps, or tune on
benchmarks to make the method look successful. BCE is evaluated analytically
in log space to avoid numerical underflow, without changing its objective.

## Four-GPU execution

| Stage | GPUs |
|---|---|
| Round-1 Q update | Q training 0/1; identical Solver vLLM replicas 2/3 |
| Later Q updates | Q training 0/1; Solver vLLM 2; frozen same-Solver HF features 3 |
| Question generation and 10-vote labeling | four independent one-GPU shards |
| Solver training | all four, inherited TP=2 rollout |
| SD refresh | GPU3 feature extraction, CPU vector gradient |

The HF model is a feature extractor, not a second judge. A dedicated GPU avoids
undocumented vLLM hidden-state hooks and two-model GPU memory co-residency.
Later Q feedback throughput may be lower than the two-replica original path;
the number of answers and the reward definition do not change. Startup waits
are ordinary service readiness checks, not a preliminary smoke experiment.

## Results and evaluation

```text
$STORAGE_PATH/rzero_runs/qwen3_4b_ocnr_minimal_v1/
  config.json, manifest.json, DONE.json
  round_1/ ... round_5/
    generated-0.json ... generated-3.json
    labeled.json, curated.json, seen.json, unseen.json, seen.parquet
    SPLIT_DONE.json
    sd.json, sd.features.npz
    rewards/reward-*.json
    logs/{questioner,solver,sd-fit,feedback-*,generate-*,label-*}.log
```

Checkpoints:

```text
$STORAGE_PATH/models/qwen3_4b_ocnr_minimal_v1_questioner_vT/global_step_5/actor/huggingface
$STORAGE_PATH/models/qwen3_4b_ocnr_minimal_v1_solver_vT/global_step_15/actor/huggingface
```

The default trains all five rounds without automatically launching the long
benchmark/API judging suite. Run the same evaluation used for your pure R-Zero
baseline, for example:

```bash
export EVAL_GPU_IDS=0,1,2,3
export EVAL_ARTIFACT_DIR="$STORAGE_PATH/rzero_runs/qwen3_4b_ocnr_minimal_v1/round_5/evaluation"
export EVAL_LOG_DIR="$EVAL_ARTIFACT_DIR/logs"
export FINAL_RESULTS_FILE="$EVAL_ARTIFACT_DIR/final_results.jsonl"
bash evaluation/evaluate.bash \
  "$STORAGE_PATH/models/qwen3_4b_ocnr_minimal_v1_solver_v5/global_step_15/actor/huggingface"
```

Alternatively set `evaluate_each_round=true` before starting a new run to use
the existing evaluator after each round. That evaluator may require the
existing API credentials/local-judge configuration; OCNR training itself does
not need OpenAI API access. Evaluate all saved S1-S5 with the same protocol to
assess iteration-collapse. Do not compare training reward or SD fit accuracy
to the paper's seven-benchmark average.

Suggested paper description: "OCNR (our implementation from the published
description), on Qwen3-4B-Base with our four-GPU R-Zero infrastructure; single
prototype, lambda=0.3, tau=0.5, alpha=0.05, one full-batch SD gradient step per
round." Report the explicit implementation choices above with the results.
