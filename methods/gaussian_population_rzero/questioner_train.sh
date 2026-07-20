#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 5 ]; then
  echo "Usage: $0 SOLVER_CENTER QUESTIONER_CENTER OUTPUT_DIR EXPERIMENT_NAME ROUND" >&2
  exit 2
fi
SOLVER_CENTER=$1
QUESTIONER_CENTER=$2
OUTPUT_DIR=$3
EXPERIMENT_NAME=$4
ROUND_INDEX=$5
METHOD_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "$METHOD_DIR/../.." && pwd)
cd "$REPO_ROOT"
export PYTHONPATH="$METHOD_DIR:$REPO_ROOT:${PYTHONPATH:-}"
export VLLM_DISABLE_COMPILE_CACHE=1
export VLLM_USE_V1=0

IFS=',' read -r -a Q_GPUS <<< "$QUESTIONER_TRAIN_GPU_IDS"
IFS=',' read -r -a S_GPUS <<< "$SOLVER_EXPERT_GPU_IDS"
QUESTIONER_GPU_COUNT=${#Q_GPUS[@]}
NUM_SERVICES=${#S_GPUS[@]}
if [ "$SOLVER_POPULATION_ENABLED" = "true" ]; then
  SOLVER_FEEDBACK_MODE=population
  if [ "$NUM_SERVICES" -gt "$SOLVER_POPULATION_SIZE" ]; then NUM_SERVICES=$SOLVER_POPULATION_SIZE; fi
  EFFECTIVE_POPULATION_SIZE=$SOLVER_POPULATION_SIZE
else
  SOLVER_FEEDBACK_MODE=central
  EFFECTIVE_POPULATION_SIZE=1
fi

mkdir -p "$OUTPUT_DIR" "$RUN_LOG_DIR"
export SOLVER_EXPERT_LOG_DIR="$RUN_LOG_DIR"
export SOLVER_EXPERT_PID_FILE="$OUTPUT_DIR/solver_${SOLVER_FEEDBACK_MODE}.pids"
export SOLVER_POPULATION_AUDIT_DIR="$OUTPUT_DIR/solver_${SOLVER_FEEDBACK_MODE}_feedback"
mkdir -p "$SOLVER_POPULATION_AUDIT_DIR"

cleanup() {
  if [ -f "$SOLVER_EXPERT_PID_FILE" ]; then
    while read -r pid; do
      if kill -0 "$pid" 2>/dev/null; then kill -- "-$pid" 2>/dev/null || kill "$pid" 2>/dev/null || true; fi
    done < "$SOLVER_EXPERT_PID_FILE"
    for _ in $(seq 1 60); do
      alive=0
      while read -r pid; do
        if kill -0 "$pid" 2>/dev/null; then alive=1; fi
      done < "$SOLVER_EXPERT_PID_FILE"
      if [ "$alive" = "0" ]; then break; fi
      sleep 1
    done
    while read -r pid; do
      if kill -0 "$pid" 2>/dev/null; then kill -KILL -- "-$pid" 2>/dev/null || true; fi
    done < "$SOLVER_EXPERT_PID_FILE"
  fi
}
trap cleanup EXIT

if [ "$SOLVER_FEEDBACK_MODE" = "population" ]; then
  bash "$METHOD_DIR/start_solver_population.sh" "$SOLVER_CENTER" "$ROUND_INDEX"
else
  bash "$METHOD_DIR/start_solver_center.sh" "$SOLVER_CENTER" "$ROUND_INDEX"
fi
for ((service=0; service<NUM_SERVICES; service++)); do
  port=$((SOLVER_EXPERT_PORT_BASE + service))
  service_pid=$(sed -n "$((service + 1))p" "$SOLVER_EXPERT_PID_FILE")
  healthy=0
  for _ in $(seq 1 600); do
    if python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:${port}/health', timeout=2).read()" >/dev/null 2>&1; then
      healthy=1
      break
    fi
    if ! kill -0 "$service_pid" 2>/dev/null; then
      echo "Solver $SOLVER_FEEDBACK_MODE service $service exited during startup" >&2
      tail -80 "$RUN_LOG_DIR/solver_${SOLVER_FEEDBACK_MODE}_r${ROUND_INDEX}_worker${service}_gpu${S_GPUS[$service]}.log" >&2 || true
      exit 1
    fi
    sleep 1
  done
  if [ "$healthy" != "1" ]; then
    echo "Solver $SOLVER_FEEDBACK_MODE service on port $port failed health check" >&2
    exit 1
  fi
done

CUDA_VISIBLE_DEVICES="$QUESTIONER_TRAIN_GPU_IDS" python3 -m verl.trainer.main \
  config=examples/config.yaml \
  data.max_response_length="$QUESTIONER_MAX_RESPONSE_LENGTH" \
  data.rollout_batch_size="$QUESTIONER_ROLLOUT_BATCH_SIZE" \
  worker.actor.model.model_path="$QUESTIONER_CENTER" \
  trainer.experiment_name="$EXPERIMENT_NAME" \
  trainer.logger="$QUESTIONER_LOGGER" \
  trainer.save_checkpoint_path="$OUTPUT_DIR" \
  trainer.total_epochs=1000 \
  worker.reward.reward_function="$METHOD_DIR/reward.py:compute_score" \
  worker.reward.reward_function_kwargs.num_services="$NUM_SERVICES" \
  worker.reward.reward_function_kwargs.port_base="$SOLVER_EXPERT_PORT_BASE" \
  worker.reward.reward_function_kwargs.population_size="$EFFECTIVE_POPULATION_SIZE" \
  worker.reward.reward_function_kwargs.expert_samples="$SOLVER_EXPERT_SAMPLES" \
  worker.reward.reward_function_kwargs.feedback_mode="$SOLVER_FEEDBACK_MODE" \
  trainer.val_freq=-1 \
  trainer.val_before_train=false \
  trainer.n_gpus_per_node="$QUESTIONER_GPU_COUNT" \
  data.format_prompt=./examples/format_prompt/questioner.jinja \
  worker.rollout.n="$QUESTIONER_ROLLOUT_N" \
  worker.rollout.tensor_parallel_size="$CENTER_ROLLOUT_TENSOR_PARALLEL_SIZE" \
  worker.actor.global_batch_size="$QUESTIONER_GLOBAL_BATCH_SIZE" \
  worker.actor.micro_batch_size_per_device_for_update="$QUESTIONER_MICRO_BATCH_UPDATE" \
  worker.actor.micro_batch_size_per_device_for_experience="$QUESTIONER_MICRO_BATCH_EXPERIENCE" \
  trainer.max_steps="$QUESTIONER_MAX_STEPS" \
  trainer.save_freq="$QUESTIONER_SAVE_FREQ"

python3 scripts/model_merger.py --local_dir "$OUTPUT_DIR/global_step_${QUESTIONER_MERGE_STEP}/actor"
VALIDATE_ARGS=()
if [ "$FULL_LOAD_VALIDATE" = "true" ]; then VALIDATE_ARGS+=(--full-load); fi
python3 "$METHOD_DIR/validate_checkpoint.py" \
  "$OUTPUT_DIR/global_step_${QUESTIONER_MERGE_STEP}/actor/huggingface" "${VALIDATE_ARGS[@]}"
