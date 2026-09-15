# OctoThinker two-GPU Terra evaluation

Run from the repository root in the existing Linux training environment. This
evaluates the **original** `jinyuan222/rzero-validity-rl-terra-v1` validation split
(297 rows), even though training used the clean dataset. It is not a clean-split
evaluation. The original dataset loader, scoring rules and API recheck are retained.

```bash
export STORAGE_PATH=/engrfs/project/jiaxinh/jinyuan/R-zero-storage
# Set OPENAI_API_KEY securely in your environment first.
(
  OCTO_CACHE_ROOT=$(mktemp -d /tmp/octo-terra-eval.XXXXXX) || exit 1
  export TORCHINDUCTOR_CACHE_DIR="${OCTO_CACHE_ROOT}/inductor"
  export TRITON_CACHE_DIR="${OCTO_CACHE_ROOT}/triton"
  mkdir -p "$TORCHINDUCTOR_CACHE_DIR" "$TRITON_CACHE_DIR" || exit 1
  VALIDITY_TERRA_GPU_IDS=0,3 \
    bash methods/validity_rl/evaluate_octothinker_terra.sh
)
echo "evaluation exit code: $?"
```

Default: sequential step 5, 10, 15; each uses two GPUs (TP=2), n=1,
temperature=0, max_tokens=4096. The prompt uses `validity_solver.jinja` plus
`octothinker_chat.jinja`, encoded without inserting another BOS token.
Stop training before evaluating its checkpoints and ensure shared-storage access
is working. Only merge trusted checkpoints: the existing merger loads pickle files.

The entry checks both rank model shards and tokenizer/config metadata for every
selected checkpoint. It merges on CPU using the existing `scripts/model_merger.py`
into a temporary directory and publishes completed results to
`RUN_ROOT/evaluation_models/global_step_N/actor/huggingface`. Original checkpoints
are unchanged. Allow enough host RAM and disk for three additional 3B models.
Optimizer/dataloader files are not required for inference. Presence/nonzero-size
checks do not prove tensor integrity; the merger and model loader perform actual loads.
Completed merges are reused only when source paths, sizes and modification times
match; if sources change, select a new `VALIDITY_TERRA_MODEL_ROOT`.

API recheck defaults to `gpt-5.6-luna`, reasoning effort `none`. Set
`RECHECK_JUDGE_MODEL` if needed. It sends full responses and canonical answers
for locally incorrect VALID examples, except explicit INVALID predictions.
This incurs API costs. Existing `results.jsonl` retains local and API scores;
`final_correct` and aggregate accuracy include successful API rechecks. API errors
are recorded as `api_error` and remain incorrect, so inspect these before comparing
models. `VALIDITY_TERRA_SKIP_API_RECHECK=1` is an optional local-only diagnostic,
not the default comparison protocol.

Outputs: `RUN_ROOT/evaluations/terra_validation_TIMESTAMP/step_N/results.jsonl`,
per-model `summary.json`, and `comparison.json`. Overall accuracy requires correct
math for VALID examples and INVALID for invalid examples; it is not pure binary
classification accuracy. Other metrics are VALID math accuracy, INVALID recall
and precision, and VALID false-rejection rate, including per-round summaries.

Overrides:

- `VALIDITY_RUN_ROOT`: training run directory.
- `VALIDITY_TERRA_MODELS="10 15"`: evaluate only selected steps.
- `VALIDITY_TERRA_MODELS="base 5 10 15"`: optionally include the untrained
  `OctoThinker/OctoThinker-3B-Hybrid-Base` baseline with the same prompt.
- `VALIDITY_TERRA_OUTPUT_ROOT`: new result directory; existing results are not
  overwritten unless `VALIDITY_TERRA_ALLOW_EXISTING=1` is explicitly supplied.

The legacy `evaluate_terra_validation.sh` keeps its Qwen defaults.
