#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 4 ]; then
    echo "Usage: $0 BASE_MODEL DATASET_PARQUET OUTPUT_DIR EXPERIMENT_NAME" >&2
    exit 2
fi

BASE_MODEL=$1
DATASET_PARQUET=$2
OUTPUT_DIR=$3
EXPERIMENT_NAME=$4

REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
cd "$REPO_ROOT"
export PYTHONPATH="${REPO_ROOT}:${PYTHONPATH:-}"
export VLLM_DISABLE_COMPILE_CACHE=1

: "${QUESTION_GPU_IDS:=0,1,2,3}"
: "${SOLVER_MAX_RESPONSE_LENGTH:=4096}"
: "${SOLVER_TOTAL_EPOCHS:=100}"
: "${SOLVER_MAX_STEPS:=20}"
: "${SOLVER_VAL_FREQ:=4}"
: "${SOLVER_MERGE_STEP:=15}"
: "${SOLVER_LOGGER:=[\"console\",\"wandb\"]}"

IFS=',' read -r -a GPU_IDS <<< "$QUESTION_GPU_IDS"
GPU_COUNT=${#GPU_IDS[@]}
mkdir -p "$OUTPUT_DIR"

echo "Task-vector Base-fit training"
echo "  experiment: $EXPERIMENT_NAME"
echo "  train_init_model: $BASE_MODEL"
echo "  local_dataset: $DATASET_PARQUET"
echo "  output: $OUTPUT_DIR"
echo "  GPUs: $QUESTION_GPU_IDS"

CUDA_VISIBLE_DEVICES="$QUESTION_GPU_IDS" python3 -m verl.trainer.main \
    config=examples/config.yaml \
    data.max_response_length="$SOLVER_MAX_RESPONSE_LENGTH" \
    data.train_files="$DATASET_PARQUET" \
    worker.actor.model.model_path="$BASE_MODEL" \
    trainer.experiment_name="$EXPERIMENT_NAME" \
    trainer.logger="$SOLVER_LOGGER" \
    trainer.save_checkpoint_path="$OUTPUT_DIR" \
    trainer.total_epochs="$SOLVER_TOTAL_EPOCHS" \
    trainer.max_steps="$SOLVER_MAX_STEPS" \
    data.format_prompt=./examples/format_prompt/solver.jinja \
    trainer.val_freq="$SOLVER_VAL_FREQ" \
    trainer.n_gpus_per_node="$GPU_COUNT" \
    worker.actor.micro_batch_size_per_device_for_update=1 \
    worker.actor.micro_batch_size_per_device_for_experience=1

ACTOR_DIR="${OUTPUT_DIR}/global_step_${SOLVER_MERGE_STEP}/actor"
if [ ! -d "$ACTOR_DIR" ]; then
    echo "Expected merge checkpoint does not exist: $ACTOR_DIR" >&2
    exit 1
fi

python3 scripts/model_merger.py --local_dir "$ACTOR_DIR"
python3 methods/task_vector_rzero/validate_checkpoint.py "$ACTOR_DIR/huggingface"
echo "Base-fit training complete: $ACTOR_DIR/huggingface"
