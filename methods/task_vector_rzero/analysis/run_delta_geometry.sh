#!/usr/bin/env bash
set -euo pipefail

METHOD_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "$METHOD_DIR/../../.." && pwd)

RUN_ROOT=${RUN_ROOT:-/engrfs/project/jiaxinh/jinyuan/R-zero-storage/task_vector_rzero/qwen3_4b_relex_rank1_5round_noeval}
OUTPUT=${OUTPUT:-${RUN_ROOT}/analysis/delta_geometry_v1}
DEVICE=${DEVICE:-cuda}
CHUNK_ELEMENTS=${CHUNK_ELEMENTS:-1000000}
EVALUATION_CSV=${EVALUATION_CSV:-${METHOD_DIR}/evaluation_scores.csv}

export PYTHONPATH="${REPO_ROOT}:${PYTHONPATH:-}"

python3 -m methods.task_vector_rzero.analysis.analyze_delta_geometry \
    --run-root "$RUN_ROOT" \
    --output "$OUTPUT" \
    --device "$DEVICE" \
    --chunk-elements "$CHUNK_ELEMENTS" \
    --resume

python3 -m methods.task_vector_rzero.analysis.plot_delta_geometry \
    --analysis-root "$OUTPUT" \
    --evaluation-csv "$EVALUATION_CSV"

python3 -m methods.task_vector_rzero.analysis.build_report \
    --analysis-root "$OUTPUT"

echo "Delta geometry analysis complete: $OUTPUT"
