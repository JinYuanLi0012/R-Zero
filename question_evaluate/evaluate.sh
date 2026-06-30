#!/bin/bash
set -e

model_name=$1
save_name=$2

QUESTION_GPU_IDS=${QUESTION_GPU_IDS:-0,1,2,3}
IFS=',' read -ra GPU_IDS <<< "$QUESTION_GPU_IDS"
pids=()

for i in "${!GPU_IDS[@]}"; do
  CUDA_VISIBLE_DEVICES=${GPU_IDS[$i]} python question_evaluate/evaluate.py --model $model_name --suffix $i --save_name $save_name &
  pids[$i]=$!
done

timeout_duration=3600
(
  sleep $timeout_duration
  echo "Timeout reached. Killing remaining tasks..."
  for pid in "${pids[@]}"; do
    if kill -0 "$pid" 2>/dev/null; then
      kill -9 "$pid" 2>/dev/null
    fi
  done
) &
timeout_pid=$!

status=0
for i in "${!pids[@]}"; do
  if wait "${pids[$i]}"; then
    echo "Task $i finished."
  else
    echo "Task $i failed."
    status=1
  fi
done

kill "$timeout_pid" 2>/dev/null || true
wait "$timeout_pid" 2>/dev/null || true
exit "$status"
