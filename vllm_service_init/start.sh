model_path=$1
run_id=$2
export VLLM_DISABLE_COMPILE_CACHE=1
VLLM_GPU_IDS=${VLLM_GPU_IDS:-2,3}
VLLM_PORT_BASE=${VLLM_PORT_BASE:-5000}
VLLM_LOG_DIR=${VLLM_LOG_DIR:-logs}
mkdir -p "$VLLM_LOG_DIR"
IFS=',' read -ra GPU_IDS <<< "$VLLM_GPU_IDS"

if [ -n "$QUESTIONER_VLLM_PID_FILE" ]; then
  : > "$QUESTIONER_VLLM_PID_FILE"
fi

for i in "${!GPU_IDS[@]}"; do
  port=$((VLLM_PORT_BASE + i))
  log_file="${VLLM_LOG_DIR}/vllm_solver_${run_id}_gpu${GPU_IDS[$i]}_port${port}.log"
  CUDA_VISIBLE_DEVICES=${GPU_IDS[$i]} setsid python vllm_service_init/start_vllm_server.py --port $port --model_path $model_path > "$log_file" 2>&1 &
  pid=$!
  echo "vLLM service gpu=${GPU_IDS[$i]} port=${port} pid=${pid} log=${log_file}"
  if [ -n "$QUESTIONER_VLLM_PID_FILE" ]; then
    echo "$pid" >> "$QUESTIONER_VLLM_PID_FILE"
  fi
done
