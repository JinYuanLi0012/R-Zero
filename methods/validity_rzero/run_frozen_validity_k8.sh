#!/usr/bin/env bash
# Original global K8 treatment + fixed Step-15 validity judge + zero replay.
set -euo pipefail
METHOD_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$METHOD_DIR/../.."

smoke=0
if [ "${1:-}" = "--smoke" ]; then
    smoke=1
    shift
fi
export VALIDITY_RZERO_ENABLED=1
export VALIDITY_RZERO_VALIDITY_JUDGE_MODE=frozen
export VALIDITY_RZERO_VALIDITY_JUDGE_MODEL=${VALIDITY_RZERO_VALIDITY_JUDGE_MODEL:-${STORAGE_PATH:?source env_rzero.sh}/models/qwen3_4b_validity_rl_terra_clean_v1/global_step_15/actor/huggingface}
export VALIDITY_RZERO_INITIAL_SOLVER="$VALIDITY_RZERO_VALIDITY_JUDGE_MODEL"
export TERRA_REPLAY_RATIO=0
export TERRA_REPLAY_DATASET=""
export TERRA_REPLAY_CONFIG=default
export TERRA_REPLAY_SEED=1

export BASE_MODEL=Qwen/Qwen3-4B-Base
export VALIDITY_RZERO_DIVERSITY_MODE=semantic_novelty_gate
export VALIDITY_RZERO_NOVELTY_K=8
export VALIDITY_RZERO_NOVELTY_MIN_SAME_HITS=1
export VALIDITY_RZERO_NOVELTY_SEED=43
export VALIDITY_RZERO_NOVELTY_SCOPE=global
export VALIDITY_RZERO_NOVELTY_INVALID_REWARD=legacy
export VALIDITY_RZERO_DOMAIN_MODE=none
export RZERO_QUESTION_BOX_FILTER=legacy
export VALIDITY_RZERO_PROMPT="$METHOD_DIR/../validity_rl/validity_solver.jinja"
export VALIDITY_RZERO_SEMANTIC_MODEL=Qwen/Qwen3-4B-Base
export VALIDITY_RZERO_SEMANTIC_LOCAL_FILES_ONLY=1
export VALIDITY_RZERO_SEMANTIC_GPU_IDS=0,1,2,3
export VALIDITY_RZERO_SEMANTIC_GPU_MEMORY_UTILIZATION=0.80
export VALIDITY_RZERO_SEMANTIC_WORKER_BATCH_SIZE=8192
export QUESTIONER_TRAIN_GPU_IDS=0,1
export VLLM_GPU_IDS=2,3
export QUESTION_GPU_IDS=0,1,2,3
export SOLVER_GENERATE_SAMPLES=${SOLVER_GENERATE_SAMPLES:-2500}

if [ "$smoke" = "1" ]; then
    export MODEL_ABBR=${MODEL_ABBR:-qwen3_4b_validity_rzero_k8_frozenstep15_noreplay_smoke_v1}
    bash "$METHOD_DIR/tests/gpu_smoke.sh" "$@"
else
    export MODEL_ABBR=${MODEL_ABBR:-qwen3_4b_validity_rzero_k8_frozenstep15_noreplay_v1}
    bash "$METHOD_DIR/run.sh" "$@"
fi
