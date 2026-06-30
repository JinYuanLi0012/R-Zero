#!/bin/bash
set -e

# Formal Qwen3-4B full R-Zero run. Source env_rzero.sh before invoking this script.
BASE_MODEL=${BASE_MODEL:-Qwen/Qwen3-4B-Base}
MODEL_ABBR=${MODEL_ABBR:-qwen3_4b_fullrun_0619}

export QUESTIONER_TRAIN_GPU_IDS=${QUESTIONER_TRAIN_GPU_IDS:-4,5}
export VLLM_GPU_IDS=${VLLM_GPU_IDS:-6,7}
export VLLM_PORT_BASE=${VLLM_PORT_BASE:-5100}
export QUESTION_GPU_IDS=${QUESTION_GPU_IDS:-4,5,6,7}

# Do not let smoke-test overrides leak into the formal run.
unset QUESTIONER_MAX_STEPS
unset QUESTIONER_SKIP_MERGE
unset QUESTIONER_MERGE_STEP
unset QUESTIONER_LOG_FILE
unset SOLVER_GENERATE_SAMPLES
unset SOLVER_MAX_STEPS
unset SOLVER_MERGE_STEP
unset SOLVER_SKIP_MERGE
unset SOLVER_SKIP_FINAL_EVAL
unset SOLVER_LOG_FILE

bash scripts/main.sh "$BASE_MODEL" "$MODEL_ABBR"
