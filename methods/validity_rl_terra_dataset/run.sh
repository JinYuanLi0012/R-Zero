#!/usr/bin/env bash
set -euo pipefail

METHOD_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
OUTPUT_DIR=${OUTPUT_DIR:-analysis_results/validity_rl_terra_dataset_v1}
MODEL=${MODEL:-gpt-5.6}
CONCURRENCY=${CONCURRENCY:-4}
PER_ROUND=${PER_ROUND:-460}
TRAIN_PER_ROUND=${TRAIN_PER_ROUND:-400}
SEED=${SEED:-42}

python3 "$METHOD_DIR/prepare.py" \
  --output-dir "$OUTPUT_DIR" \
  --seed "$SEED" \
  --per-round "$PER_ROUND" \
  --train-per-round "$TRAIN_PER_ROUND" \
  "$@"

python3 "$METHOD_DIR/annotate.py" \
  --input "$OUTPUT_DIR/terra_blind_input.jsonl" \
  --output-dir "$OUTPUT_DIR" \
  --model "$MODEL" \
  --concurrency "$CONCURRENCY"

python3 "$METHOD_DIR/finalize.py" --output-dir "$OUTPUT_DIR"
