#!/usr/bin/env bash
set -euo pipefail

MODEL=$1
ROUND_INDEX=$2
SAVE_NAME=$3
OUTPUT_DIR=$4
METHOD_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

: "${QUESTIONER_POPULATION_SIZE:=10}"
: "${QUESTIONER_NOISE_SIGMA:=0.001}"
: "${POPULATION_SEED:=42}"
: "${QUESTION_TOTAL_BUDGET:=4000}"
: "${QUESTION_GENERATION_GPU_IDS:=0,1,2,3}"
: "${QUESTION_GENERATION_GPU_MEMORY_UTILIZATION:=0.8}"
: "${QUESTION_GENERATION_MAX_TOKENS:=4096}"
: "${QUESTION_GENERATION_LOG_DIR:=${OUTPUT_DIR}/logs}"
: "${TENSOR_PARALLEL_SIZE:=1}"
export VLLM_USE_V1=0

IFS=',' read -r -a GPUS <<< "$QUESTION_GENERATION_GPU_IDS"
NUM_WORKERS=${#GPUS[@]}
if [ "$NUM_WORKERS" -gt "$QUESTIONER_POPULATION_SIZE" ]; then
  NUM_WORKERS=$QUESTIONER_POPULATION_SIZE
fi
mkdir -p "$OUTPUT_DIR" "$QUESTION_GENERATION_LOG_DIR"
pids=()
for ((worker=0; worker<NUM_WORKERS; worker++)); do
  log="$QUESTION_GENERATION_LOG_DIR/question_population_r${ROUND_INDEX}_worker${worker}_gpu${GPUS[$worker]}.log"
  CUDA_VISIBLE_DEVICES="${GPUS[$worker]}" python3 "$METHOD_DIR/generate_questions.py" \
    --model "$MODEL" \
    --round-index "$ROUND_INDEX" \
    --population-size "$QUESTIONER_POPULATION_SIZE" \
    --sigma "$QUESTIONER_NOISE_SIGMA" \
    --global-seed "$POPULATION_SEED" \
    --total-budget "$QUESTION_TOTAL_BUDGET" \
    --worker-index "$worker" \
    --num-workers "$NUM_WORKERS" \
    --output "$OUTPUT_DIR/${SAVE_NAME}_${worker}.json" \
    --manifest "$OUTPUT_DIR/${SAVE_NAME}_${worker}_generation_manifest.json" \
    --max-tokens "$QUESTION_GENERATION_MAX_TOKENS" \
    --gpu-memory-utilization "$QUESTION_GENERATION_GPU_MEMORY_UTILIZATION" \
    --tensor-parallel-size "$TENSOR_PARALLEL_SIZE" > "$log" 2>&1 &
  pids+=("$!")
done

status=0
for pid in "${pids[@]}"; do
  if ! wait "$pid"; then status=1; fi
done
if [ "$status" != "0" ]; then exit "$status"; fi
echo "$NUM_WORKERS"
