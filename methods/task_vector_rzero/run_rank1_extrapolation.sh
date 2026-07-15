#!/usr/bin/env bash
set -euo pipefail

METHOD_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "$METHOD_DIR/../.." && pwd)
CONFIG_PATH="$METHOD_DIR/config.sh"
SOURCE_RUN_NAME=""
OUTPUT_RUN_NAME=""
SCALES_CSV="1,2,3,4,5"
RESUME=0
FULL_LOAD_OVERRIDE=""

usage() {
    cat <<EOF
Usage: bash methods/task_vector_rzero/run_rank1_extrapolation.sh \\
  --source-run NAME --output-run NAME [options]

Builds V_k = Base + scale_k * (round-1 Rank-1 model - Base) from a completed
RELEX Rank-1 task-vector run. The source run is read-only.

Options:
  --config PATH          Config providing STORAGE_PATH and validation defaults.
  --scales CSV           Output scales in order (default: 1,2,3,4,5).
  --resume               Validate and reuse already completed outputs.
  --full-load-validate   Load every output with Transformers after composition.
  --no-full-load-validate
EOF
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --config)
            CONFIG_PATH=$2
            shift 2
            ;;
        --source-run)
            SOURCE_RUN_NAME=$2
            shift 2
            ;;
        --output-run)
            OUTPUT_RUN_NAME=$2
            shift 2
            ;;
        --scales)
            SCALES_CSV=$2
            shift 2
            ;;
        --resume)
            RESUME=1
            shift
            ;;
        --full-load-validate)
            FULL_LOAD_OVERRIDE=true
            shift
            ;;
        --no-full-load-validate)
            FULL_LOAD_OVERRIDE=false
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown argument: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
done

if [ ! -f "$CONFIG_PATH" ]; then
    echo "Config does not exist: $CONFIG_PATH" >&2
    exit 2
fi
if [ -z "$SOURCE_RUN_NAME" ] || [ -z "$OUTPUT_RUN_NAME" ]; then
    echo "--source-run and --output-run are required" >&2
    usage >&2
    exit 2
fi
if [[ "$SOURCE_RUN_NAME" == */* ]] || [[ "$OUTPUT_RUN_NAME" == */* ]]; then
    echo "Run names must not contain '/'" >&2
    exit 2
fi

export TASK_VECTOR_METHOD=relex_rank1
# shellcheck source=config.sh
source "$CONFIG_PATH"
: "${FULL_LOAD_VALIDATE:=true}"
if [ -n "$FULL_LOAD_OVERRIDE" ]; then
    FULL_LOAD_VALIDATE=$FULL_LOAD_OVERRIDE
fi

SOURCE_RUN_ROOT="${STORAGE_PATH}/task_vector_rzero/${SOURCE_RUN_NAME}"
OUTPUT_ROOT="${STORAGE_PATH}/task_vector_rzero_extrapolation/${OUTPUT_RUN_NAME}"
IFS=',' read -r -a SCALES <<< "$SCALES_CSV"
if [ "${#SCALES[@]}" -eq 0 ]; then
    echo "--scales must contain at least one value" >&2
    exit 2
fi

ARGS=(
    --source-run-root "$SOURCE_RUN_ROOT"
    --output-root "$OUTPUT_ROOT"
    --chunk-elements "$TASK_VECTOR_CHUNK_ELEMENTS"
)
for scale in "${SCALES[@]}"; do
    if [ -z "$scale" ]; then
        echo "--scales contains an empty value" >&2
        exit 2
    fi
    ARGS+=(--scale "$scale")
done
if [ "$RESUME" = "1" ]; then
    ARGS+=(--resume)
fi

cd "$REPO_ROOT"
export PYTHONPATH="${REPO_ROOT}:${PYTHONPATH:-}"
echo "Round-1 Rank-1 delta extrapolation"
echo "  source run: $SOURCE_RUN_ROOT"
echo "  output root: $OUTPUT_ROOT"
echo "  scales: $SCALES_CSV"
echo "  full-load validation: $FULL_LOAD_VALIDATE"
python3 "$METHOD_DIR/extrapolate_rank1.py" "${ARGS[@]}"

for index in "${!SCALES[@]}"; do
    model="$OUTPUT_ROOT/composed_solvers/v$((index + 1))"
    if [ "$FULL_LOAD_VALIDATE" = "true" ]; then
        python3 "$METHOD_DIR/validate_checkpoint.py" "$model" --full-load
    else
        python3 "$METHOD_DIR/validate_checkpoint.py" "$model"
    fi
done

echo "Rank-1 extrapolation completed successfully."
echo "Models: $OUTPUT_ROOT/composed_solvers/v1...v${#SCALES[@]}"
