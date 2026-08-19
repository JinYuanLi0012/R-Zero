#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "Usage: $0 SOURCE_DIR CONSISTENCY_AUDIT_DIR DEEP_REVIEW_DIR" >&2
  exit 2
fi

SOURCE_DIR="$1"
AUDIT_DIR="$2"
DEEP_REVIEW_DIR="$3"
OUTPUT_DIR="${CLEAN_DATASET_OUTPUT_DIR:-analysis_results/validity_rl_terra_dataset_v1_clean_v1}"

python3 methods/validity_rl_terra_dataset/build_clean_dataset.py \
  "$SOURCE_DIR" "$AUDIT_DIR" "$DEEP_REVIEW_DIR" \
  --output-dir "$OUTPUT_DIR"
