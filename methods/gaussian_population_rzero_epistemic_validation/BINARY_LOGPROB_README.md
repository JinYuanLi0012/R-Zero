# Binary few-shot + model-logprob Base Judge

This is the minimal follow-up to the A-F structured Judge control. It reuses the
same 600 prepared questions and Terra first-pass reference labels, but it does not
reuse old Qwen Judge outputs and does not call an external API.

The frozen `Qwen/Qwen3-4B-Base` runs two preregistered prompt interfaces:

- `direct`: directly inspect whether the question is sufficient, consistent,
  solvable, and objectively gradable.
- `solver_first`: solve first while checking for missing information,
  contradictions, impossibility, and multiple reasonable interpretations.

Both prompts contain the same four obvious synthetic demonstrations. None comes
from the 600 target questions or Terra judgments. The GPU worker sees only an
opaque ID and question text.

For each prompt, the model deterministically generates one concise analysis. The
worker then appends `Verdict:` and independently scores the complete candidate
token sequences ` VALID` and ` INVALID` with vLLM prompt-token logprobs. The
reported `probability_valid` is a two-candidate softmax of those sequence
log-likelihoods. It is not generated or self-reported by the model.

## Formal run

```bash
bash methods/gaussian_population_rzero_epistemic_validation/run_binary_logprob_judge.sh \
  --run-root "$RUN_ROOT" \
  --model Qwen/Qwen3-4B-Base \
  --resume
```

Defaults are four single-GPU shards (`0,1,2,3`), temperature 0, 1024 maximum
analysis tokens, and batch size 16. Atomic artifacts allow safe resume.

Outputs:

```text
$RUN_ROOT/base_judge_binary_logprob/
├── blind_input.jsonl
├── private_mapping.jsonl
├── raw/
│   ├── direct/
│   └── solver_first/
├── binary_logprob_results.jsonl
├── binary_logprob_manifest.json
└── analysis/
    ├── metrics.json
    ├── binary_metrics.csv
    ├── confusion_matrices.csv
    ├── round_valid_rates.csv
    ├── prompt_disagreements.csv
    ├── generation_diagnostics.csv
    └── report.md
```

Terra label A is the Valid reference and B-F are Invalid. The report includes the
always-valid baseline and overall/V1/V2/V3 invalid recall, balanced accuracy,
Valid precision/recall/F1, MCC, Cohen's kappa, and ROC-AUC.

## CPU tests

```bash
python -m unittest \
  methods.gaussian_population_rzero_epistemic_validation.tests.test_binary_logprob_judge
```

## Two-question GPU smoke

```bash
bash methods/gaussian_population_rzero_epistemic_validation/tests/binary_logprob_gpu_smoke.sh \
  "$RUN_ROOT"
```
