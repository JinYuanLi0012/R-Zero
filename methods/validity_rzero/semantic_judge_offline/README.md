# Offline 50-pair semantic-judge falsification test

This directory is deliberately independent of R-Zero training. It does not modify
the Questioner reward, Solver, archive, or any training configuration.

The repository's raw 4B base model is `Qwen/Qwen3-4B-Base` (see
`scripts/run_qwen3_4b_full.sh` and `methods/validity_rzero/run.sh`). Do not replace
it with the Step-15 validity Solver, an Instruct model, or another checkpoint.

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
