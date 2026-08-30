# Offline 50-pair semantic-judge falsification test

This directory is deliberately independent of R-Zero training. It does not modify
the Questioner reward, Solver, archive, or any training configuration.

The repository's raw 4B base model is `Qwen/Qwen3-4B-Base` (see
`scripts/run_qwen3_4b_full.sh` and `methods/validity_rzero/run.sh`). Do not replace
it with the Step-15 validity Solver, an Instruct model, or another checkpoint.

## Round-4 2048x128 semantic-MC smoke

This is the required feasibility smoke before enabling the online treatment.
It samples all 2,048 candidates from the full Round-4 Phase-B file (seed 42),
then samples one shared 128-index panel from those candidates (seed 43). It does
not filter by validity, score, or Phase-B pass status and does not deduplicate
question text. Only the same row index is skipped as self; cached exact-text
pairs are expanded back to their original pair-instance multiplicity.

```bash
cd /storage1/jiaxinh/Active/jinyuan/R-zero
git pull --ff-only
git rev-parse --short HEAD
source env_rzero.sh

SEMANTIC_SMOKE_INPUT=/engrfs/project/jiaxinh/jinyuan/R-zero-storage/rzero_runs/qwen3_4b_validity_rzero_clean_formal_r10_initstep15_divlambda5_v1/datasets/round_4_phase_b.jsonl
SEMANTIC_SMOKE_OUTPUT=/engrfs/project/jiaxinh/jinyuan/R-zero-storage/rzero_runs/round4_semantic_mc_smoke_2048x128_v1

python methods/validity_rzero/semantic_judge_offline/run_round4_semantic_smoke.py \
  --input "$SEMANTIC_SMOKE_INPUT" \
  --output-dir "$SEMANTIC_SMOKE_OUTPUT" \
  --model Qwen/Qwen3-4B-Base \
  --candidate-count 2048 \
  --panel-count 128 \
  --candidate-seed 42 \
  --panel-seed 43 \
  --sampling-seed 42 \
  --max-tokens 1024 \
  --gpu-ids 2,3 \
  --local-files-only
```

The two workers each load one frozen Base replica; no Solver is loaded. The
runner writes `semantic_smoke_manifest.json`,
`semantic_smoke_per_question.jsonl`, and `semantic_smoke_report.md`. It also
keeps a successful exact-pair cache in the output directory so an interrupted
rerun can avoid already completed inference while preserving multiplicity.

Inspect the fixed pair-count invariant, final retry parse rate, reward summary,
and per-question records before starting training:

```bash
python - "$SEMANTIC_SMOKE_OUTPUT/semantic_smoke_manifest.json" <<'PY'
import json, sys
manifest = json.load(open(sys.argv[1]))
feasibility = manifest["feasibility"]
assert feasibility["total_pair_instances"] == 262_016, feasibility
print(json.dumps(feasibility, indent=2))
print(json.dumps(manifest["reward_signal"], indent=2))
PY

sed -n '1,160p' "$SEMANTIC_SMOKE_OUTPUT/semantic_smoke_report.md"
wc -l "$SEMANTIC_SMOKE_OUTPUT/semantic_smoke_per_question.jsonl"
```

## Controlled v4 direct-label ablation

V4 measures the accuracy and cost effect of removing the brief-analysis request.
It uses the same 50 pairs, both orders, frozen model snapshot, vLLM engine, BF16,
seed, max_tokens=1024, sampling parameters, full box stops, retained stop text,
parser, and runtime accounting as v3-max1024. The only intended variable is the
prompt asking for the boxed label directly. This is a diagnostic ablation, not a
held-out validation.

```bash
INPUT_ROOT=/engrfs/project/jiaxinh/jinyuan/R-zero-storage/rzero_runs/semantic_judge_offline_50/input
OUTPUT_ROOT=/engrfs/project/jiaxinh/jinyuan/R-zero-storage/rzero_runs/semantic_judge_offline_50/output
V3_OUTPUT="${OUTPUT_ROOT}/qwen3_4b_base_generative_v3_vllm_max1024_diagnostic"
V4_OUTPUT="${OUTPUT_ROOT}/qwen3_4b_base_v4_direct_label_ablation"

python methods/validity_rzero/semantic_judge_offline/run_pair_judge_v4_direct.py \
  --input "${INPUT_ROOT}/semantic_judge_50_blind.jsonl" \
  --output-dir "${V4_OUTPUT}" \
  --model Qwen/Qwen3-4B-Base \
  --max-tokens 1024 \
  --seed 42 \
  --tensor-parallel-size 1 \
  --gpu-memory-utilization 0.85 \
  --local-files-only

python methods/validity_rzero/semantic_judge_offline/score_pair_judge_v4_direct.py \
  --predictions "${V4_OUTPUT}/predictions_v4_direct.jsonl" \
  --blind "${INPUT_ROOT}/semantic_judge_50_blind.jsonl" \
  --gold "${INPUT_ROOT}/semantic_judge_50_gold.jsonl" \
  --output-dir "${V4_OUTPUT}/scored_v4_direct"

python methods/validity_rzero/semantic_judge_offline/compare_v4_direct.py \
  --baseline-metrics "${V3_OUTPUT}/scored_v3_max1024/metrics_v3.json" \
  --baseline-manifest "${V3_OUTPUT}/run_manifest_v3_vllm.json" \
  --direct-metrics "${V4_OUTPUT}/scored_v4_direct/metrics_v4_direct.json" \
  --direct-manifest "${V4_OUTPUT}/run_manifest_v4_direct.json" \
  --output-dir "${V4_OUTPUT}/comparison_vs_v3"
```

The comparison writes `comparison_v4_direct_vs_v3.json` and Markdown, including
per-order accuracy/format deltas plus mean output-token, throughput, generation
wall-time, and total-wall-time deltas.

## Current protocol: generative v3-max1024/vLLM diagnostic rerun

V3 keeps the user-confirmed v2 prompt byte-for-byte unchanged, but replaces the
greedy Transformers loop with one batched vLLM call over all 100 ordered
conditions. It also stops as soon as either complete canonical box is generated,
retains the stop string in the output, relaxes parsing only for boxed-label
surface variants, and records model-load, generation, total runtime, token counts,
and throughput. This is still a **diagnostic rerun on the same 50 pairs**, not a
new held-out validation.

The sampling protocol was selected only after inspecting these sources:

- The exact `Qwen/Qwen3-4B-Base` `generation_config.json` says
  `do_sample=false` and `max_new_tokens=2048`. V2 exposed the repetition failure
  of that greedy choice. V3 reads the actual local cached file again at runtime
  and stores both its path and JSON in the manifest. Source:
  <https://huggingface.co/Qwen/Qwen3-4B-Base/blob/main/generation_config.json>.
- This repository's Questioner uses `temperature=1.0, top_p=0.95` in
  `question_generate/question_generate.py`; its Solver service uses
  `temperature=1.0, top_p=1.0, top_k=40` in
  `vllm_service_init/start_vllm_server.py`.
- Qwen's official Qwen3 best practices explicitly warn that greedy decoding can
  cause endless repetitions. Their thinking-mode preset is `temperature=0.6`,
  `top_p=0.95`, `top_k=20`, `min_p=0`; when endless repetition is observed they
  recommend `presence_penalty=1.5`. Source:
  <https://huggingface.co/Qwen/Qwen3-4B#best-practices>.

V3 therefore uses exactly that official sampling preset plus the documented
anti-repetition penalty, neutral `frequency_penalty=0` and
`repetition_penalty=1`, fixed `seed=42`, one sample, and a 1,024-token
limit. The exact `SamplingParams` are serialized in the manifest. The runner
resolves the cached Hub snapshot while reading `generation_config.json` and
passes that exact snapshot directory—not a mutable Hub alias—to vLLM.

```bash
cd /storage1/jiaxinh/Active/jinyuan/R-zero
git pull --ff-only
git rev-parse --short HEAD
git status --short
source env_rzero.sh

INPUT_ROOT=/engrfs/project/jiaxinh/jinyuan/R-zero-storage/rzero_runs/semantic_judge_offline_50/input
OUTPUT_ROOT=/engrfs/project/jiaxinh/jinyuan/R-zero-storage/rzero_runs/semantic_judge_offline_50/output
V3_OUTPUT="${OUTPUT_ROOT}/qwen3_4b_base_generative_v3_vllm_max1024_diagnostic"

python methods/validity_rzero/semantic_judge_offline/run_pair_judge_v3_vllm.py \
  --input "${INPUT_ROOT}/semantic_judge_50_blind.jsonl" \
  --output-dir "${V3_OUTPUT}" \
  --model Qwen/Qwen3-4B-Base \
  --max-tokens 1024 \
  --seed 42 \
  --tensor-parallel-size 1 \
  --gpu-memory-utilization 0.85 \
  --local-files-only
```

V3 writes `predictions_v3_vllm.jsonl` and `run_manifest_v3_vllm.json`. Each
prediction includes the full response, finish/stop reason, prompt/output token
counts, parsed label, and format status. The two complete canonical stop strings
are `\\boxed{SAME_TYPE}` and `\\boxed{DIFFERENT}`, with
`include_stop_str_in_output=true`.

After blind generation completes, score it separately:

```bash
python methods/validity_rzero/semantic_judge_offline/score_pair_judge_v3.py \
  --predictions "${V3_OUTPUT}/predictions_v3_vllm.jsonl" \
  --blind "${INPUT_ROOT}/semantic_judge_50_blind.jsonl" \
  --gold "${INPUT_ROOT}/semantic_judge_50_gold.jsonl" \
  --output-dir "${V3_OUTPUT}/scored_v3_max1024"
```

The scorer writes `metrics_v3.json`, `errors_v3.jsonl`,
`order_disagreements_v3.jsonl`, and `report_v3.md`. End-to-end accuracy remains
primary. Parseable-only accuracy is reported only as an additional diagnostic
and never replaces failures to produce a usable boxed verdict.

## Preserved generative v2 diagnostic rerun

The forced-choice A/B likelihood implementation below is preserved as v1 for
reproducibility, but it is not the current intended experiment. Generative v2
uses the frozen base model as a plain completion model, deterministically
generates a short justification, and strictly parses one final boxed semantic
label. Because the prompt was revised after examining the original protocol,
running these same 50 pairs is a **diagnostic rerun**, not a new held-out
validation.

After resolving the model as described below, run v2 in a new output directory:

```bash
INPUT_ROOT=/engrfs/project/jiaxinh/jinyuan/R-zero-storage/rzero_runs/semantic_judge_offline_50/input
OUTPUT_ROOT=/engrfs/project/jiaxinh/jinyuan/R-zero-storage/rzero_runs/semantic_judge_offline_50/output

python methods/validity_rzero/semantic_judge_offline/run_pair_judge_v2.py \
  --input "${INPUT_ROOT}/semantic_judge_50_blind.jsonl" \
  --output-dir "${OUTPUT_ROOT}/qwen3_4b_base_generative_v2_diagnostic" \
  --model Qwen/Qwen3-4B-Base \
  --device cuda:0 \
  --dtype bfloat16 \
  --batch-size 4 \
  --max-new-tokens 256 \
  --local-files-only
```

This writes `predictions_v2.jsonl` and `run_manifest_v2.json`. Every pair is
generated in `q1_q2` and `q2_q1` order. There is no A/B label mapping and no
conditional-likelihood scoring. The full continuation is retained as
`raw_response`. Exactly one `\\boxed{SAME_TYPE}` or `\\boxed{DIFFERENT}` must
occur at the end; a missing, non-final, repeated, or conflicting boxed label is
recorded as `FORMAT_ERROR` without guessing from ordinary prose.

Score v2 only after blind generation finishes:

```bash
python methods/validity_rzero/semantic_judge_offline/score_pair_judge_v2.py \
  --predictions "${OUTPUT_ROOT}/qwen3_4b_base_generative_v2_diagnostic/predictions_v2.jsonl" \
  --blind "${INPUT_ROOT}/semantic_judge_50_blind.jsonl" \
  --gold "${INPUT_ROOT}/semantic_judge_50_gold.jsonl" \
  --output-dir "${OUTPUT_ROOT}/qwen3_4b_base_generative_v2_diagnostic/scored_v2"
```

The scorer writes `metrics_v2.json`, `errors_v2.jsonl`,
`order_disagreements_v2.jsonl`, and `report_v2.md`. It reports each order's
confusion matrix, accuracy, false negatives, false positives, format errors,
stratum splits, and order stability. It intentionally does not declare this
rerun a new held-out pass or authorize reward integration.

The remaining sections document the preserved v1 protocol.

## 1. Resolve the model before running

From the Linux repository:

```bash
cd /storage1/jiaxinh/Active/jinyuan/R-zero
git pull --ff-only
git rev-parse --short HEAD
git status --short
source env_rzero.sh

printf 'BASE_MODEL=%s\n' "${BASE_MODEL-}"
rg -n 'BASE_MODEL|Qwen3-4B' env_rzero.sh scripts methods examples
find "${HF_HUB_CACHE}" -maxdepth 1 -type d -name 'models--Qwen--Qwen3-4B-Base' -print
```

The runner defaults to the exact repository model ID
`Qwen/Qwen3-4B-Base`. Hugging Face records the loaded revision in the run
manifest. Passing a path containing `Instruct`, `global_step`, or `checkpoint`
fails unless `--allow-nonbase-model` explicitly acknowledges that protocol
deviation.

## 2. Run blind inference

Put the blind file at (or adjust the variable to point to its actual location):

```bash
INPUT_ROOT=/engrfs/project/jiaxinh/jinyuan/R-zero-storage/rzero_runs/semantic_judge_offline_50/input
OUTPUT_ROOT=/engrfs/project/jiaxinh/jinyuan/R-zero-storage/rzero_runs/semantic_judge_offline_50/output

python methods/validity_rzero/semantic_judge_offline/run_pair_judge.py \
  --input "${INPUT_ROOT}/semantic_judge_50_blind.jsonl" \
  --output-dir "${OUTPUT_ROOT}/qwen3_4b_base_v1" \
  --model Qwen/Qwen3-4B-Base \
  --device cuda:0 \
  --dtype auto \
  --batch-size 4 \
  --local-files-only
```

Remove `--local-files-only` only if the exact base model is not cached and a Hub
download is intentional. One GPU is sufficient. Reduce `--batch-size` if memory
is tight.

The inference process reads only the blind JSONL. Only `q1` and `q2` enter the
model prompt; `pair_id` is retained solely for joining outputs. It evaluates all
four preregistered conditions in fixed order:

1. `q1_q2`, `A_same`
2. `q1_q2`, `A_different`
3. `q2_q1`, `A_same`
4. `q2_q1`, `A_different`

It performs no sampling and generates no rationale. It compares conditional
likelihoods of the continuations ` A` and ` B`. If both have equal token counts,
it compares summed token log probabilities. If token counts differ, it compares
mean token log probability so unequal-length raw sums are never mixed. Exact
joint-string tokenization must equal the separately tokenized prompt plus
candidate for every condition; the runner fails before inference if a tokenizer
merges across that boundary. Exact
candidate token IDs, decoded tokens, scoring rule, prompt hashes, model revision,
input hash, Git HEAD, software versions, dtype, device, and GPU are saved in
`run_manifest.json`.

Outputs:

```text
qwen3_4b_base_v1/predictions.jsonl
qwen3_4b_base_v1/run_manifest.json
```

## 3. Score only after inference is complete

The scorer, and only the scorer, receives the private gold key:

```bash
python methods/validity_rzero/semantic_judge_offline/score_pair_judge.py \
  --predictions "${OUTPUT_ROOT}/qwen3_4b_base_v1/predictions.jsonl" \
  --blind "${INPUT_ROOT}/semantic_judge_50_blind.jsonl" \
  --gold "${INPUT_ROOT}/semantic_judge_50_gold.jsonl" \
  --output-dir "${OUTPUT_ROOT}/qwen3_4b_base_v1/scored"
```

The scorer writes:

```text
scored/metrics.json
scored/errors.jsonl
scored/stability_disagreements.jsonl
scored/report.md
```

The primary condition is preregistered as `q1_q2 + A_same`. The result is called
`promising_enough_for_larger_300_pair_validation` only when all checks pass:

- primary accuracy is at least 90%;
- false negatives are at most 2/25;
- false positives are at most 2/25;
- question-order disagreements are at most 2/50 under each of the two mappings;
- A/B-mapping disagreements are at most 2/50 under each of the two question
  orders;
- at most two of the eight `same_template` pairs are wrong in the primary
  condition (the operational no-collapse check).

Otherwise the result is `unstable` when only stability checks fail, or
`falsified` when a semantic-accuracy check fails. Do not tune the prompt on these
50 gold labels and claim a recovered result.

## 4. Local non-GPU checks

```bash
python -m unittest discover \
  -s methods/validity_rzero/semantic_judge_offline/tests \
  -p 'test_*.py' -v
```
