#!/bin/bash
set -e
export VLLM_DISABLE_COMPILE_CACHE=1
REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
export PYTHONPATH="${REPO_ROOT}:${PYTHONPATH:-}"
model_name=$1
mkdir -p logs
EVAL_RUN_ID=${EVAL_RUN_ID:-$(date +%Y%m%d_%H%M%S)}

MODEL_NAMES=(
  $model_name
)

if [ -n "${EVAL_TASKS:-}" ]; then
  IFS=',' read -ra TASKS <<< "$EVAL_TASKS"
else
  TASKS=(
    "math"
    "gsm8k"
    "amc"
    "minerva"
    "olympiad"
    "aime2024"
    "aime2025"
  )
fi

if [ -n "${EVAL_GPU_IDS:-}" ]; then
  IFS=',' read -ra GPU_QUEUE <<< "$EVAL_GPU_IDS"
else
  GPU_QUEUE=($(nvidia-smi --query-gpu=index --format=csv,noheader))
fi
EVAL_CUDA_VISIBLE_DEVICES=$(IFS=','; echo "${GPU_QUEUE[*]}")
EVAL_TENSOR_PARALLEL_SIZE=${EVAL_TENSOR_PARALLEL_SIZE:-${#GPU_QUEUE[@]}}
export EVAL_TENSOR_PARALLEL_SIZE
export EVAL_GPU_MEMORY_UTILIZATION=${EVAL_GPU_MEMORY_UTILIZATION:-0.85}

echo "Available eval GPUs: ${GPU_QUEUE[@]}"
echo "Eval tensor parallel size: ${EVAL_TENSOR_PARALLEL_SIZE}"
echo "Eval tasks: ${TASKS[@]}"

declare -A pids
declare -A pid_tasks
declare -A pid_logs
failed=0

start_job() {
  local gpu_id="$1"
  local model="$2"
  local task="$3"

  echo "==> [$(date '+%Y-%m-%d %H:%M:%S')] Start task [${task}] with model [${model}] on GPU [${gpu_id}] ..."

  local log_file="logs/eval_${EVAL_RUN_ID}_${task}_gpu${gpu_id}.log"

  CUDA_VISIBLE_DEVICES="${gpu_id}" \
  python evaluation/generate.py --model "${model}" --dataset "${task}" > "${log_file}" 2>&1 &

  pids["${gpu_id}"]=$!
  pid_tasks["${gpu_id}"]="${task}"
  pid_logs["${gpu_id}"]="${log_file}"
  echo "==> Log: ${log_file}"
}

for MODEL_NAME in "${MODEL_NAMES[@]}"; do
    echo "==> Processing model: ${MODEL_NAME}"
    TASK_INDEX=0
    NUM_TASKS=${#TASKS[@]}

    while :; do
        while [ ${#GPU_QUEUE[@]} -gt 0 ] && [ ${TASK_INDEX} -lt ${NUM_TASKS} ]; do
            gpu_id="${GPU_QUEUE[0]}"
            GPU_QUEUE=("${GPU_QUEUE[@]:1}")

            task="${TASKS[${TASK_INDEX}]}"
            ((TASK_INDEX+=1))

            start_job "$gpu_id" "$MODEL_NAME" "$task"
        done

        if [ ${TASK_INDEX} -ge ${NUM_TASKS} ] && [ ${#pids[@]} -eq 0 ]; then
            break
        fi

        for gpu_id in "${!pids[@]}"; do
            pid="${pids[$gpu_id]}"
            if ! kill -0 "$pid" 2>/dev/null; then
                task="${pid_tasks[$gpu_id]}"
                log_file="${pid_logs[$gpu_id]}"
                if wait "$pid"; then
                    echo "==> [$(date '+%Y-%m-%d %H:%M:%S')] GPU [${gpu_id}] task [${task}] finished successfully."
                else
                    status=$?
                    echo "==> [$(date '+%Y-%m-%d %H:%M:%S')] GPU [${gpu_id}] task [${task}] failed with exit code [${status}]. See ${log_file}"
                    failed=1
                fi
                unset pids["$gpu_id"]
                unset pid_tasks["$gpu_id"]
                unset pid_logs["$gpu_id"]
                GPU_QUEUE+=("$gpu_id")
            fi
        done

        sleep 1
    done
done

if [ "$failed" != "0" ]; then
  echo "==> Some base evaluation tasks failed; skipping results_recheck and later evaluation."
  exit 1
fi

python evaluation/results_recheck.py --model_name $model_name

if [ "${EVAL_MATH_ONLY:-0}" = "1" ]; then
  echo "==> EVAL_MATH_ONLY=1, skipping supergpqa/bbeh/mmlupro."
  echo "==> All math tasks have finished!"
  exit 0
fi

CUDA_VISIBLE_DEVICES="${EVAL_CUDA_VISIBLE_DEVICES}" python evaluation/eval_supergpqa.py --model_path $model_name
CUDA_VISIBLE_DEVICES="${EVAL_CUDA_VISIBLE_DEVICES}" python evaluation/eval_bbeh.py --model_path $model_name
CUDA_VISIBLE_DEVICES="${EVAL_CUDA_VISIBLE_DEVICES}" python evaluation/eval_mmlupro.py --model_path $model_name


echo "==> All tasks have finished!"
