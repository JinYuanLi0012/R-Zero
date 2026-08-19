#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 CONSISTENCY_AUDIT_DIR [suspect_deep_review.py options...]" >&2
  exit 2
fi

AUDIT_DIR=$1
shift
OUTPUT_DIR=${DEEP_REVIEW_OUTPUT_DIR:-analysis_results/validity_rl_terra_dataset_v1_answer_deep_review_v1}

"${PYTHON_BIN:-python3}" methods/validity_rl_terra_dataset/suspect_deep_review.py \
  "$AUDIT_DIR" \
  --output-dir "$OUTPUT_DIR" \
  "$@"
