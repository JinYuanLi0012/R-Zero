#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"
args=(
  --annotation-mode "${ANNOTATION_MODE:-sync}"
  --concurrency "${CONCURRENCY:-16}"
  --input "${INPUT_JSONL:-analysis_results/validity_rl_terra_dataset_v1/train.jsonl}"
  --output-dir "${OUTPUT_DIR:-analysis_results/validity_repair_v1}"
  --model "${REPAIR_MODEL:-gpt-5.6-sol}"
  --reasoning-effort "${REPAIR_REASONING_EFFORT:-high}"
  --max-output-tokens "${REPAIR_MAX_OUTPUT_TOKENS:-16384}"
  --repair-limit "${REPAIR_LIMIT:-0}"
  --seed "${REPAIR_SEED:-42}"
  --poll-seconds "${BATCH_POLL_SECONDS:-60}"
)
exec "${PYTHON_BIN:-python}" methods/validity_repair/pipeline.py "${args[@]}" "$@"
