#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"
exec "${PYTHON_BIN:-python}" methods/validity_repair/label_parallel.py \
 --repair-dir "${REPAIR_DIR:-analysis_results/validity_repair_sol_sync_full_v1}" \
 --output-dir "${LABEL_OUTPUT_DIR:-analysis_results/validity_repair_solver_labels_4gpu_v1}" \
 --model "${LABEL_MODEL:-Qwen/Qwen3-4B-Base}" \
 --pair-limit "${PAIR_LIMIT:-0}" \
 --batch-size "${LABEL_BATCH_SIZE:-16}" "$@"
