#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 4 ]; then
    cat >&2 <<EOF
Usage: $0 BASE_MODEL EXISTING_V1 SECOND_ROUND_DATASET OUTPUT_ROOT

SECOND_ROUND_DATASET may be a local Parquet file or an HF dataset such as
jinyuan222/repo@train. This trains only A2 from Base, composes V2, and evaluates
only the composed V2. Existing Base, V1, and standard V2 are not reevaluated.
EOF
    exit 2
fi

BASE_MODEL=$1
EXISTING_V1=$2
SECOND_ROUND_DATASET=$3
OUTPUT_ROOT=$4
METHOD_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "$METHOD_DIR/../.." && pwd)
cd "$REPO_ROOT"

if [ -e "$OUTPUT_ROOT" ]; then
    echo "OUTPUT_ROOT already exists: $OUTPUT_ROOT" >&2
    exit 2
fi
mkdir -p "$OUTPUT_ROOT/logs"

BASE_MODEL_SOURCE=$BASE_MODEL
mkdir -p "$OUTPUT_ROOT/state"
BASE_RESOLVE_ARGS=(
    --model "$BASE_MODEL_SOURCE"
    --manifest "$OUTPUT_ROOT/state/base_manifest.json"
)
if [ -n "${BASE_REVISION:-}" ]; then
    BASE_RESOLVE_ARGS+=(--revision "$BASE_REVISION")
fi
BASE_RESOLUTION=$(python3 "$METHOD_DIR/resolve_base.py" "${BASE_RESOLVE_ARGS[@]}")
BASE_MODEL=$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["resolved_path"])' "$BASE_RESOLUTION")

A2_DIR="$OUTPUT_ROOT/base_fit_a2"
A2_HF="$A2_DIR/global_step_${SOLVER_MERGE_STEP:-15}/actor/huggingface"
COMPOSED_V2="$OUTPUT_ROOT/composed_v2"

bash "$METHOD_DIR/train_base_fit.sh" \
    "$BASE_MODEL" "$SECOND_ROUND_DATASET" "$A2_DIR" taskvec_validation_basefit_v2 \
    > >(tee -a "$OUTPUT_ROOT/logs/base_fit_a2.log") 2>&1

python3 "$METHOD_DIR/compose_task_vectors.py" \
    --base "$BASE_MODEL" \
    --base-provenance "$OUTPUT_ROOT/state/base_manifest.json" \
    --auxiliary "$EXISTING_V1" --scale "${TASK_VECTOR_SCALE_V1:-1}" \
    --auxiliary "$A2_HF" --scale "${TASK_VECTOR_SCALE_V2:-1}" \
    --output "$COMPOSED_V2" \
    --chunk-elements "${TASK_VECTOR_CHUNK_ELEMENTS:-8000000}" \
    > >(tee -a "$OUTPUT_ROOT/logs/compose_v2.log") 2>&1

python3 "$METHOD_DIR/validate_checkpoint.py" "$COMPOSED_V2" --full-load

if [ "${SKIP_COMPOSED_V2_EVAL:-false}" != "true" ]; then
    mkdir -p "$OUTPUT_ROOT/evaluation"
    STORAGE_PATH="$OUTPUT_ROOT/evaluation" \
    EVAL_ARTIFACT_DIR="$OUTPUT_ROOT/evaluation" \
    EVAL_LOG_DIR="$OUTPUT_ROOT/evaluation/logs" \
        bash evaluation/evaluate.bash "$COMPOSED_V2" \
            > >(tee -a "$OUTPUT_ROOT/logs/evaluate_v2.log") 2>&1
fi

echo "Existing-artifact V2 validation complete: $COMPOSED_V2"
