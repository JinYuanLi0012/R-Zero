#!/usr/bin/env bash
set -euo pipefail

MODEL_PATH=$1
ROUND_INDEX=$2
METHOD_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

: "${SOLVER_EXPERT_GPU_IDS:=2,3}"
: "${SOLVER_EXPERT_SAMPLES:=10}"
: "${SOLVER_EXPERT_PORT_BASE:=5000}"
: "${SOLVER_EXPERT_GPU_MEMORY_UTILIZATION:=0.8}"
: "${SOLVER_EXPERT_MAX_TOKENS:=4096}"
: "${VLLM_SERVER_BATCH_SIZE:=32}"
: "${SOLVER_EXPERT_LOG_DIR:=logs}"
: "${SOLVER_EXPERT_PID_FILE:=${SOLVER_EXPERT_LOG_DIR}/solver_center.pids}"
: "${TENSOR_PARALLEL_SIZE:=1}"
export VLLM_USE_V1=0

if [ "$TENSOR_PARALLEL_SIZE" != "1" ]; then
  echo "Only TENSOR_PARALLEL_SIZE=1 is supported" >&2
  exit 2
fi
IFS=',' read -r -a GPUS <<< "$SOLVER_EXPERT_GPU_IDS"
if [ "${#GPUS[@]}" -lt 1 ]; then
  echo "At least one central Solver feedback GPU is required" >&2
  exit 2
fi

mkdir -p "$SOLVER_EXPERT_LOG_DIR" "$(dirname "$SOLVER_EXPERT_PID_FILE")"
: > "$SOLVER_EXPERT_PID_FILE"
for ((worker=0; worker<${#GPUS[@]}; worker++)); do
  port=$((SOLVER_EXPERT_PORT_BASE + worker))
  log="$SOLVER_EXPERT_LOG_DIR/solver_center_r${ROUND_INDEX}_worker${worker}_gpu${GPUS[$worker]}.log"
  CUDA_VISIBLE_DEVICES="${GPUS[$worker]}" setsid python3 "$METHOD_DIR/solver_center_server.py" \
    --port "$port" \
    --model-path "$MODEL_PATH" \
    --samples "$SOLVER_EXPERT_SAMPLES" \
    --max-tokens "$SOLVER_EXPERT_MAX_TOKENS" \
    --batch-size "$VLLM_SERVER_BATCH_SIZE" \
    --gpu-memory-utilization "$SOLVER_EXPERT_GPU_MEMORY_UTILIZATION" \
    --tensor-parallel-size "$TENSOR_PARALLEL_SIZE" > "$log" 2>&1 &
  pid=$!
  echo "$pid" >> "$SOLVER_EXPERT_PID_FILE"
  echo "central solver worker=$worker gpu=${GPUS[$worker]} port=$port pid=$pid"
done
echo "${#GPUS[@]}"
