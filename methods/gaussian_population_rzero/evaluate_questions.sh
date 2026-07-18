#!/usr/bin/env bash
set -euo pipefail

MODEL=$1
SAVE_NAME=$2
GENERATED_DIR=$3
NUM_SHARDS=$4
METHOD_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

: "${QUESTION_GENERATION_GPU_IDS:=0,1,2,3}"
: "${SOLVER_LABEL_SAMPLES:=9}"
: "${SOLVER_LABEL_MAX_TOKENS:=4096}"
: "${SOLVER_LABEL_GPU_MEMORY_UTILIZATION:=0.85}"
: "${SOLVER_LABEL_BATCH_SIZE:=0}"

if [ "$SOLVER_LABEL_SAMPLES" != "9" ]; then
  echo "SOLVER_LABEL_SAMPLES must remain 9 for standard R-Zero alignment" >&2
  exit 2
fi
IFS=',' read -r -a GPUS <<< "$QUESTION_GENERATION_GPU_IDS"
if [ "$NUM_SHARDS" -gt "${#GPUS[@]}" ]; then
  echo "Not enough labeling GPUs for $NUM_SHARDS shards" >&2
  exit 2
fi

pids=()
for ((shard=0; shard<NUM_SHARDS; shard++)); do
  CUDA_VISIBLE_DEVICES="${GPUS[$shard]}" python3 "$METHOD_DIR/evaluate_questions.py" \
    --model "$MODEL" \
    --input "$GENERATED_DIR/${SAVE_NAME}_${shard}.json" \
    --output "$GENERATED_DIR/${SAVE_NAME}_${shard}_results.json" \
    --samples "$SOLVER_LABEL_SAMPLES" \
    --worker-seed "$shard" \
    --max-tokens "$SOLVER_LABEL_MAX_TOKENS" \
    --gpu-memory-utilization "$SOLVER_LABEL_GPU_MEMORY_UTILIZATION" \
    --batch-size "$SOLVER_LABEL_BATCH_SIZE" &
  pids+=("$!")
done
status=0
for pid in "${pids[@]}"; do
  if ! wait "$pid"; then status=1; fi
done
exit "$status"
