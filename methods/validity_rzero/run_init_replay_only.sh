#!/usr/bin/env bash
# Matched-teacher-data control: original R-Zero feedback, shared Solver init/replay.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
: "${STORAGE_PATH:?source env_rzero.sh or set STORAGE_PATH}"
export RZERO_INIT_REPLAY_ONLY=1
export VALIDITY_RZERO_ENABLED=0
export VALIDITY_RZERO_INITIAL_SOLVER=${VALIDITY_RZERO_INITIAL_SOLVER:-$STORAGE_PATH/models/qwen3_4b_validity_rl_terra_clean_v1/global_step_15/actor/huggingface}
export TERRA_REPLAY_DATASET=${TERRA_REPLAY_DATASET:-jinyuan222/rzero-validity-rl-terra-v1-clean-v1}
export TERRA_REPLAY_CONFIG=${TERRA_REPLAY_CONFIG:-default}
export TERRA_REPLAY_RATIO=${TERRA_REPLAY_RATIO:-0.1}
export TERRA_REPLAY_SEED=${TERRA_REPLAY_SEED:-1}
# Preserve standard R-Zero feedback and Solver updates; reject variant leakage.
for flag in SOLVER_NEGATIVE_ONLY SOLVER_DYNAMIC_VOTE SOLVER_TOKEN_MASKING; do
    if [ "${!flag:-0}" != "0" ]; then
        echo "$flag must be 0 for the matched R-Zero control" >&2; exit 2
    fi
done
export QUESTIONER_MAX_STEPS=${QUESTIONER_MAX_STEPS:-5}
export QUESTIONER_MERGE_STEP=${QUESTIONER_MERGE_STEP:-5}
export SOLVER_MAX_STEPS=${SOLVER_MAX_STEPS:-15}
export SOLVER_MERGE_STEP=${SOLVER_MERGE_STEP:-15}
export SOLVER_GENERATE_SAMPLES=${SOLVER_GENERATE_SAMPLES:-2500}
BASE_MODEL=${BASE_MODEL:-Qwen/Qwen3-4B-Base}
MODEL_ABBR=${MODEL_ABBR:-qwen3_4b_rzero_initstep15_replay10}
bash scripts/main.sh --no-eval "$@" "$BASE_MODEL" "$MODEL_ABBR"
