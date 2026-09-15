#!/usr/bin/env bash
# Original Terra validation (297 rows), original API recheck, two-GPU inference.
set -euo pipefail
METHOD_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "${METHOD_DIR}/../.."
: "${STORAGE_PATH:?Source env_rzero.sh or set STORAGE_PATH first}"
export VALIDITY_RUN_ROOT=${VALIDITY_RUN_ROOT:-${STORAGE_PATH}/models/octothinker_3b_hybrid_validity_rl_terra_clean_v1}
export VALIDITY_TERRA_MODEL_ROOT=${VALIDITY_TERRA_MODEL_ROOT:-${VALIDITY_RUN_ROOT}/evaluation_models}
export VALIDITY_TERRA_BASE_MODEL=${VALIDITY_TERRA_BASE_MODEL:-OctoThinker/OctoThinker-3B-Hybrid-Base}
export VALIDITY_TERRA_MODELS=${VALIDITY_TERRA_MODELS:-"5 10 15"}
export VALIDITY_TERRA_GPU_IDS=${VALIDITY_TERRA_GPU_IDS:-${VALIDITY_GPU_IDS:-${CUDA_VISIBLE_DEVICES:-0,1}}}
IFS=',' read -r -a GPUS <<< "$VALIDITY_TERRA_GPU_IDS"
if [[ ${#GPUS[@]} != 2 || -z "${GPUS[0]}" || -z "${GPUS[1]}" || "${GPUS[0]}" == "${GPUS[1]}" ]]; then
    echo "Set VALIDITY_TERRA_GPU_IDS to two distinct allocated GPU IDs." >&2; exit 2
fi
export VALIDITY_TERRA_TENSOR_PARALLEL_SIZE=2
export VALIDITY_TERRA_CHAT_TEMPLATE_FILE="${METHOD_DIR}/octothinker_chat.jinja"
export VALIDITY_TERRA_SKIP_API_RECHECK=${VALIDITY_TERRA_SKIP_API_RECHECK:-0}
if [[ "$VALIDITY_TERRA_SKIP_API_RECHECK" != 1 && -z "${OPENAI_API_KEY:-}" ]]; then
    echo "Set OPENAI_API_KEY for the existing Terra math-answer API recheck." >&2; exit 2
fi
read -r -a MODEL_KEYS <<< "$VALIDITY_TERRA_MODELS"
STEPS=()
for key in "${MODEL_KEYS[@]}"; do
    case "$key" in
        base) ;;
        5|10|15) STEPS+=("$key") ;;
        *) echo "Unknown model '$key'; use base, 5, 10, 15." >&2; exit 2 ;;
    esac
done
if [[ ${#MODEL_KEYS[@]} == 0 ]]; then
    echo "No models requested." >&2; exit 2
fi
if [[ ${#STEPS[@]} != 0 ]]; then
    python3 "${METHOD_DIR}/prepare_octothinker_eval.py" \
        --run-root "$VALIDITY_RUN_ROOT" --output-root "$VALIDITY_TERRA_MODEL_ROOT" \
        --steps "${STEPS[@]}"
fi
bash "${METHOD_DIR}/evaluate_terra_validation.sh"
