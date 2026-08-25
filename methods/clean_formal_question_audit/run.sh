#!/usr/bin/env bash
set -euo pipefail

METHOD_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
DATA_DIR=${DATA_DIR:-/engrfs/project/jiaxinh/jinyuan/R-zero-storage/rzero_runs/qwen3_4b_validity_rzero_clean_formal_v1/datasets}
OUTPUT_DIR=${OUTPUT_DIR:-analysis_results/clean_formal_v1_question_audit_terra_sync_300}
PER_ROUND=${PER_ROUND:-300}
SEED=${SEED:-42}
MODEL=${MODEL:-gpt-5.6-terra}
ANNOTATION_MODE=${ANNOTATION_MODE:-sync}
CONCURRENCY=${CONCURRENCY:-8}
REASONING_EFFORT=${REASONING_EFFORT:-high}
MAX_OUTPUT_TOKENS=${MAX_OUTPUT_TOKENS:-16384}
MAX_ATTEMPTS=${MAX_ATTEMPTS:-3}
MIN_CONFIDENCE=${MIN_CONFIDENCE:-0.8}
BATCH_POLL_SECONDS=${BATCH_POLL_SECONDS:-60}

echo "[pipeline] stage 1/3: sample (data=$DATA_DIR output=$OUTPUT_DIR per_round=$PER_ROUND)"
python3 "$METHOD_DIR/prepare.py" \
  --data-dir "$DATA_DIR" \
  --output-dir "$OUTPUT_DIR" \
  --per-round "$PER_ROUND" \
  --seed "$SEED"

echo "[pipeline] stage 2/3: annotation (model=$MODEL mode=$ANNOTATION_MODE)"
if [[ "$ANNOTATION_MODE" == "sync" ]]; then
  python3 "$METHOD_DIR/sync_annotate.py" \
    --input "$OUTPUT_DIR/terra_blind_input.jsonl" \
    --sampled "$OUTPUT_DIR/sampled_questions.jsonl" \
    --output-dir "$OUTPUT_DIR" \
    --model "$MODEL" \
    --reasoning-effort "$REASONING_EFFORT" \
    --max-output-tokens "$MAX_OUTPUT_TOKENS" \
    --max-attempts "$MAX_ATTEMPTS" \
    --min-confidence "$MIN_CONFIDENCE" \
    --concurrency "$CONCURRENCY"
elif [[ "$ANNOTATION_MODE" == "batch" ]]; then
  python3 "$METHOD_DIR/annotate.py" \
    --input "$OUTPUT_DIR/terra_blind_input.jsonl" \
    --sampled "$OUTPUT_DIR/sampled_questions.jsonl" \
    --output-dir "$OUTPUT_DIR" \
    --model "$MODEL" \
    --reasoning-effort "$REASONING_EFFORT" \
    --max-output-tokens "$MAX_OUTPUT_TOKENS" \
    --max-attempts "$MAX_ATTEMPTS" \
    --min-confidence "$MIN_CONFIDENCE" \
    --poll-seconds "$BATCH_POLL_SECONDS"
else
  echo "ANNOTATION_MODE must be sync or batch (got: $ANNOTATION_MODE)" >&2
  exit 2
fi

echo "[pipeline] stage 3/3: aggregate and report"
python3 "$METHOD_DIR/finalize.py" --output-dir "$OUTPUT_DIR"

echo "[pipeline] complete: $OUTPUT_DIR/analysis/report.md"
