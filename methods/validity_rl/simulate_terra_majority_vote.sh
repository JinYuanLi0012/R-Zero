#!/usr/bin/env bash
set -euo pipefail

METHOD_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "${METHOD_DIR}/../.." && pwd)
cd "${REPO_ROOT}"
export PYTHONPATH="${REPO_ROOT}:${PYTHONPATH:-}"

if [[ -z "${STORAGE_PATH:-}" ]]; then
    echo "Set STORAGE_PATH before Terra vote simulation." >&2
    exit 2
fi

RUN_ROOT=${VALIDITY_VOTE_RUN_ROOT:-${VALIDITY_RUN_ROOT:-${STORAGE_PATH}/models/qwen3_4b_validity_rl_terra_v1}}
BASE_MODEL=${VALIDITY_VOTE_BASE_MODEL:-Qwen/Qwen3-4B-Base}
MODELS_STRING=${VALIDITY_VOTE_MODELS:-"base 5 10 15"}
GPU_IDS=${VALIDITY_VOTE_GPU_IDS:-0,1,2,3}
TENSOR_PARALLEL_SIZE=${VALIDITY_VOTE_TENSOR_PARALLEL_SIZE:-1}
EVAL_TAG=${VALIDITY_VOTE_EVAL_TAG:-$(date +%Y%m%d_%H%M%S)}
OUTPUT_ROOT=${VALIDITY_VOTE_OUTPUT_ROOT:-${RUN_ROOT}/evaluations/terra_vote_simulation_${EVAL_TAG}}
CACHE_ROOT=${VALIDITY_VOTE_CACHE_ROOT:-/tmp/rzero_validity_vote_${EVAL_TAG}}
SEED=${VALIDITY_VOTE_SEED:-0}
MAX_TOKENS=${VALIDITY_VOTE_MAX_TOKENS:-4096}
BATCH_SIZE=${VALIDITY_VOTE_BATCH_SIZE:-0}
JUDGE_MODEL=${RECHECK_JUDGE_MODEL:-gpt-5.6-luna}
JUDGE_EFFORT=${RECHECK_REASONING_EFFORT:-none}
JUDGE_MAX_TOKENS=${RECHECK_MAX_COMPLETION_TOKENS:-8}
SKIP_API_RECHECK=${VALIDITY_VOTE_SKIP_API_RECHECK:-0}

read -r -a MODEL_KEYS <<< "${MODELS_STRING}"
if [[ ${#MODEL_KEYS[@]} -eq 0 ]]; then
    echo "VALIDITY_VOTE_MODELS did not contain any models." >&2
    exit 2
fi
IFS=',' read -r -a GPU_ARRAY <<< "${GPU_IDS}"
if [[ "${TENSOR_PARALLEL_SIZE}" != "1" ]]; then
    echo "This launcher assigns one model per GPU; set VALIDITY_VOTE_TENSOR_PARALLEL_SIZE=1." >&2
    exit 2
fi
if [[ ${#GPU_ARRAY[@]} -lt ${#MODEL_KEYS[@]} ]]; then
    echo "Need at least ${#MODEL_KEYS[@]} GPU IDs for ${#MODEL_KEYS[@]} models; got ${GPU_IDS}." >&2
    exit 2
fi
if [[ "${VALIDITY_VOTE_DRY_RUN:-0}" != "1" \
    && "${SKIP_API_RECHECK}" != "1" \
    && -z "${OPENAI_API_KEY:-}" ]]; then
    echo "Set OPENAI_API_KEY for the formal final-math equivalence judge." >&2
    echo "For a non-formal local-only diagnostic, set VALIDITY_VOTE_SKIP_API_RECHECK=1." >&2
    exit 2
fi

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

mkdir -p "${OUTPUT_ROOT}/logs"

echo "Terra majority-vote architecture simulation"
echo "Models: ${MODEL_KEYS[*]}"
echo "GPUs: ${GPU_IDS} (one model per GPU, tensor parallel size 1)"
echo "Protocols: Two-stage 8+8 vs One-stage 16"
echo "Sampling: temperature=1.0, top_p=1.0, top_k=40, max_tokens=${MAX_TOKENS}"
echo "Seed: ${SEED}"
echo "Final math judge: ${JUDGE_MODEL} (reasoning_effort=${JUDGE_EFFORT})"
echo "Output root: ${OUTPUT_ROOT}"
echo "Compile cache root: ${CACHE_ROOT}"

PIDS=()
RUN_LABELS=()
LOG_FILES=()
for index in "${!MODEL_LABELS[@]}"; do
    MODEL_LABEL=${MODEL_LABELS[$index]}
    MODEL_PATH=${MODEL_PATHS[$index]}
    GPU_ID=${GPU_ARRAY[$index]}
    LOG_FILE="${OUTPUT_ROOT}/logs/${MODEL_LABEL}.log"
    MODEL_CACHE="${CACHE_ROOT}/${MODEL_LABEL}"
    COMMAND=(
        python3 methods/validity_rl/simulate_terra_majority_vote.py
        --model "${MODEL_PATH}"
        --model-label "${MODEL_LABEL}"
        --output-dir "${OUTPUT_ROOT}/${MODEL_LABEL}"
        --tensor-parallel-size "${TENSOR_PARALLEL_SIZE}"
        --seed "${SEED}"
        --max-tokens "${MAX_TOKENS}"
        --batch-size "${BATCH_SIZE}"
        --judge-model "${JUDGE_MODEL}"
        --judge-reasoning-effort "${JUDGE_EFFORT}"
        --judge-max-completion-tokens "${JUDGE_MAX_TOKENS}"
    )
    if [[ "${SKIP_API_RECHECK}" == "1" ]]; then
        COMMAND+=(--skip-api-recheck)
    fi
    if [[ "${VALIDITY_VOTE_ALLOW_EXISTING:-0}" == "1" ]]; then
        COMMAND+=(--allow-existing)
    fi

    echo "========== ${MODEL_LABEL} -> GPU ${GPU_ID}: ${MODEL_PATH} =========="
    if [[ "${VALIDITY_VOTE_DRY_RUN:-0}" == "1" ]]; then
        printf '%q ' \
            "CUDA_VISIBLE_DEVICES=${GPU_ID}" \
            "TMPDIR=${MODEL_CACHE}/tmp" \
            "TORCHINDUCTOR_CACHE_DIR=${MODEL_CACHE}/torchinductor" \
            "TRITON_CACHE_DIR=${MODEL_CACHE}/triton" \
            "${COMMAND[@]}"
        printf '\n'
    else
        mkdir -p \
            "${MODEL_CACHE}/tmp" \
            "${MODEL_CACHE}/torchinductor" \
            "${MODEL_CACHE}/triton"
        CUDA_VISIBLE_DEVICES="${GPU_ID}" \
        TMPDIR="${MODEL_CACHE}/tmp" \
        TORCHINDUCTOR_CACHE_DIR="${MODEL_CACHE}/torchinductor" \
        TRITON_CACHE_DIR="${MODEL_CACHE}/triton" \
            "${COMMAND[@]}" >"${LOG_FILE}" 2>&1 &
        MODEL_PID=$!
        PIDS+=("${MODEL_PID}")
        RUN_LABELS+=("${MODEL_LABEL}")
        LOG_FILES+=("${LOG_FILE}")
        echo "Started ${MODEL_LABEL} as PID ${MODEL_PID}; log: ${LOG_FILE}"
    fi
done

if [[ "${VALIDITY_VOTE_DRY_RUN:-0}" != "1" ]]; then
    FAILED=0
    for index in "${!PIDS[@]}"; do
        if wait "${PIDS[$index]}"; then
            echo "Finished ${RUN_LABELS[$index]}; log: ${LOG_FILES[$index]}"
        else
            EXIT_CODE=$?
            echo "Failed ${RUN_LABELS[$index]} with exit code ${EXIT_CODE}; log: ${LOG_FILES[$index]}" >&2
            FAILED=1
        fi
    done
    if [[ "${FAILED}" == "1" ]]; then
        echo "At least one model failed; comparison was not generated." >&2
        exit 1
    fi

    python3 methods/validity_rl/simulate_terra_majority_vote.py \
        --compare-dir "${OUTPUT_ROOT}"
fi

echo "Vote simulation artifacts: ${OUTPUT_ROOT}"
