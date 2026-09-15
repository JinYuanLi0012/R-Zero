#!/usr/bin/env bash
# Two-GPU OctoThinker Hybrid Base experiment. Run with bash; optionally --smoke.
set -euo pipefail
METHOD_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "${METHOD_DIR}/../.."
MODE=${1:-train}
[[ "$#" -le 1 && ( "$MODE" == train || "$MODE" == --smoke || "$MODE" == --resume ) ]] || {
    echo "Usage: bash $0 [--smoke|--resume]" >&2; exit 2;
}
: "${STORAGE_PATH:?Source env_rzero.sh or set STORAGE_PATH first}"
export VALIDITY_GPU_IDS=${VALIDITY_GPU_IDS:-${CUDA_VISIBLE_DEVICES:-0,1}}
IFS=',' read -r -a OCTO_GPUS <<< "$VALIDITY_GPU_IDS"
if [[ ${#OCTO_GPUS[@]} != 2 || -z "${OCTO_GPUS[0]}" || -z "${OCTO_GPUS[1]}" || "${OCTO_GPUS[0]}" == "${OCTO_GPUS[1]}" ]]; then
    echo "This entry requires two GPUs. Set VALIDITY_GPU_IDS=0,1 (or two allocated IDs)." >&2
    exit 2
fi
export VALIDITY_NUM_GPUS=2
export VALIDITY_TENSOR_PARALLEL_SIZE=2
export VALIDITY_MODEL_PATH=${VALIDITY_MODEL_PATH:-OctoThinker/OctoThinker-3B-Hybrid-Base}
export VALIDITY_DATASET=${VALIDITY_DATASET:-jinyuan222/rzero-validity-rl-terra-v1-clean-v1}
export VALIDITY_CHAT_TEMPLATE_FILE="${METHOD_DIR}/octothinker_chat.jinja"
export VALIDITY_LOGGER=${VALIDITY_LOGGER:-'["console","wandb"]'}
export VALIDITY_VAL_BATCH_SIZE=16
export VALIDITY_GPU_MEMORY_UTILIZATION=${VALIDITY_GPU_MEMORY_UTILIZATION:-0.6}
RUN_NAME=octothinker_3b_hybrid_validity_rl_terra_clean_v1
if [[ "$MODE" == --smoke ]]; then
    RUN_NAME="${RUN_NAME}_smoke"
    export VALIDITY_ROLLOUT_BATCH_SIZE=2 VALIDITY_ACTOR_GLOBAL_BATCH_SIZE=2
    export VALIDITY_ROLLOUT_N=2 VALIDITY_MAX_RESPONSE_LENGTH=256
    export VALIDITY_TOTAL_EPOCHS=1 VALIDITY_MAX_STEPS=1
    export VALIDITY_SAVE_FREQ=1 VALIDITY_SAVE_LIMIT=1
    export VALIDITY_VAL_GENERATIONS_TO_LOG=1
fi
export VALIDITY_EXPERIMENT_NAME=${VALIDITY_EXPERIMENT_NAME:-$RUN_NAME}
export VALIDITY_SAVE_PATH=${VALIDITY_SAVE_PATH:-${STORAGE_PATH}/models/${VALIDITY_EXPERIMENT_NAME}}
DATA_DIR="${VALIDITY_SAVE_PATH}/data"
# Always bind this run to the audited files, even if old overrides remain in
# the shell from another experiment.
export VALIDITY_TRAIN_FILES="${DATA_DIR}/train.parquet"
export VALIDITY_VAL_FILES="${DATA_DIR}/validation.parquet"
unset VALIDITY_LOAD_CHECKPOINT
if [[ "$MODE" == --resume ]]; then
    # Validate the committed recovery point, not the highest directory name.
    # Reuse the original parquet files so dataloader state remains meaningful.
    VALIDITY_LOAD_CHECKPOINT=$(python3 "${METHOD_DIR}/resume_checkpoint.py" \
        --root "$VALIDITY_SAVE_PATH" --dataset "$VALIDITY_DATASET" \
        --max-steps "${VALIDITY_MAX_STEPS:-15}")
    export VALIDITY_LOAD_CHECKPOINT
    echo "Resuming from ${VALIDITY_LOAD_CHECKPOINT}; target step ${VALIDITY_MAX_STEPS:-15}"
elif [[ "${VALIDITY_DRY_RUN:-0}" != 1 ]]; then
    if [[ -e "${VALIDITY_SAVE_PATH}/latest_global_step.txt" ]]; then
        echo "Run already has a checkpoint: ${VALIDITY_SAVE_PATH}. Choose a new experiment name." >&2
        exit 2
    fi
    PREPARE_ARGS=(--dataset "$VALIDITY_DATASET" --output-dir "$DATA_DIR")
    if [[ "$MODE" == --smoke ]]; then
        PREPARE_ARGS+=(--train-limit 2 --validation-limit 1)
    else
        PREPARE_ARGS+=(--full)
    fi
    python3 "${METHOD_DIR}/prepare_dataset.py" "${PREPARE_ARGS[@]}"
fi
bash "${METHOD_DIR}/train_validity_grpo.sh"
