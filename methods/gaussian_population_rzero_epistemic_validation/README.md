# Gaussian Population R-Zero: V1–V3 Epistemic Validation

This directory implements a read-only, offline pilot over the retained ordinary
R-Zero V1–V3 Solver datasets. It does not train a Questioner or Solver, mutate
existing checkpoints, delete source data, or upload artifacts.

The recoverable Arrow datasets are already filtered by the historical reward.
Consequently, the experiment tests whether epistemic disagreement can further
separate valid questions **within old-reward-retained data**. It cannot reproduce
selection from the deleted 8k candidate pools or reconstruct the rollout-batch
BLEU component of the original Questioner reward.

## Run

Edit environment overrides if required, then run from the repository root:

```bash
bash methods/gaussian_population_rzero_epistemic_validation/run.sh \
  --config methods/gaussian_population_rzero_epistemic_validation/config.sh
```

Resume a stopped pipeline or run one stage:

```bash
bash methods/gaussian_population_rzero_epistemic_validation/run.sh \
  --config methods/gaussian_population_rzero_epistemic_validation/config.sh \
  --resume

bash methods/gaussian_population_rzero_epistemic_validation/run.sh \
  --config methods/gaussian_population_rzero_epistemic_validation/config.sh \
  --stage score_all_sigmas --resume
```

Stages are `prepare`, `score_all_sigmas`, `judge`, and `analyze`. Dependencies
must already be complete for a single-stage invocation. Artifacts are written to:

```text
$STORAGE_PATH/epistemic_validation/$RUN_NAME/
```

Live judging reads `OPENAI_API_KEY` from the environment. The key is never placed
in prompts, manifests, or output files.

## Important artifacts

- `prepared/`: stable sampled row IDs and Arrow provenance.
- `scores/v*/raw/sigma_*/expert_*.parquet`: all raw 8x8 completions, atomically sharded by round, sigma, and expert.
- `scores/v*/summary/sigma_*.parquet`: answer classes and both entropy policies.
- `judge/blind_input.jsonl`: the only fields exposed to the reference Judge.
- `judge/human_review_blind.jsonl`: 75-question blind human review sheet.
- `analysis/report.md`: equal-footing cross-sigma result with CSV/JSON/PNG companions.

Every one of the 600 questions is scored at the five preregistered scales
`0, 1e-4, 3e-4, 1e-3, 3e-3`, for 192,000 formal completions. Noise directions,
expert identities, and sampling seeds are identical across scales. Sigma zero is
the control for disagreement induced only by generation sampling. There is no
calibration gate and no post-hoc selection of a main sigma.

Question validity is sigma-independent, so GPT-5.6 judges each unique question
text exactly once. Duplicate dataset rows reuse that blind judgment while keeping
their original row IDs in every analysis.

To import completed human labels:

```bash
python methods/gaussian_population_rzero_epistemic_validation/human_review.py \
  --human-results "$RUN_ROOT/judge/human_review_blind.csv" \
  --private-key "$RUN_ROOT/judge/human_review_private_key.jsonl" \
  --judge-results "$RUN_ROOT/judge/judge_results.jsonl" \
  --output "$RUN_ROOT/analysis/human_agreement.json"
```

## Smoke tests

`tests/gpu_smoke.sh` uses two questions, all eight experts, and two samples per
expert. It exercises the real four-GPU vLLM path without altering checkpoints.
`tests/live_judge_smoke.sh QUESTION_FILE` performs one optional live Judge call.
