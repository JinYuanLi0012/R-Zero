#!/usr/bin/env bash
# Original K8 one-hit gate experiment, all three roles switched to OctoThinker.
set -euo pipefail
METHOD_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "${METHOD_DIR}/../.."
if [[ $# -gt 1 || ( $# -eq 1 && "$1" != --resume ) ]]; then
    echo "Usage: bash $0 [--resume]" >&2; exit 2
fi
: "${STORAGE_PATH:?Source env_rzero.sh first}"
: "${HUGGINGFACENAME:?Source env_rzero.sh first (datasets are uploaded under this namespace)}"
export PYTHONPATH="${PWD}:${PYTHONPATH:-}"
export MODEL_ABBR=${OCTO_MODEL_ABBR:-octothinker_3b_hybrid_validity_rzero_semantic_novelty_gate_k8_4gpu_v1}
export RZERO_NUM_ROUNDS=${OCTO_NUM_ROUNDS:-5}
# Isolate this experiment from Qwen/continuation settings left in the shell.
unset RZERO_RUN_ROOT VALIDITY_RZERO_ARTIFACT_DIR QUESTIONER_OUTPUT_DIR SOLVER_TRAIN_FILES
unset QUESTIONER_LOAD_CHECKPOINT SOLVER_LOAD_CHECKPOINT
unset SOLVER_DATASET_READY SOLVER_PREPARE_ONLY SOLVER_DATASET_RECEIPT
unset VALIDITY_RZERO_FROZEN_GATE_FILE VALIDITY_RZERO_VALIDITY_JUDGE_MODEL
unset VALIDITY_RZERO_DIVERSITY_LAMBDA VALIDITY_RZERO_SEMANTIC_PANEL_SIZE VALIDITY_RZERO_SEMANTIC_PANEL_SEED
export RZERO_FIRST_ROUND=1
export SOLVER_NEGATIVE_ONLY=0 SOLVER_DYNAMIC_VOTE=0 SOLVER_TOKEN_MASKING=0 SOLVER_EVAL_DUAL=0
export VALIDITY_RZERO_DOMAIN_MODE=none VALIDITY_RZERO_NOVELTY_SCOPE=global
export VALIDITY_RZERO_MODEL_FAMILY=octothinker
export VALIDITY_RZERO_VALIDITY_JUDGE_MODE=current_solver
export VALIDITY_RZERO_DIVERSITY_MODE=semantic_novelty_gate
export VALIDITY_RZERO_NOVELTY_K=8 VALIDITY_RZERO_NOVELTY_MIN_SAME_HITS=1 VALIDITY_RZERO_NOVELTY_SEED=43
export VALIDITY_RZERO_NOVELTY_INVALID_REWARD=legacy
export TERRA_REPLAY_DATASET=jinyuan222/rzero-validity-rl-terra-v1-clean-v1
export TERRA_REPLAY_CONFIG=default TERRA_REPLAY_RATIO=0.1 TERRA_REPLAY_SEED=1
export QUESTION_GPU_IDS=0,1,2,3 QUESTIONER_TRAIN_GPU_IDS=0,1 VLLM_GPU_IDS=2,3
export VALIDITY_RZERO_SEMANTIC_GPU_IDS=0,1,2,3
export VALIDITY_RZERO_SEMANTIC_GPU_MEMORY_UTILIZATION=0.80
export VALIDITY_RZERO_SEMANTIC_WORKER_BATCH_SIZE=8192
export VALIDITY_RZERO_SEMANTIC_LOCAL_FILES_ONLY=1
export QUESTIONER_MAX_STEPS=5 QUESTIONER_MERGE_STEP=5 SOLVER_MAX_STEPS=15 SOLVER_MERGE_STEP=15
export QUESTIONER_SAVE_FREQ=1 QUESTIONER_SAVE_LIMIT=1 SOLVER_SAVE_FREQ=1 SOLVER_SAVE_LIMIT=1
export SOLVER_VAL_FREQ=4
export QUESTIONER_ROLLOUT_BATCH_SIZE=512 QUESTIONER_ROLLOUT_N=4 QUESTIONER_GLOBAL_BATCH_SIZE=4
export QUESTIONER_MAX_RESPONSE_LENGTH=4096 SOLVER_MAX_RESPONSE_LENGTH=4096
export SOLVER_ROLLOUT_BATCH_SIZE=512 SOLVER_GENERATE_SAMPLES=2500 SOLVER_TOTAL_EPOCHS=100
export SOLVER_UPLOAD_MIN_SCORE=0.3 SOLVER_UPLOAD_MAX_SCORE=0.8
export QUESTIONER_LOGGER='["console","wandb"]' SOLVER_LOGGER='["console","wandb"]'
export WANDB_MODE=online
unset WANDB_DISABLED

# Isolated compile caches, as in the successful validity training launch.
OCTO_CACHE_ROOT=$(mktemp -d /tmp/octo-rzero-cache.XXXXXX)
export TORCHINDUCTOR_CACHE_DIR="${OCTO_CACHE_ROOT}/inductor"
export TRITON_CACHE_DIR="${OCTO_CACHE_ROOT}/triton"
mkdir -p "$TORCHINDUCTOR_CACHE_DIR" "$TRITON_CACHE_DIR"

OCTO_VALIDITY_ROOT=${OCTO_VALIDITY_ROOT:-${STORAGE_PATH}/models/octothinker_3b_hybrid_validity_rl_terra_clean_v1}
python3 methods/validity_rl/prepare_octothinker_eval.py \
    --run-root "$OCTO_VALIDITY_ROOT" --output-root "${OCTO_VALIDITY_ROOT}/evaluation_models" --steps 10
export VALIDITY_RZERO_INITIAL_SOLVER="${OCTO_VALIDITY_ROOT}/evaluation_models/global_step_10/actor/huggingface"

# Resolve/download base once; the frozen semantic workers subsequently use local files only.
export OCTO_BASE_MODEL=${OCTO_BASE_MODEL:-OctoThinker/OctoThinker-3B-Hybrid-Base}
BASE_MODEL=$(python3 - <<'PY'
import os
from pathlib import Path
from huggingface_hub import snapshot_download
from transformers import AutoConfig, AutoTokenizer
from scripts.validate_hf_checkpoint import validate_checkpoint
from methods.validity_rzero.octothinker import configure_tokenizer
source = os.environ['OCTO_BASE_MODEL']
path = Path(source).expanduser()
if not path.is_dir():
    path = Path(snapshot_download(source, local_files_only=os.getenv('HF_HUB_OFFLINE') == '1'))
validate_checkpoint(path)
if not (path / 'generation_config.json').is_file():
    raise ValueError('Frozen semantic judge requires generation_config.json in the base snapshot')
config = AutoConfig.from_pretrained(path, local_files_only=True)
if config.model_type != 'llama':
    raise ValueError('Expected OctoThinker Hybrid Base (Llama architecture)')
configure_tokenizer(AutoTokenizer.from_pretrained(path, local_files_only=True))
print(path.resolve())
PY
)
export BASE_MODEL
export VALIDITY_RZERO_SEMANTIC_MODEL="$BASE_MODEL"
echo "OctoThinker Questioner / frozen semantic judge: $BASE_MODEL"
echo "OctoThinker initial Solver: $VALIDITY_RZERO_INITIAL_SOLVER"
echo "New experiment: $MODEL_ABBR; rounds=$RZERO_NUM_ROUNDS; W&B=online"
bash methods/validity_rzero/run.sh "$@"
