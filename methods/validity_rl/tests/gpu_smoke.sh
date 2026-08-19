#!/usr/bin/env bash
set -euo pipefail

METHOD_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
REPO_ROOT=$(cd "${METHOD_DIR}/../.." && pwd)
SMOKE_DIR=${VALIDITY_SMOKE_DATA_DIR:-${REPO_ROOT}/work/validity_rl_smoke_data}

cd "${REPO_ROOT}"
python3 "${METHOD_DIR}/prepare_dataset.py" \
    --output-dir "${SMOKE_DIR}" \
    --train-limit 2 \
    --validation-limit 1

VALIDITY_EXPERIMENT_NAME=${VALIDITY_EXPERIMENT_NAME:-qwen3_4b_validity_rl_smoke} \
VALIDITY_TRAIN_FILES="${SMOKE_DIR}/train.parquet" \
VALIDITY_VAL_FILES="${SMOKE_DIR}/validation.parquet" \
VALIDITY_ROLLOUT_BATCH_SIZE=2 \
VALIDITY_ACTOR_GLOBAL_BATCH_SIZE=2 \
VALIDITY_ROLLOUT_N=2 \
VALIDITY_MAX_RESPONSE_LENGTH=256 \
VALIDITY_TOTAL_EPOCHS=1 \
VALIDITY_MAX_STEPS=1 \
VALIDITY_SAVE_FREQ=1 \
VALIDITY_SAVE_LIMIT=1 \
VALIDITY_LOGGER='["console"]' \
VALIDITY_VAL_GENERATIONS_TO_LOG=1 \
bash "${METHOD_DIR}/train_validity_grpo.sh"
