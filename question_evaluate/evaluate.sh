#!/bin/bash
set -euo pipefail

model_name=$1
save_name=$2

export QUESTION_GPU_IDS=${QUESTION_GPU_IDS:-0,1,2,3}
export QUESTION_EVAL_TIMEOUT_SECONDS=${QUESTION_EVAL_TIMEOUT_SECONDS:-43200}
if ! [[ "$QUESTION_EVAL_TIMEOUT_SECONDS" =~ ^[1-9][0-9]*$ ]]; then
  echo "QUESTION_EVAL_TIMEOUT_SECONDS must be a positive integer" >&2
  exit 2
fi

if [ "${VALIDITY_RZERO_ENABLED:-0}" = "1" ] && [ "${VALIDITY_RZERO_VALIDITY_JUDGE_MODE:-current_solver}" = "frozen" ]; then
  python3 -m methods.validity_rzero.frozen_validity --save-name "$save_name"
fi

# The supervisor owns worker sessions, their vLLM children, and a monotonic
# deadline. No background sleep/watchdog process can be orphaned.
exec python3 -m question_evaluate.run_workers --model "$model_name" --save-name "$save_name"
