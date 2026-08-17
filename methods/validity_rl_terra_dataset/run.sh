#!/usr/bin/env bash
set -euo pipefail

METHOD_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
OUTPUT_DIR=${OUTPUT_DIR:-analysis_results/validity_rl_terra_dataset_v1}
MODEL=${MODEL:-gpt-5.6-sol}
ANNOTATION_MODE=${ANNOTATION_MODE:-batch}
BATCH_POLL_SECONDS=${BATCH_POLL_SECONDS:-60}
CONCURRENCY=${CONCURRENCY:-4}
PER_ROUND=${PER_ROUND:-460}
TRAIN_PER_ROUND=${TRAIN_PER_ROUND:-400}
SEED=${SEED:-42}

echo "[pipeline] stage 1/3: prepare (output=$OUTPUT_DIR)"
python3 "$METHOD_DIR/prepare.py" \
  --output-dir "$OUTPUT_DIR" \
  --seed "$SEED" \
  --per-round "$PER_ROUND" \
  --train-per-round "$TRAIN_PER_ROUND" \
  "$@"

echo "[pipeline] stage 2/3: Terra annotation (model=$MODEL mode=$ANNOTATION_MODE)"
if [[ "$ANNOTATION_MODE" == "batch" ]]; then
  python3 "$METHOD_DIR/batch_annotate.py" \
    --input "$OUTPUT_DIR/terra_blind_input.jsonl" \
    --output-dir "$OUTPUT_DIR" \
    --model "$MODEL" \
    --poll-seconds "$BATCH_POLL_SECONDS"
elif [[ "$ANNOTATION_MODE" == "sync" ]]; then
  python3 "$METHOD_DIR/annotate.py" \
    --input "$OUTPUT_DIR/terra_blind_input.jsonl" \
    --output-dir "$OUTPUT_DIR" \
    --model "$MODEL" \
    --concurrency "$CONCURRENCY"
else
  echo "ANNOTATION_MODE must be batch or sync" >&2
  exit 2
fi

echo "[pipeline] stage 3/3: finalize and report"
python3 "$METHOD_DIR/finalize.py" --output-dir "$OUTPUT_DIR"
echo "[pipeline] complete: $OUTPUT_DIR/analysis/report.md"
