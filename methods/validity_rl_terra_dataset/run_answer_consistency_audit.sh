#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 SOURCE_DIR [answer_consistency_audit.py options...]" >&2
  exit 2
fi

SOURCE_DIR=$1
shift
OUTPUT_DIR=${CONSISTENCY_OUTPUT_DIR:-analysis_results/validity_rl_terra_dataset_v1_answer_consistency_audit_v1}

"${PYTHON_BIN:-python3}" methods/validity_rl_terra_dataset/answer_consistency_audit.py \
  "$SOURCE_DIR" \
  --output-dir "$OUTPUT_DIR" \
  "$@"
