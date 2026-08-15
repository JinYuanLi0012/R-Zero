# Frozen Qwen3-4B-Base question-validity control

This is a small, independent control experiment over the 600 prepared questions.
It does not regenerate questions, rerun the Solver population, perturb parameters,
or call the Terra API. A frozen `Qwen/Qwen3-4B-Base` sees only each question and
predicts the same strict A-F validity taxonomy used by the Terra reference Judge.

## Formal run

From the repository root on the four-A100 server:

```bash
bash methods/gaussian_population_rzero_epistemic_validation/run_base_judge.sh \
  --run-root "$RUN_ROOT" \
  --model Qwen/Qwen3-4B-Base \
  --resume
```

The defaults are one deterministic completion per question, `temperature=0`,
`top_p=1`, `max_tokens=4096`, and GPU IDs `0,1,2,3`. Resume skips every atomic
per-question artifact already marked `success` or `final_parse_failure`.

The worker first requests guided JSON when the installed vLLM supports it. If it
does not, it uses the same strict JSON prompt without guidance. A malformed result
gets one deterministic retry with a repair instruction; a second malformed result
is retained as an explicit final parse failure.

Outputs are isolated under:

```text
$RUN_ROOT/base_judge/
├── blind_input.jsonl
├── private_mapping.jsonl
├── raw/
├── base_judge_results.jsonl
├── base_judge_manifest.json
└── analysis/
    ├── metrics.json
    ├── binary_metrics.csv
    ├── af_confusion.csv
    ├── round_valid_rates.csv
    ├── disagreements.csv
    └── report.md
```

Only `opaque_base_judge_id` and `question` occur in `blind_input.jsonl`, which is
the sole experiment-data file read by GPU workers. Analysis treats Terra label A
as Valid and B-F as Invalid. Terra remains a reference judgment, not ground truth.
The report includes an always-valid baseline so ordinary accuracy cannot obscure
poor invalid-question detection.

## CPU checks

```bash
python -m unittest \
  methods.gaussian_population_rzero_epistemic_validation.tests.test_base_judge
```

## Two-question GPU smoke

```bash
bash methods/gaussian_population_rzero_epistemic_validation/tests/base_judge_gpu_smoke.sh \
  "$RUN_ROOT"
```

The smoke test copies two prepared rows to a temporary directory, runs the actual
four-shard launch path with shorter generations, and leaves formal artifacts
untouched.
