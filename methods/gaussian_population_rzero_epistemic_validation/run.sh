#!/usr/bin/env bash
set -euo pipefail

METHOD_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
CONFIG_PATH="${METHOD_DIR}/config.sh"
REQUESTED_STAGE=all
RESUME=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --config) CONFIG_PATH=$2; shift 2 ;;
    --stage) REQUESTED_STAGE=$2; shift 2 ;;
    --resume) RESUME=1; shift ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

source "$CONFIG_PATH"
RUN_ROOT="${STORAGE_PATH}/epistemic_validation/${RUN_NAME}"
STATE_DIR="${RUN_ROOT}/state"
PREPARED_DIR="${RUN_ROOT}/prepared"
SCORE_DIR="${RUN_ROOT}/scores"
JUDGE_DIR="${RUN_ROOT}/judge"
ANALYSIS_DIR="${RUN_ROOT}/analysis"
mkdir -p "$STATE_DIR"
cp "$CONFIG_PATH" "${RUN_ROOT}/config.snapshot.sh"

stage_wanted() {
  [[ "$REQUESTED_STAGE" == all || "$REQUESTED_STAGE" == "$1" ]]
}

stage_done() {
  "$PYTHON_BIN" "$METHOD_DIR/state.py" is-complete --state-dir "$STATE_DIR" --stage "$1"
}

mark_done() {
  "$PYTHON_BIN" "$METHOD_DIR/state.py" complete --state-dir "$STATE_DIR" --stage "$1"
}

run_population() {
  local model=$1 input=$2 output=$3 round=$4 sigmas=$5
  local resume_args=()
  if [[ "$RESUME" -eq 1 ]]; then resume_args+=(--resume); fi
  "$PYTHON_BIN" "$METHOD_DIR/population_driver.py" \
    --model "$model" --input "$input" --output-dir "$output" --round-index "$round" \
    --sigmas "$sigmas" --gpu-ids "$GPU_IDS" --population-size "$POPULATION_SIZE" \
    --global-seed "$POPULATION_SEED" --samples "$SAMPLES_PER_EXPERT" \
    --max-tokens "$MAX_TOKENS" --batch-size "$INFERENCE_BATCH_SIZE" \
    --temperature "$TEMPERATURE" --top-p "$TOP_P" --top-k "$TOP_K" \
    --gpu-memory-utilization "$GPU_MEMORY_UTILIZATION" "${resume_args[@]}"
}

if stage_wanted prepare; then
  if [[ "$RESUME" -eq 1 ]] && stage_done prepare; then
    echo "[resume] prepare already complete"
  else
    "$PYTHON_BIN" "$METHOD_DIR/prepare.py" \
      --cache-root "$HF_DATASETS_CACHE" \
      --dataset-names "$V1_DATASET_NAME" "$V2_DATASET_NAME" "$V3_DATASET_NAME" \
      --expected-rows "$V1_EXPECTED_ROWS" "$V2_EXPECTED_ROWS" "$V3_EXPECTED_ROWS" \
      --centers "$BASE_MODEL" "$SOLVER_V1" "$SOLVER_V2" \
      --seed "$EXPERIMENT_SEED" --output-dir "$PREPARED_DIR"
    mark_done prepare
  fi
fi

if stage_wanted score_all_sigmas; then
  if [[ "$RESUME" -eq 1 ]] && stage_done score_all_sigmas; then
    echo "[resume] score_all_sigmas already complete"
  else
    [[ -f "${PREPARED_DIR}/all_samples.jsonl" ]] || { echo "prepare stage is required" >&2; exit 1; }
    centers=("$BASE_MODEL" "$SOLVER_V1" "$SOLVER_V2")
    for round in 1 2 3; do
      round_root="${SCORE_DIR}/v${round}"
      run_population "${centers[$((round - 1))]}" "${PREPARED_DIR}/v${round}_sample.jsonl" "$round_root/raw" "$round" "$EPISTEMIC_SIGMAS"
      "$PYTHON_BIN" "$METHOD_DIR/aggregate.py" --input "${PREPARED_DIR}/v${round}_sample.jsonl" \
        --raw-root "$round_root/raw" --output-dir "$round_root/summary" --sigmas "$EPISTEMIC_SIGMAS" \
        --population-size "$POPULATION_SIZE" --samples "$SAMPLES_PER_EXPERT"
    done
    mark_done score_all_sigmas
  fi
fi

if stage_wanted judge; then
  if [[ "$RESUME" -eq 1 ]] && stage_done judge; then
    echo "[resume] judge already complete"
  else
    "$PYTHON_BIN" "$METHOD_DIR/judge.py" --input "${PREPARED_DIR}/all_samples.jsonl" --output-dir "$JUDGE_DIR" \
      --model "$JUDGE_MODEL" --concurrency "$JUDGE_CONCURRENCY" \
      --human-review-size "$HUMAN_REVIEW_SIZE" --seed "$EXPERIMENT_SEED"
    mark_done judge
  fi
fi

if stage_wanted analyze; then
  if [[ "$RESUME" -eq 1 ]] && stage_done analyze; then
    echo "[resume] analyze already complete"
  else
    "$PYTHON_BIN" "$METHOD_DIR/analyze.py" --samples "${PREPARED_DIR}/all_samples.jsonl" \
      --judge-results "${JUDGE_DIR}/judge_results.jsonl" --score-root "$SCORE_DIR" \
      --sigmas "$EPISTEMIC_SIGMAS" --output-dir "$ANALYSIS_DIR" \
      --bootstrap-samples "$ANALYSIS_BOOTSTRAP_SAMPLES" --seed "$EXPERIMENT_SEED"
    "$PYTHON_BIN" "$METHOD_DIR/verify_run.py" --run-root "$RUN_ROOT" \
      --population-size "$POPULATION_SIZE" --samples "$SAMPLES_PER_EXPERT" \
      --sigmas "$EPISTEMIC_SIGMAS"
    mark_done analyze
  fi
fi

if [[ "$REQUESTED_STAGE" != all && ! "$REQUESTED_STAGE" =~ ^(prepare|score_all_sigmas|judge|analyze)$ ]]; then
  echo "Unknown stage: $REQUESTED_STAGE" >&2
  exit 2
fi

echo "Artifacts: $RUN_ROOT"
