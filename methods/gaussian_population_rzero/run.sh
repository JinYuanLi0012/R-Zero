#!/usr/bin/env bash
set -euo pipefail

METHOD_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "$METHOD_DIR/../.." && pwd)
CONFIG="$METHOD_DIR/config.sh"
RESUME=0
NO_EVAL=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --config) CONFIG=$2; shift 2 ;;
    --resume) RESUME=1; shift ;;
    --no-eval) NO_EVAL=1; shift ;;
    -h|--help)
      echo "Usage: $0 [--config PATH] [--resume] [--no-eval]"
      exit 0 ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

cd "$REPO_ROOT"
set -a
# shellcheck disable=SC1090
source "$CONFIG"
set +a
export PYTHONPATH="$METHOD_DIR:$REPO_ROOT:${PYTHONPATH:-}"
python3 "$METHOD_DIR/validate_config.py"

RUN_ROOT="$STORAGE_PATH/gaussian_population_rzero/$RUN_NAME"
QUESTIONERS_DIR="$RUN_ROOT/questioners"
DATASETS_DIR="$RUN_ROOT/datasets"
SOLVERS_DIR="$RUN_ROOT/solvers"
EVALUATIONS_DIR="$RUN_ROOT/evaluations"
RUN_LOG_DIR="$RUN_ROOT/logs"
STATE_DIR="$RUN_ROOT/state"
STATE_FILE="$STATE_DIR/run_state.json"
BASE_MANIFEST="$STATE_DIR/base_manifest.json"
if [ -e "$STATE_FILE" ] && [ "$RESUME" != "1" ]; then
  echo "Run already exists at $RUN_ROOT. Use --resume or select a different RUN_NAME." >&2
  exit 2
fi
mkdir -p "$QUESTIONERS_DIR" "$DATASETS_DIR" "$SOLVERS_DIR" "$EVALUATIONS_DIR" "$RUN_LOG_DIR" "$STATE_DIR"
export RUN_LOG_DIR

BASE_MODEL_SOURCE=$BASE_MODEL
BASE_RESOLVE_ARGS=(--model "$BASE_MODEL_SOURCE" --manifest "$BASE_MANIFEST")
if [ -n "$BASE_REVISION" ]; then BASE_RESOLVE_ARGS+=(--revision "$BASE_REVISION"); fi
BASE_RESOLUTION=$(python3 "$METHOD_DIR/resolve_base.py" "${BASE_RESOLVE_ARGS[@]}")
BASE_MODEL=$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["resolved_path"])' "$BASE_RESOLUTION")
BASE_IDENTITY=$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["identity_sha256"])' "$BASE_RESOLUTION")
BASE_RESOLVED_REVISION=$(python3 -c 'import json,sys; print(json.loads(sys.argv[1]).get("resolved_revision") or "local")' "$BASE_RESOLUTION")
FINGERPRINT=$(python3 "$METHOD_DIR/pipeline_state.py" init \
  --state "$STATE_FILE" \
  --field "base_model_source=$BASE_MODEL_SOURCE" \
  --field "base_resolved_revision=$BASE_RESOLVED_REVISION" \
  --field "base_identity=$BASE_IDENTITY" \
  --field "run_name=$RUN_NAME" \
  --field "model_abbr=$MODEL_ABBR" \
  --field "num_rounds=$NUM_ROUNDS" \
  --field "questioner_population_size=$QUESTIONER_POPULATION_SIZE" \
  --field "solver_population_size=$SOLVER_POPULATION_SIZE" \
  --field "questioner_sigma=$QUESTIONER_NOISE_SIGMA" \
  --field "solver_sigma=$SOLVER_NOISE_SIGMA" \
  --field "population_seed=$POPULATION_SEED" \
  --field "question_total_budget=$QUESTION_TOTAL_BUDGET" \
  --field "solver_expert_samples=$SOLVER_EXPERT_SAMPLES" \
  --field "solver_label_samples=$SOLVER_LABEL_SAMPLES" \
  --field "tensor_parallel_size=$TENSOR_PARALLEL_SIZE" \
  --field "questioner_train_gpu_ids=$QUESTIONER_TRAIN_GPU_IDS" \
  --field "solver_expert_gpu_ids=$SOLVER_EXPERT_GPU_IDS" \
  --field "question_generation_gpu_ids=$QUESTION_GENERATION_GPU_IDS" \
  --field "solver_expert_port_base=$SOLVER_EXPERT_PORT_BASE" \
  --field "questioner_max_steps=$QUESTIONER_MAX_STEPS" \
  --field "questioner_merge_step=$QUESTIONER_MERGE_STEP" \
  --field "questioner_save_freq=$QUESTIONER_SAVE_FREQ" \
  --field "questioner_rollout_batch_size=$QUESTIONER_ROLLOUT_BATCH_SIZE" \
  --field "questioner_rollout_n=$QUESTIONER_ROLLOUT_N" \
  --field "questioner_global_batch_size=$QUESTIONER_GLOBAL_BATCH_SIZE" \
  --field "questioner_micro_batch_update=$QUESTIONER_MICRO_BATCH_UPDATE" \
  --field "questioner_micro_batch_experience=$QUESTIONER_MICRO_BATCH_EXPERIENCE" \
  --field "questioner_max_response_length=$QUESTIONER_MAX_RESPONSE_LENGTH" \
  --field "solver_max_steps=$SOLVER_MAX_STEPS" \
  --field "solver_merge_step=$SOLVER_MERGE_STEP" \
  --field "solver_save_freq=$SOLVER_SAVE_FREQ" \
  --field "solver_save_limit=$SOLVER_SAVE_LIMIT" \
  --field "solver_total_epochs=$SOLVER_TOTAL_EPOCHS" \
  --field "solver_max_response_length=$SOLVER_MAX_RESPONSE_LENGTH" \
  --field "solver_val_freq=$SOLVER_VAL_FREQ" \
  --field "solver_expert_max_tokens=$SOLVER_EXPERT_MAX_TOKENS" \
  --field "question_generation_max_tokens=$QUESTION_GENERATION_MAX_TOKENS" \
  --field "solver_label_max_tokens=$SOLVER_LABEL_MAX_TOKENS" \
  --field "solver_expert_gpu_memory_utilization=$SOLVER_EXPERT_GPU_MEMORY_UTILIZATION" \
  --field "question_generation_gpu_memory_utilization=$QUESTION_GENERATION_GPU_MEMORY_UTILIZATION" \
  --field "solver_label_gpu_memory_utilization=$SOLVER_LABEL_GPU_MEMORY_UTILIZATION" \
  --field "solver_label_batch_size=$SOLVER_LABEL_BATCH_SIZE" \
  --field "dataset_score_range=${DATASET_MIN_SCORE}:${DATASET_MAX_SCORE}")

marker() { printf '%s/%s/_SUCCESS.json' "$STATE_DIR" "$1"; }

stage_done() {
  local stage=$1
  shift
  local args=(check --marker "$(marker "$stage")" --fingerprint "$FINGERPRINT")
  for required in "$@"; do args+=(--require "$required"); done
  python3 "$METHOD_DIR/pipeline_state.py" "${args[@]}"
}

guard_stage() {
  local stage=$1
  shift
  if stage_done "$stage" "$@"; then
    if [ "$RESUME" = "1" ]; then
      echo "[resume] skip completed stage $stage"
      return 1
    fi
    echo "Stage $stage already exists. Use --resume or a new RUN_NAME." >&2
    exit 2
  fi
  return 0
}

complete_stage() {
  local stage=$1 artifact=$2
  shift 2
  local args=(complete --state "$STATE_FILE" --marker "$(marker "$stage")" \
    --stage "$stage" --fingerprint "$FINGERPRINT" --artifact "$artifact")
  for item in "$@"; do args+=(--meta "$item"); done
  python3 "$METHOD_DIR/pipeline_state.py" "${args[@]}"
}

prepare_tmp() {
  local path=$1
  if [ -e "$path" ]; then
    local stale="${path}.stale.$(date +%s)"
    mv "$path" "$stale"
    echo "Preserved incomplete stage at $stale"
  fi
  mkdir -p "$path"
}

preserve_incomplete() {
  local path=$1
  if [ -e "$path" ]; then
    local stale="${path}.stale.$(date +%s)"
    mv "$path" "$stale"
    echo "Preserved incomplete final artifact at $stale"
  fi
}

CURRENT_QUESTIONER=$BASE_MODEL
CURRENT_SOLVER=$BASE_MODEL

echo "Gaussian-Population R-Zero: run=$RUN_NAME rounds=$NUM_ROUNDS B=$QUESTION_TOTAL_BUDGET"
for ((round=1; round<=NUM_ROUNDS; round++)); do
  echo "================ round $round / $NUM_ROUNDS ================"

  QUESTIONER_DIR="$QUESTIONERS_DIR/q${round}"
  QUESTIONER_HF="$QUESTIONER_DIR/global_step_${QUESTIONER_MERGE_STEP}/actor/huggingface"
  SOLVER_POPULATION_MANIFEST="$QUESTIONER_DIR/solver_population_manifest.json"
  QUESTIONER_STAGE="round_${round}/questioner"
  if guard_stage "$QUESTIONER_STAGE" "$QUESTIONER_HF" "$SOLVER_POPULATION_MANIFEST"; then
    preserve_incomplete "$QUESTIONER_DIR"
    QUESTIONER_TMP="$QUESTIONERS_DIR/.q${round}.inprogress"
    prepare_tmp "$QUESTIONER_TMP"
    python3 "$METHOD_DIR/manifests.py" population \
      --center "$CURRENT_SOLVER" --role solver --round-index "$round" \
      --population-size "$SOLVER_POPULATION_SIZE" --sigma "$SOLVER_NOISE_SIGMA" \
      --global-seed "$POPULATION_SEED" --gpu-ids "$SOLVER_EXPERT_GPU_IDS" \
      --samples "$SOLVER_EXPERT_SAMPLES" \
      --output "$QUESTIONER_TMP/solver_population_manifest.json"
    QUESTIONER_LOG_FILE="$RUN_LOG_DIR/questioner_r${round}.log"
    bash "$METHOD_DIR/questioner_train.sh" \
      "$CURRENT_SOLVER" "$CURRENT_QUESTIONER" "$QUESTIONER_TMP" \
      "${RUN_NAME}_questioner_v${round}" "$round" \
      > >(tee -a "$QUESTIONER_LOG_FILE") 2>&1
    mv "$QUESTIONER_TMP" "$QUESTIONER_DIR"
    complete_stage "$QUESTIONER_STAGE" "$QUESTIONER_HF" \
      "questioner_init=$CURRENT_QUESTIONER" "solver_population_center=$CURRENT_SOLVER" \
      "solver_population_size=$SOLVER_POPULATION_SIZE" "solver_sigma=$SOLVER_NOISE_SIGMA"
  fi
  CURRENT_QUESTIONER=$QUESTIONER_HF

  DATASET_DIR="$DATASETS_DIR/d${round}"
  DATASET_FILE="$DATASET_DIR/train.parquet"
  DATASET_MANIFEST="$DATASET_DIR/dataset_manifest.json"
  QUESTIONER_POPULATION_MANIFEST="$DATASET_DIR/questioner_population_manifest.json"
  DATASET_STAGE="round_${round}/dataset"
  if guard_stage "$DATASET_STAGE" "$DATASET_FILE" "$DATASET_MANIFEST" "$QUESTIONER_POPULATION_MANIFEST"; then
    preserve_incomplete "$DATASET_DIR"
    DATASET_TMP="$DATASETS_DIR/.d${round}.inprogress"
    prepare_tmp "$DATASET_TMP"
    GENERATED_DIR="$DATASET_TMP/generated_question"
    mkdir -p "$GENERATED_DIR"
    SAVE_NAME="${RUN_NAME}_questions_v${round}"
    export QUESTION_GENERATION_LOG_DIR="$RUN_LOG_DIR"
    NUM_SHARDS=$(bash "$METHOD_DIR/generate_questions.sh" \
      "$CURRENT_QUESTIONER" "$round" "$SAVE_NAME" "$GENERATED_DIR")
    python3 "$METHOD_DIR/manifests.py" verify-generation \
      --center "$CURRENT_QUESTIONER" --round-index "$round" \
      --population-size "$QUESTIONER_POPULATION_SIZE" --sigma "$QUESTIONER_NOISE_SIGMA" \
      --global-seed "$POPULATION_SEED" --total-budget "$QUESTION_TOTAL_BUDGET" \
      --num-shards "$NUM_SHARDS" --generated-dir "$GENERATED_DIR" --save-name "$SAVE_NAME" \
      --gpu-ids "$QUESTION_GENERATION_GPU_IDS" \
      --output "$DATASET_TMP/questioner_population_manifest.json"
    bash "$METHOD_DIR/evaluate_questions.sh" \
      "$CURRENT_SOLVER" "$SAVE_NAME" "$GENERATED_DIR" "$NUM_SHARDS" \
      > >(tee -a "$RUN_LOG_DIR/central_solver_label_r${round}.log") 2>&1
    python3 "$METHOD_DIR/prepare_dataset.py" \
      --generated-dir "$GENERATED_DIR" --experiment-name "$SAVE_NAME" \
      --num-shards "$NUM_SHARDS" --total-budget "$QUESTION_TOTAL_BUDGET" \
      --output "$DATASET_TMP/train.parquet" \
      --min-score "$DATASET_MIN_SCORE" --max-score "$DATASET_MAX_SCORE"
    mv "$DATASET_TMP" "$DATASET_DIR"
    FILTERED=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["filtered_count"])' "$DATASET_DIR/dataset_manifest.json")
    complete_stage "$DATASET_STAGE" "$DATASET_FILE" \
      "questioner_center=$CURRENT_QUESTIONER" "labeler_center=$CURRENT_SOLVER" \
      "question_total_budget=$QUESTION_TOTAL_BUDGET" "filtered_count=$FILTERED"
  fi

  SOLVER_DIR="$SOLVERS_DIR/s${round}"
  SOLVER_HF="$SOLVER_DIR/global_step_${SOLVER_MERGE_STEP}/actor/huggingface"
  SOLVER_STAGE="round_${round}/solver"
  if guard_stage "$SOLVER_STAGE" "$SOLVER_HF"; then
    preserve_incomplete "$SOLVER_DIR"
    SOLVER_TMP="$SOLVERS_DIR/.s${round}.inprogress"
    prepare_tmp "$SOLVER_TMP"
    bash "$METHOD_DIR/solver_train.sh" \
      "$CURRENT_SOLVER" "$DATASET_FILE" "$SOLVER_TMP" "${RUN_NAME}_solver_v${round}" \
      > >(tee -a "$RUN_LOG_DIR/solver_r${round}.log") 2>&1
    mv "$SOLVER_TMP" "$SOLVER_DIR"
    complete_stage "$SOLVER_STAGE" "$SOLVER_HF" \
      "solver_init=$CURRENT_SOLVER" "dataset=$DATASET_FILE" "selected_step=$SOLVER_MERGE_STEP"
  fi
  CURRENT_SOLVER=$SOLVER_HF

  if [ "$NO_EVAL" != "1" ] && [ "$EVALUATE_EACH_ROUND" = "true" ]; then
    EVAL_DIR="$EVALUATIONS_DIR/s${round}"
    EVAL_STAGE="round_${round}/evaluation"
    if guard_stage "$EVAL_STAGE" "$EVAL_DIR"; then
      preserve_incomplete "$EVAL_DIR"
      mkdir -p "$EVAL_DIR"
      EVAL_ARTIFACT_DIR="$EVAL_DIR" EVAL_LOG_DIR="$RUN_LOG_DIR" \
        EVAL_RUN_ID="${RUN_NAME}_s${round}" EVAL_GPU_IDS="$QUESTION_GENERATION_GPU_IDS" \
        bash evaluation/evaluate.bash "$CURRENT_SOLVER"
      complete_stage "$EVAL_STAGE" "$EVAL_DIR" "solver=$CURRENT_SOLVER"
    fi
  fi
done

python3 - "$RUN_ROOT/summary.json" "$CURRENT_QUESTIONER" "$CURRENT_SOLVER" "$NUM_ROUNDS" <<'PY'
import json, sys
from pathlib import Path
path = Path(sys.argv[1])
path.write_text(json.dumps({
    "rounds": int(sys.argv[4]),
    "final_questioner": sys.argv[2],
    "final_solver": sys.argv[3],
    "expert_checkpoints_persisted": False,
}, indent=2) + "\n")
PY
echo "Completed Gaussian-Population R-Zero: $RUN_ROOT"
