#!/usr/bin/env bash
set -euo pipefail

METHOD_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "${METHOD_DIR}/../.." && pwd)
cd "${REPO_ROOT}"

if [[ -z "${STORAGE_PATH:-}" ]]; then
    echo "Set STORAGE_PATH before evaluation." >&2
    exit 2
fi

RUN_ROOT=${VALIDITY_RUN_ROOT:-${STORAGE_PATH}/models/qwen3_4b_validity_rl_terra_v1}
STEPS_STRING=${VALIDITY_EVAL_STEPS:-"5 10 15"}
GPU_IDS=${VALIDITY_EVAL_GPU_IDS:-0,1,2,3}
EVAL_TAG=${VALIDITY_EVAL_TAG:-$(date +%Y%m%d_%H%M%S)}
JUDGE_MODEL=${RECHECK_JUDGE_MODEL:-gpt-5.6-luna}
JUDGE_EFFORT=${RECHECK_REASONING_EFFORT:-none}
JUDGE_MAX_TOKENS=${RECHECK_MAX_COMPLETION_TOKENS:-8}

read -r -a STEPS <<< "${STEPS_STRING}"
if [[ ${#STEPS[@]} -eq 0 ]]; then
    echo "VALIDITY_EVAL_STEPS did not contain any checkpoint steps." >&2
    exit 2
fi

LOG_DIR="${RUN_ROOT}/logs/evaluation_${EVAL_TAG}"

echo "Validity-RL math evaluation"
echo "Run root: ${RUN_ROOT}"
echo "Steps: ${STEPS[*]}"
echo "GPUs: ${GPU_IDS}"
echo "Judge: ${JUDGE_MODEL} (reasoning_effort=${JUDGE_EFFORT})"
echo "Evaluation tag: ${EVAL_TAG}"

for step in "${STEPS[@]}"; do
    MODEL_PATH="${RUN_ROOT}/global_step_${step}/actor/huggingface"
    ARTIFACT_DIR="${RUN_ROOT}/evaluations/${EVAL_TAG}_step_${step}"

    if [[ ! -s "${MODEL_PATH}/config.json" ]]; then
        echo "Missing merged config: ${MODEL_PATH}/config.json" >&2
        exit 1
    fi
    if ! compgen -G "${MODEL_PATH}/*.safetensors" >/dev/null \
        && ! compgen -G "${MODEL_PATH}/*.bin" >/dev/null; then
        echo "Missing merged model weights: ${MODEL_PATH}" >&2
        exit 1
    fi
    if [[ -e "${ARTIFACT_DIR}/final_results.jsonl" \
        && "${VALIDITY_EVAL_ALLOW_EXISTING:-0}" != "1" ]]; then
        echo "Result already exists: ${ARTIFACT_DIR}/final_results.jsonl" >&2
        echo "Use a new VALIDITY_EVAL_TAG, or set VALIDITY_EVAL_ALLOW_EXISTING=1." >&2
        exit 1
    fi

    echo "========== Evaluating Validity-RL Step ${step} =========="
    COMMAND=(
        env
        "RECHECK_JUDGE_MODEL=${JUDGE_MODEL}"
        "RECHECK_REASONING_EFFORT=${JUDGE_EFFORT}"
        "RECHECK_MAX_COMPLETION_TOKENS=${JUDGE_MAX_TOKENS}"
        "EVAL_GPU_IDS=${GPU_IDS}"
        EVAL_MATH_ONLY=1
        "EVAL_ARTIFACT_DIR=${ARTIFACT_DIR}"
        "EVAL_LOG_DIR=${LOG_DIR}"
        "EVAL_RUN_ID=validity_rl_step_${step}_math"
        bash evaluation/evaluate.bash "${MODEL_PATH}"
    )

    if [[ "${VALIDITY_EVAL_DRY_RUN:-0}" == "1" ]]; then
        printf '%q ' "${COMMAND[@]}"
        printf '\n'
    else
        "${COMMAND[@]}"
    fi
done

echo "Evaluation artifacts:"
for step in "${STEPS[@]}"; do
    echo "  ${RUN_ROOT}/evaluations/${EVAL_TAG}_step_${step}/final_results.jsonl"
done
