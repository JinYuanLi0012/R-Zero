#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 4 ]; then
  echo "Usage: $0 SOLVER_CENTER DATASET_PARQUET OUTPUT_DIR EXPERIMENT_NAME" >&2
  exit 2
fi
SOLVER_CENTER=$1
DATASET=$2
OUTPUT_DIR=$3
EXPERIMENT_NAME=$4
METHOD_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "$METHOD_DIR/../.." && pwd)
cd "$REPO_ROOT"
export PYTHONPATH="$METHOD_DIR:$REPO_ROOT:${PYTHONPATH:-}"
export VLLM_DISABLE_COMPILE_CACHE=1
export VLLM_USE_V1=0
IFS=',' read -r -a GPUS <<< "$QUESTION_GENERATION_GPU_IDS"
GPU_COUNT=${#GPUS[@]}
mkdir -p "$OUTPUT_DIR"

CUDA_VISIBLE_DEVICES="$QUESTION_GENERATION_GPU_IDS" python3 -m verl.trainer.main \
  config=examples/config.yaml \
  data.max_response_length="$SOLVER_MAX_RESPONSE_LENGTH" \
  data.rollout_batch_size="$SOLVER_ROLLOUT_BATCH_SIZE" \
  data.train_files="$DATASET" \
  worker.actor.model.model_path="$SOLVER_CENTER" \
  trainer.experiment_name="$EXPERIMENT_NAME" \
  trainer.logger="$SOLVER_LOGGER" \
  trainer.save_checkpoint_path="$OUTPUT_DIR" \
  trainer.total_epochs="$SOLVER_TOTAL_EPOCHS" \
  trainer.max_steps="$SOLVER_MAX_STEPS" \
  trainer.save_freq="$SOLVER_SAVE_FREQ" \
  trainer.save_limit="$SOLVER_SAVE_LIMIT" \
  data.format_prompt=./examples/format_prompt/solver.jinja \
  worker.rollout.n="$SOLVER_ROLLOUT_N" \
  worker.rollout.tensor_parallel_size="$CENTER_ROLLOUT_TENSOR_PARALLEL_SIZE" \
  worker.actor.global_batch_size="$SOLVER_GLOBAL_BATCH_SIZE" \
  trainer.val_freq="$SOLVER_VAL_FREQ" \
  trainer.n_gpus_per_node="$GPU_COUNT" \
  worker.actor.micro_batch_size_per_device_for_update=1 \
  worker.actor.micro_batch_size_per_device_for_experience=1

python3 scripts/model_merger.py --local_dir "$OUTPUT_DIR/global_step_${SOLVER_MERGE_STEP}/actor"
VALIDATE_ARGS=()
if [ "$FULL_LOAD_VALIDATE" = "true" ]; then VALIDATE_ARGS+=(--full-load); fi
python3 "$METHOD_DIR/validate_checkpoint.py" \
  "$OUTPUT_DIR/global_step_${SOLVER_MERGE_STEP}/actor/huggingface" "${VALIDATE_ARGS[@]}"
