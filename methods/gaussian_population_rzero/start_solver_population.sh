#!/usr/bin/env bash
set -euo pipefail

MODEL_PATH=$1
ROUND_INDEX=$2
METHOD_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

: "${SOLVER_EXPERT_GPU_IDS:=2,3}"
: "${SOLVER_POPULATION_SIZE:=10}"
: "${SOLVER_NOISE_SIGMA:=0.001}"
: "${POPULATION_SEED:=42}"
: "${SOLVER_EXPERT_SAMPLES:=10}"
: "${SOLVER_EXPERT_PORT_BASE:=5000}"
: "${SOLVER_EXPERT_GPU_MEMORY_UTILIZATION:=0.8}"
: "${SOLVER_EXPERT_MAX_TOKENS:=4096}"
: "${SOLVER_EXPERT_LOG_DIR:=logs}"
: "${SOLVER_EXPERT_PID_FILE:=${SOLVER_EXPERT_LOG_DIR}/solver_population.pids}"
: "${TENSOR_PARALLEL_SIZE:=1}"
export VLLM_USE_V1=0

if [ "$TENSOR_PARALLEL_SIZE" != "1" ]; then
  echo "Only TENSOR_PARALLEL_SIZE=1 is supported" >&2
  exit 2
fi

IFS=',' read -r -a GPUS <<< "$SOLVER_EXPERT_GPU_IDS"
NUM_WORKERS=${#GPUS[@]}
if [ "$NUM_WORKERS" -gt "$SOLVER_POPULATION_SIZE" ]; then
  NUM_WORKERS=$SOLVER_POPULATION_SIZE
fi
if [ "$NUM_WORKERS" -lt 1 ]; then
  echo "At least one Solver expert GPU is required" >&2
  exit 2
fi

mkdir -p "$SOLVER_EXPERT_LOG_DIR" "$(dirname "$SOLVER_EXPERT_PID_FILE")"
: > "$SOLVER_EXPERT_PID_FILE"

for ((worker=0; worker<NUM_WORKERS; worker++)); do
  indices=""
  for ((expert=worker; expert<SOLVER_POPULATION_SIZE; expert+=NUM_WORKERS)); do
    if [ -n "$indices" ]; then indices+=","; fi
    indices+="$expert"
  done
  port=$((SOLVER_EXPERT_PORT_BASE + worker))
  log="$SOLVER_EXPERT_LOG_DIR/solver_population_r${ROUND_INDEX}_worker${worker}_gpu${GPUS[$worker]}.log"
  CUDA_VISIBLE_DEVICES="${GPUS[$worker]}" setsid python3 "$METHOD_DIR/solver_population_server.py" \
    --port "$port" \
    --model-path "$MODEL_PATH" \
    --round-index "$ROUND_INDEX" \
    --population-size "$SOLVER_POPULATION_SIZE" \
    --expert-indices "$indices" \
    --sigma "$SOLVER_NOISE_SIGMA" \
    --global-seed "$POPULATION_SEED" \
    --samples "$SOLVER_EXPERT_SAMPLES" \
    --max-tokens "$SOLVER_EXPERT_MAX_TOKENS" \
    --gpu-memory-utilization "$SOLVER_EXPERT_GPU_MEMORY_UTILIZATION" \
    --tensor-parallel-size "$TENSOR_PARALLEL_SIZE" > "$log" 2>&1 &
  pid=$!
  echo "$pid" >> "$SOLVER_EXPERT_PID_FILE"
  echo "solver population worker=$worker gpu=${GPUS[$worker]} port=$port experts=$indices pid=$pid"
done

echo "$NUM_WORKERS"
