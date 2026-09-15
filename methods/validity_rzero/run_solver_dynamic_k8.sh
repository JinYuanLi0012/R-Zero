#!/usr/bin/env bash
# Solver-only round 1: reuse the original mixed dataset, with fresh dynamic labels.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
case "${1:-}" in
    "") RESUME=0 ;;
    --resume) RESUME=1 ;;
    *) echo "Usage: bash $0 [--resume]" >&2; exit 2 ;;
esac
: "${STORAGE_PATH:?source env_rzero.sh first}"
: "${HUGGINGFACENAME:?source env_rzero.sh first}"
RUN_NAME=${SOLVER_DYNAMIC_RUN_NAME:-qwen3_4b_validity_rzero_semantic_novelty_gate_k8_solver_dynamic_mask_4gpu_v1}
EXPERIMENT=${RUN_NAME}_solver_v1
RUN_ROOT=$STORAGE_PATH/rzero_runs/$RUN_NAME
MODEL_DIR=$STORAGE_PATH/models/$EXPERIMENT
INITIAL=$STORAGE_PATH/models/qwen3_4b_validity_rl_terra_clean_v1/global_step_15/actor/huggingface
SOURCE_EXPERIMENT=qwen3_4b_validity_rzero_semantic_novelty_gate_k8_solver_negative_4gpu_v1_solver_v1
export SOLVER_TRAIN_FILES=${HUGGINGFACENAME}/${SOURCE_EXPERIMENT}@train
export VALIDITY_RZERO_ENABLED=1
export VALIDITY_RZERO_ARTIFACT_DIR=$RUN_ROOT/artifacts
unset VALIDITY_RZERO_DIVERSITY_MODE SOLVER_LOAD_CHECKPOINT SOLVER_LOG_FILE
export QUESTION_GPU_IDS=0,1,2,3
export SOLVER_NEGATIVE_ONLY=1 SOLVER_DYNAMIC_VOTE=1 SOLVER_TOKEN_MASKING=1
export SOLVER_DATASET_READY=1 SOLVER_PREPARE_ONLY=0
export SOLVER_SKIP_MERGE=0 SOLVER_SKIP_FINAL_EVAL=1
export SOLVER_MAX_STEPS=15 SOLVER_MERGE_STEP=15 SOLVER_TOTAL_EPOCHS=100
export SOLVER_ROLLOUT_BATCH_SIZE=512 SOLVER_MAX_RESPONSE_LENGTH=4096 SOLVER_VAL_FREQ=4
export SOLVER_SAVE_FREQ=3 SOLVER_SAVE_LIMIT=5 SOLVER_KEEP_LATEST_RESUME_STATE_ONLY=false
export RECHECK_LOCAL_TMP_ROOT=/tmp RECHECK_STARTUP_TIMEOUT=3600
FINAL_HF=$MODEL_DIR/global_step_15/actor/huggingface

# Reusing a dataset is explicit; this launcher never invokes the Questioner,
# dataset preparation/upload, service cleanup, or the multi-round pipeline.
if [ "$RESUME" = "0" ] && [ -d "$MODEL_DIR" ]; then
    echo "Output already exists: $MODEL_DIR. Use --resume or a new SOLVER_DYNAMIC_RUN_NAME." >&2
    exit 2
fi
python3 scripts/validate_hf_checkpoint.py "$INITIAL" >/dev/null
mkdir -p "$RUN_ROOT"
python3 - "$RUN_ROOT/run_config.json" "$INITIAL" "$SOLVER_TRAIN_FILES" "$RESUME" <<'PY'
import json, sys
from pathlib import Path
path = Path(sys.argv[1])
config = dict(initial_solver=sys.argv[2], dataset=sys.argv[3],
              treatment='unique_min2_16vote_2pos3neg_full_entropy_per_response_q98_median_v1',
              max_steps=15, save_freq=3, rollout_batch_size=512)
if path.exists():
    if json.loads(path.read_text()) != config:
        raise SystemExit('Run configuration changed; choose a new SOLVER_DYNAMIC_RUN_NAME.')
elif sys.argv[4] == '1':
    raise SystemExit('No run_config.json for --resume; this launcher only resumes its own experiment.')
else:
    path.write_text(json.dumps(config, indent=2) + '\n')
PY
if [ "$RESUME" = "1" ] && [ ! -f "$RUN_ROOT/training_complete" ]; then
    SOLVER_LOAD_CHECKPOINT=$(python3 - "$MODEL_DIR" <<'PY'
import sys
from pathlib import Path
root = Path(sys.argv[1])
candidates = [p for p in root.glob('global_step_*')
              if (p / 'dataloader.pt').is_file() and any((p / 'actor').glob('model_world_size_*_rank_*.pt'))]
if not candidates:
    raise SystemExit('No resumable checkpoint found in this experiment; choose a new run name for a fresh run.')
print(max(candidates, key=lambda p: int(p.name.rsplit('_', 1)[1])))
PY
)
    export SOLVER_LOAD_CHECKPOINT
fi
if [ ! -f "$RUN_ROOT/training_complete" ]; then
    echo "Solver-only round 1: initial=$INITIAL dataset=$SOLVER_TRAIN_FILES output=$MODEL_DIR"
    bash scripts/solver_train.sh "$INITIAL" unused_questioner "$EXPERIMENT"
    python3 scripts/validate_hf_checkpoint.py "$FINAL_HF" >/dev/null
    touch "$RUN_ROOT/training_complete"
fi

for MODE in rzero-original corrected; do
    EVAL_DIR=$RUN_ROOT/evaluations/solver_v1/$MODE
    if [ -f "$EVAL_DIR/complete" ]; then continue; fi
    mkdir -p "$EVAL_DIR"
    BATCH=$EVAL_DIR/math_${MODE}_$(python3 -c 'import uuid; print(uuid.uuid4().hex)')
    python3 evaluation/evaluate_models.py --suite math --gpu-ids "$QUESTION_GPU_IDS" \
        --judge-prompt-mode "$MODE" --storage-path "$STORAGE_PATH" --batch-dir "$BATCH" \
        "$FINAL_HF" 2>&1 | tee "${BATCH}.log"
    cp "$BATCH/summary.csv" "$EVAL_DIR/summary.csv"
    cp "$BATCH/summary.md" "$EVAL_DIR/summary.md"
    touch "$EVAL_DIR/complete"
done
echo "Done. Evaluation summaries: $RUN_ROOT/evaluations/solver_v1/{rzero-original,corrected}/summary.md"
