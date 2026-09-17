#!/usr/bin/env bash
# Pure R-Zero: reproduce the Qwen 8K/five-round schedule with Octo Hybrid Base.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
if [[ $# -gt 1 || ( $# -eq 1 && "$1" != --resume ) ]]; then
    echo "Usage: bash $0 [--resume]" >&2; exit 2
fi
: "${STORAGE_PATH:?Source the server environment first}"
: "${HUGGINGFACENAME:?Set the namespace for generated training datasets}"
export PYTHONPATH="$PWD:${PYTHONPATH:-}"
export MODEL_ABBR=${OCTO_BASE_RZERO_NAME:-octothinker_3b_hybrid_base_rzero_8k_5round_v1}
if [[ ! "$MODEL_ABBR" =~ ^[a-zA-Z0-9][a-zA-Z0-9_-]*$ ]]; then
    echo "Invalid OCTO_BASE_RZERO_NAME" >&2; exit 2
fi

# Clear algorithm/checkpoint/data overrides from previous experiments. Preserve
# scheduler/auth/cache settings and transport knobs such as RZERO_RAY_TMPDIR,
# RZERO_SOLVER_VLLM_PORT_BASE and VLLM_PORT_BASE used by Compute2.
for name in ${!VALIDITY_RZERO_@} ${!TERRA_REPLAY_@} ${!QUESTIONER_@} ${!SOLVER_@}; do
    unset "$name"
done
unset RZERO_INITIAL_QUESTIONER RZERO_RUN_ROOT OCTO_FROZEN_JUDGE_MODEL
unset WANDB_DISABLED WANDB_RUN_ID WANDB_RESUME WANDB_NAME
unset VLLM_PORT VLLM_DP_MASTER_PORT
export VALIDITY_RZERO_ENABLED=0
# Model/template adaptation only; this flag does not enable validity rewards.
export VALIDITY_RZERO_MODEL_FAMILY=octothinker
export RZERO_NUM_ROUNDS=5 RZERO_FIRST_ROUND=1 RZERO_QUESTION_BOX_FILTER=legacy
export SOLVER_NEGATIVE_ONLY=0 SOLVER_DYNAMIC_VOTE=0 SOLVER_TOKEN_MASKING=0 SOLVER_EVAL_DUAL=0
export QUESTION_GPU_IDS=0,1,2,3 QUESTIONER_TRAIN_GPU_IDS=0,1 VLLM_GPU_IDS=2,3
export QUESTIONER_MAX_STEPS=5 QUESTIONER_MERGE_STEP=5 SOLVER_MAX_STEPS=15 SOLVER_MERGE_STEP=15
export QUESTIONER_SAVE_FREQ=1 QUESTIONER_SAVE_LIMIT=1 SOLVER_SAVE_FREQ=1 SOLVER_SAVE_LIMIT=1
export QUESTIONER_ROLLOUT_BATCH_SIZE=512 QUESTIONER_ROLLOUT_N=4 QUESTIONER_GLOBAL_BATCH_SIZE=4
export QUESTIONER_MICRO_BATCH_UPDATE=2 QUESTIONER_MICRO_BATCH_EXPERIENCE=8
export QUESTIONER_MAX_RESPONSE_LENGTH=4096 SOLVER_MAX_RESPONSE_LENGTH=4096
export SOLVER_ROLLOUT_BATCH_SIZE=512 SOLVER_GENERATE_SAMPLES=2000 SOLVER_TOTAL_EPOCHS=100
export SOLVER_VAL_FREQ=4 SOLVER_UPLOAD_MIN_SCORE=0.3 SOLVER_UPLOAD_MAX_SCORE=0.8
export VLLM_SERVER_N=10 VLLM_SERVER_MAX_TOKENS=4096
export QUESTIONER_LOGGER='["console","wandb"]' SOLVER_LOGGER='["console","wandb"]' WANDB_MODE=online

run_root="$STORAGE_PATH/rzero_runs/$MODEL_ABBR"
if [[ ${1:-} == --resume ]]; then
    [[ -s "$run_root/state/run_state.json" ]] || {
        echo "No existing pipeline state to resume: $run_root" >&2; exit 2;
    }
elif [[ -e "$run_root" || -e "$STORAGE_PATH/models/${MODEL_ABBR}_questioner_v1" || \
        -e "$STORAGE_PATH/models/${MODEL_ABBR}_solver_v1" ]]; then
    echo "Refuse fresh launch over existing experiment: $MODEL_ABBR" >&2; exit 2
fi

export OCTO_BASE_MODEL=${OCTO_BASE_MODEL:-OctoThinker/OctoThinker-3B-Hybrid-Base}
BASE_MODEL=$(python3 - <<'PY'
import os
from pathlib import Path
from huggingface_hub import snapshot_download
from transformers import AutoConfig, AutoTokenizer
from scripts.validate_hf_checkpoint import validate_checkpoint
from methods.validity_rzero.octothinker import configure_tokenizer
path = Path(os.environ['OCTO_BASE_MODEL']).expanduser()
if not path.is_dir():
    path = Path(snapshot_download(os.environ['OCTO_BASE_MODEL'],
                                 local_files_only=os.getenv('HF_HUB_OFFLINE') == '1'))
validate_checkpoint(path)
if AutoConfig.from_pretrained(path, local_files_only=True).model_type != 'llama':
    raise ValueError('Expected OctoThinker Hybrid Base (Llama architecture)')
tokenizer = configure_tokenizer(AutoTokenizer.from_pretrained(path, local_files_only=True))
ids = tokenizer.apply_chat_template([{'role': 'user', 'content': 'Test'}],
                                    tokenize=True, add_generation_prompt=True)
if ids.count(tokenizer.bos_token_id) != 1:
    raise ValueError('Octo template must produce exactly one BOS')
print(path.resolve())
PY
)
export BASE_MODEL
OCTO_CACHE_ROOT=$(mktemp -d /tmp/octo-base-rzero-cache.XXXXXX)
export TORCHINDUCTOR_CACHE_DIR="$OCTO_CACHE_ROOT/inductor" TRITON_CACHE_DIR="$OCTO_CACHE_ROOT/triton"
mkdir -p "$TORCHINDUCTOR_CACHE_DIR" "$TRITON_CACHE_DIR"
echo "Pure R-Zero: Questioner and Solver both initialize from $BASE_MODEL"
echo "run=$MODEL_ABBR rounds=5 candidates=8000 Q_steps=5 S_steps=15; W&B=online"
echo "Original BLEU/frontier reward; no validity, Terra replay or semantic judge"
bash scripts/main.sh --no-eval --rounds 5 "$@" "$BASE_MODEL" "$MODEL_ABBR"
