#!/usr/bin/env bash
set -euo pipefail

METHOD_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "${METHOD_DIR}/../.." && pwd)
cd "${REPO_ROOT}"

if [[ -z "${STORAGE_PATH:-}" ]]; then
    echo "Set STORAGE_PATH before Terra validation evaluation." >&2
    exit 2
fi

RUN_ROOT=${VALIDITY_RUN_ROOT:-${STORAGE_PATH}/models/qwen3_4b_validity_rl_terra_v1}
BASE_MODEL=${VALIDITY_TERRA_BASE_MODEL:-Qwen/Qwen3-4B-Base}
MODELS_STRING=${VALIDITY_TERRA_MODELS:-"base 5 10 15"}
GPU_IDS=${VALIDITY_TERRA_GPU_IDS:-${CUDA_VISIBLE_DEVICES:-0,1,2,3}}
IFS=',' read -r -a GPU_ARRAY <<< "${GPU_IDS}"
TENSOR_PARALLEL_SIZE=${VALIDITY_TERRA_TENSOR_PARALLEL_SIZE:-${#GPU_ARRAY[@]}}
EVAL_TAG=${VALIDITY_TERRA_EVAL_TAG:-$(date +%Y%m%d_%H%M%S)}
OUTPUT_ROOT=${VALIDITY_TERRA_OUTPUT_ROOT:-${RUN_ROOT}/evaluations/terra_validation_${EVAL_TAG}}
JUDGE_MODEL=${RECHECK_JUDGE_MODEL:-gpt-5.6-luna}
JUDGE_EFFORT=${RECHECK_REASONING_EFFORT:-none}
JUDGE_MAX_TOKENS=${RECHECK_MAX_COMPLETION_TOKENS:-8}
SKIP_API_RECHECK=${VALIDITY_TERRA_SKIP_API_RECHECK:-0}

read -r -a MODEL_KEYS <<< "${MODELS_STRING}"
if [[ ${#MODEL_KEYS[@]} -eq 0 ]]; then
    echo "VALIDITY_TERRA_MODELS did not contain any models." >&2
    exit 2
fi
if [[ "${VALIDITY_TERRA_DRY_RUN:-0}" != "1" \
    && "${SKIP_API_RECHECK}" != "1" \
    && -z "${OPENAI_API_KEY:-}" ]]; then
    echo "Set OPENAI_API_KEY for the R-Zero-style math answer recheck." >&2
    echo "For an explicitly local-only diagnostic, set VALIDITY_TERRA_SKIP_API_RECHECK=1." >&2
    exit 2
fi

mkdir -p "${OUTPUT_ROOT}"

MODEL_LABELS=()
MODEL_PATHS=()
for key in "${MODEL_KEYS[@]}"; do
    if [[ "${key}" == "base" ]]; then
        MODEL_LABELS+=(base)
        MODEL_PATHS+=("${BASE_MODEL}")
    elif [[ "${key}" =~ ^(5|10|15)$ ]]; then
        MODEL_LABELS+=("step_${key}")
        MODEL_PATH="${RUN_ROOT}/global_step_${key}/actor/huggingface"
        if [[ ! -s "${MODEL_PATH}/config.json" ]]; then
            echo "Missing merged config: ${MODEL_PATH}/config.json" >&2
            exit 1
        fi
        if ! compgen -G "${MODEL_PATH}/*.safetensors" >/dev/null \
            && ! compgen -G "${MODEL_PATH}/*.bin" >/dev/null; then
            echo "Missing merged model weights: ${MODEL_PATH}" >&2
            exit 1
        fi
        MODEL_PATHS+=("${MODEL_PATH}")
    else
        echo "Unknown model key '${key}'; use base, 5, 10, and/or 15." >&2
        exit 2
    fi
done

echo "Terra held-out validity evaluation"
echo "Models: ${MODEL_KEYS[*]}"
echo "GPUs: ${GPU_IDS} (tensor parallel size ${TENSOR_PARALLEL_SIZE})"
echo "Protocol: n=1, temperature=0.0, max_tokens=4096"
echo "Judge: ${JUDGE_MODEL} (reasoning_effort=${JUDGE_EFFORT})"
echo "Output root: ${OUTPUT_ROOT}"

for index in "${!MODEL_LABELS[@]}"; do
    MODEL_LABEL=${MODEL_LABELS[$index]}
    MODEL_PATH=${MODEL_PATHS[$index]}

    COMMAND=(
        python3 methods/validity_rl/evaluate_terra_validation.py
        --model "${MODEL_PATH}"
        --model-label "${MODEL_LABEL}"
        --output-dir "${OUTPUT_ROOT}/${MODEL_LABEL}"
        --tensor-parallel-size "${TENSOR_PARALLEL_SIZE}"
        --judge-model "${JUDGE_MODEL}"
        --judge-reasoning-effort "${JUDGE_EFFORT}"
        --judge-max-completion-tokens "${JUDGE_MAX_TOKENS}"
    )
    if [[ "${SKIP_API_RECHECK}" == "1" ]]; then
        COMMAND+=(--skip-api-recheck)
    fi
    if [[ "${VALIDITY_TERRA_ALLOW_EXISTING:-0}" == "1" ]]; then
        COMMAND+=(--allow-existing)
    fi

    echo "========== Evaluating ${MODEL_LABEL}: ${MODEL_PATH} =========="
    if [[ "${VALIDITY_TERRA_DRY_RUN:-0}" == "1" ]]; then
        printf '%q ' "CUDA_VISIBLE_DEVICES=${GPU_IDS}" "${COMMAND[@]}"
        printf '\n'
    else
        CUDA_VISIBLE_DEVICES="${GPU_IDS}" "${COMMAND[@]}"
    fi
done

if [[ "${VALIDITY_TERRA_DRY_RUN:-0}" != "1" ]]; then
    python3 methods/validity_rl/evaluate_terra_validation.py --compare-dir "${OUTPUT_ROOT}"
fi

echo "Terra evaluation artifacts: ${OUTPUT_ROOT}"
