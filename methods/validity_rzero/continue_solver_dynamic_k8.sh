#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
# Continue the completed dynamic Solver-only round 1 through rounds 2-5.
# Source env_rzero.sh first; --resume resumes this continuation pipeline.
if [ "$#" -gt 1 ]; then
    echo "Usage: bash $0 [--resume]" >&2; exit 2
fi
case "${1:-}" in
    ""|--resume) ;;
    *) echo "Usage: bash $0 [--resume]" >&2; exit 2 ;;
esac
: "${STORAGE_PATH:?source env_rzero.sh first}"
unset RZERO_RUN_ROOT VALIDITY_RZERO_ARTIFACT_DIR
unset QUESTIONER_OUTPUT_DIR QUESTIONER_LOAD_CHECKPOINT SOLVER_LOAD_CHECKPOINT
unset SOLVER_TRAIN_FILES SOLVER_DATASET_READY SOLVER_PREPARE_ONLY SOLVER_DATASET_RECEIPT
unset SOLVER_LOG_FILE QUESTIONER_LOG_FILE
unset SOLVER_SKIP_MERGE SOLVER_SKIP_FINAL_EVAL
unset VALIDITY_RZERO_DIVERSITY_LAMBDA VALIDITY_RZERO_SEMANTIC_PANEL_SIZE VALIDITY_RZERO_SEMANTIC_PANEL_SEED
export BASE_MODEL=Qwen/Qwen3-4B-Base
export MODEL_ABBR=${SOLVER_DYNAMIC_RUN_NAME:-qwen3_4b_validity_rzero_semantic_novelty_gate_k8_solver_dynamic_mask_4gpu_v1}
export RZERO_FIRST_ROUND=2
export RZERO_INITIAL_QUESTIONER=$STORAGE_PATH/models/qwen3_4b_validity_rzero_semantic_novelty_gate_k8_solver_negative_4gpu_v1_questioner_v1/global_step_5/actor/huggingface
export VALIDITY_RZERO_INITIAL_SOLVER=$STORAGE_PATH/models/${MODEL_ABBR}_solver_v1/global_step_15/actor/huggingface
export TERRA_REPLAY_DATASET=jinyuan222/rzero-validity-rl-terra-v1-clean-v1
export TERRA_REPLAY_CONFIG=default
export TERRA_REPLAY_RATIO=0.1
export TERRA_REPLAY_SEED=1

# Exact original Questioner treatment, including INVALID = 0.5 - votes/9.
export VALIDITY_RZERO_VALIDITY_JUDGE_MODE=current_solver
export VALIDITY_RZERO_DOMAIN_MODE=none
export RZERO_QUESTION_BOX_FILTER=legacy
export VALIDITY_RZERO_DIVERSITY_MODE=semantic_novelty_gate
export VALIDITY_RZERO_NOVELTY_SCOPE=global
export VALIDITY_RZERO_NOVELTY_K=8
export VALIDITY_RZERO_NOVELTY_MIN_SAME_HITS=1
export VALIDITY_RZERO_NOVELTY_SEED=43
export VALIDITY_RZERO_NOVELTY_INVALID_REWARD=legacy
export VALIDITY_RZERO_SEMANTIC_MODEL=Qwen/Qwen3-4B-Base
export VALIDITY_RZERO_SEMANTIC_LOCAL_FILES_ONLY=1
export VALIDITY_RZERO_SEMANTIC_GPU_IDS=0,1,2,3
export VALIDITY_RZERO_SEMANTIC_GPU_MEMORY_UTILIZATION=0.80
export VALIDITY_RZERO_SEMANTIC_WORKER_BATCH_SIZE=8192
export QUESTIONER_TRAIN_GPU_IDS=0,1
export VLLM_GPU_IDS=2,3
export QUESTION_GPU_IDS=0,1,2,3

export RZERO_NUM_ROUNDS=5
export QUESTIONER_MAX_STEPS=5 QUESTIONER_MERGE_STEP=5
export QUESTIONER_ROLLOUT_BATCH_SIZE=512 QUESTIONER_ROLLOUT_N=4
export QUESTIONER_GLOBAL_BATCH_SIZE=4 QUESTIONER_MAX_RESPONSE_LENGTH=4096
export SOLVER_MAX_STEPS=15 SOLVER_MERGE_STEP=15
export SOLVER_SAVE_FREQ=3 SOLVER_SAVE_LIMIT=5 SOLVER_KEEP_LATEST_RESUME_STATE_ONLY=false
export SOLVER_ROLLOUT_BATCH_SIZE=512 SOLVER_MAX_RESPONSE_LENGTH=4096
export SOLVER_GENERATE_SAMPLES=2500
export SOLVER_TOTAL_EPOCHS=100 SOLVER_VAL_FREQ=4
export SOLVER_UPLOAD_MIN_SCORE=0.3 SOLVER_UPLOAD_MAX_SCORE=0.8

# Keep the successful dynamic-vote + full-entropy-masking Solver treatment.
export SOLVER_NEGATIVE_ONLY=1
export SOLVER_DYNAMIC_VOTE=1 SOLVER_TOKEN_MASKING=1
export SOLVER_EVAL_DUAL=1
export RECHECK_LOCAL_TMP_ROOT=/tmp
export RECHECK_STARTUP_TIMEOUT=3600
echo "Continuing rounds 2-5 from Solver v1: $VALIDITY_RZERO_INITIAL_SOLVER"
echo "Initial Questioner v1: $RZERO_INITIAL_QUESTIONER"
bash methods/validity_rzero/run.sh "$@"
