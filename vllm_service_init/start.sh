#!/usr/bin/env bash
set -euo pipefail

model_path=$1
run_id=$2
export VLLM_DISABLE_COMPILE_CACHE=1
VLLM_GPU_IDS=${VLLM_GPU_IDS:-2,3}
VLLM_PORT_BASE=${VLLM_PORT_BASE:-5000}
VLLM_LOG_DIR=${VLLM_LOG_DIR:-logs}
PYTHON_EXECUTABLE=${PYTHON_EXECUTABLE:-python3}
mkdir -p "$VLLM_LOG_DIR"
IFS=',' read -ra GPU_IDS <<< "$VLLM_GPU_IDS"
# Both initial launch and semantic handoff restart use this entry. Physical GPU
# IDs also keep temporary reward workers on GPUs 0/1 separate from GPUs 2/3.
port_plan=$("$PYTHON_EXECUTABLE" vllm_service_init/solver_ports.py \
  --gpu-ids "$VLLM_GPU_IDS" --http-base "$VLLM_PORT_BASE" \
  --internal-base "${RZERO_SOLVER_VLLM_PORT_BASE:-12000}")
PORT_ROWS=()
while IFS= read -r row; do PORT_ROWS+=("$row"); done <<< "$port_plan"

if [ -n "${QUESTIONER_VLLM_PID_FILE:-}" ]; then
  : > "$QUESTIONER_VLLM_PID_FILE"
fi

for i in "${!GPU_IDS[@]}"; do
  read -r port internal_port dp_port <<< "${PORT_ROWS[$i]}"
  log_file="${VLLM_LOG_DIR}/vllm_solver_${run_id}_gpu${GPU_IDS[$i]}_port${port}.log"
  CUDA_VISIBLE_DEVICES=${GPU_IDS[$i]} VLLM_PORT=$internal_port VLLM_DP_MASTER_PORT=$dp_port \
    setsid "$PYTHON_EXECUTABLE" vllm_service_init/start_vllm_server.py --port "$port" --model_path "$model_path" --run_id "$run_id" > "$log_file" 2>&1 &
  pid=$!
  echo "vLLM service gpu=${GPU_IDS[$i]} port=${port} internal_port=${internal_port} dp_port=${dp_port} pid=${pid} log=${log_file}"
  if [ -n "${QUESTIONER_VLLM_PID_FILE:-}" ]; then
    echo "$pid" >> "$QUESTIONER_VLLM_PID_FILE"
  fi
done
