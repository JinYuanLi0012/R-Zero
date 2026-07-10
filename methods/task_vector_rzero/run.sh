#!/usr/bin/env bash
set -euo pipefail

METHOD_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "$METHOD_DIR/../.." && pwd)
CONFIG_PATH="$METHOD_DIR/config.sh"
RESUME=0

usage() {
    cat <<EOF
Usage: bash methods/task_vector_rzero/run.sh [--config PATH] [--resume] [--no-eval]

Runs the complete task-vector R-Zero loop. A run that already has state must be
continued with --resume; incompatible configurations are rejected.
EOF
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --config)
            CONFIG_PATH=$2
            shift 2
            ;;
        --resume)
            RESUME=1
            shift
            ;;
        --no-eval)
            EVALUATE_EACH_ROUND=false
            export EVALUATE_EACH_ROUND
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown argument: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
done

if [ ! -f "$CONFIG_PATH" ]; then
    echo "Config does not exist: $CONFIG_PATH" >&2
    exit 2
fi

# shellcheck source=config.sh
source "$CONFIG_PATH"
cd "$REPO_ROOT"
export PYTHONPATH="${REPO_ROOT}:${PYTHONPATH:-}"
export STORAGE_PATH HUGGINGFACENAME
export QUESTIONER_TRAIN_GPU_IDS VLLM_GPU_IDS VLLM_PORT_BASE
export QUESTIONER_MAX_STEPS QUESTIONER_MERGE_STEP QUESTIONER_SAVE_FREQ
export QUESTIONER_ROLLOUT_BATCH_SIZE QUESTIONER_ROLLOUT_N
export QUESTIONER_GLOBAL_BATCH_SIZE QUESTIONER_MICRO_BATCH_UPDATE
export QUESTIONER_MICRO_BATCH_EXPERIENCE QUESTIONER_VAL_BEFORE_TRAIN
export QUESTION_GPU_IDS SOLVER_MAX_RESPONSE_LENGTH SOLVER_TOTAL_EPOCHS
export SOLVER_MAX_STEPS SOLVER_VAL_FREQ SOLVER_MERGE_STEP SOLVER_LOGGER

if ! [[ "$NUM_ROUNDS" =~ ^[1-9][0-9]*$ ]]; then
    echo "NUM_ROUNDS must be a positive integer" >&2
    exit 2
fi
if [ "${#TASK_VECTOR_SCALES[@]}" -lt "$NUM_ROUNDS" ]; then
    echo "TASK_VECTOR_SCALES must contain at least NUM_ROUNDS entries" >&2
    exit 2
fi
for command in python3 bash; do
    command -v "$command" >/dev/null || { echo "Missing command: $command" >&2; exit 2; }
done

RUN_ROOT="${STORAGE_PATH}/task_vector_rzero/${RUN_NAME}"
QUESTIONERS_DIR="$RUN_ROOT/questioners"
DATASETS_DIR="$RUN_ROOT/datasets"
BASE_FITS_DIR="$RUN_ROOT/base_fits"
SOLVERS_DIR="$RUN_ROOT/composed_solvers"
EVALUATIONS_DIR="$RUN_ROOT/evaluations"
STATE_DIR="$RUN_ROOT/state"
LOG_DIR="$RUN_ROOT/logs"
STATE_FILE="$STATE_DIR/run_state.json"
BASE_MANIFEST="$STATE_DIR/base_manifest.json"

if [ -e "$STATE_FILE" ] && [ "$RESUME" != "1" ]; then
    echo "Run already exists at $RUN_ROOT. Use --resume or select a different RUN_NAME." >&2
    exit 2
fi
mkdir -p "$QUESTIONERS_DIR" "$DATASETS_DIR" "$BASE_FITS_DIR" \
    "$SOLVERS_DIR" "$EVALUATIONS_DIR" "$STATE_DIR" "$LOG_DIR"

BASE_MODEL_SOURCE=$BASE_MODEL
BASE_RESOLVE_ARGS=(--model "$BASE_MODEL_SOURCE" --manifest "$BASE_MANIFEST")
if [ -n "$BASE_REVISION" ]; then
    BASE_RESOLVE_ARGS+=(--revision "$BASE_REVISION")
fi
BASE_RESOLUTION=$(python3 "$METHOD_DIR/resolve_base.py" "${BASE_RESOLVE_ARGS[@]}")
BASE_MODEL=$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["resolved_path"])' "$BASE_RESOLUTION")
BASE_IDENTITY=$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["identity_sha256"])' "$BASE_RESOLUTION")
BASE_RESOLVED_REVISION=$(python3 -c 'import json,sys; print(json.loads(sys.argv[1]).get("resolved_revision") or "local")' "$BASE_RESOLUTION")

SCALES_CSV=$(IFS=,; echo "${TASK_VECTOR_SCALES[*]:0:$NUM_ROUNDS}")
csv_count() {
    local values=$1
    local entries
    IFS=',' read -r -a entries <<< "$values"
    echo "${#entries[@]}"
}
QUESTIONER_TRAIN_GPU_COUNT=$(csv_count "$QUESTIONER_TRAIN_GPU_IDS")
QUESTIONER_VLLM_GPU_COUNT=$(csv_count "$VLLM_GPU_IDS")
QUESTION_GPU_COUNT=$(csv_count "$QUESTION_GPU_IDS")
RUN_FINGERPRINT=$(python3 "$METHOD_DIR/pipeline_state.py" init \
    --state "$STATE_FILE" \
    --field "base_model_source=$BASE_MODEL_SOURCE" \
    --field "base_resolved_revision=$BASE_RESOLVED_REVISION" \
    --field "base_identity_sha256=$BASE_IDENTITY" \
    --field "model_abbr=$MODEL_ABBR" \
    --field "run_name=$RUN_NAME" \
    --field "num_rounds=$NUM_ROUNDS" \
    --field "task_vector_scales=$SCALES_CSV" \
    --field "questioner_max_steps=$QUESTIONER_MAX_STEPS" \
    --field "questioner_merge_step=$QUESTIONER_MERGE_STEP" \
    --field "questioner_save_freq=$QUESTIONER_SAVE_FREQ" \
    --field "questioner_train_gpu_count=$QUESTIONER_TRAIN_GPU_COUNT" \
    --field "questioner_vllm_gpu_count=$QUESTIONER_VLLM_GPU_COUNT" \
    --field "questioner_rollout_batch_size=$QUESTIONER_ROLLOUT_BATCH_SIZE" \
    --field "questioner_rollout_n=$QUESTIONER_ROLLOUT_N" \
    --field "questioner_global_batch_size=$QUESTIONER_GLOBAL_BATCH_SIZE" \
    --field "questioner_micro_batch_update=$QUESTIONER_MICRO_BATCH_UPDATE" \
    --field "questioner_micro_batch_experience=$QUESTIONER_MICRO_BATCH_EXPERIENCE" \
    --field "solver_generate_samples=$SOLVER_GENERATE_SAMPLES" \
    --field "question_gpu_count=$QUESTION_GPU_COUNT" \
    --field "solver_max_response_length=$SOLVER_MAX_RESPONSE_LENGTH" \
    --field "solver_total_epochs=$SOLVER_TOTAL_EPOCHS" \
    --field "solver_max_steps=$SOLVER_MAX_STEPS" \
    --field "solver_val_freq=$SOLVER_VAL_FREQ" \
    --field "solver_merge_step=$SOLVER_MERGE_STEP" \
    --field "dataset_score_range=${DATASET_MIN_SCORE}:${DATASET_MAX_SCORE}")

marker_path() {
    printf '%s/%s/_SUCCESS.json' "$STATE_DIR" "$1"
}

stage_is_complete() {
    local stage=$1
    local artifact=$2
    python3 "$METHOD_DIR/pipeline_state.py" check \
        --marker "$(marker_path "$stage")" \
        --fingerprint "$RUN_FINGERPRINT" \
        --require "$artifact"
}

guard_stage() {
    local stage=$1
    local artifact=$2
    local kind=${3:-generic}
    if stage_is_complete "$stage" "$artifact"; then
        echo "[resume] $stage is complete: $artifact"
        return 1
    fi
    if [ -e "$(marker_path "$stage")" ]; then
        echo "Stage marker is invalid or its artifacts are missing: $stage" >&2
        exit 2
    fi
    if [ -e "$artifact" ]; then
        if [ "$RESUME" != "1" ]; then
            echo "Untracked artifact exists for incomplete stage $stage: $artifact" >&2
            exit 2
        fi
        echo "[resume] validating artifact created before its success marker: $artifact"
        case "$kind" in
            checkpoint)
                python3 "$METHOD_DIR/validate_checkpoint.py" "$artifact"
                ;;
            composed)
                if [ "$FULL_LOAD_VALIDATE" = "true" ]; then
                    python3 "$METHOD_DIR/validate_checkpoint.py" "$artifact" --full-load
                else
                    python3 "$METHOD_DIR/validate_checkpoint.py" "$artifact"
                fi
                ;;
            dataset)
                python3 -c 'import hashlib,json,sys,pathlib; p=pathlib.Path(sys.argv[1]); m=json.load(open(p.parent/"dataset_manifest.json")); h=hashlib.sha256(p.read_bytes()).hexdigest(); assert h == m["parquet_sha256"], "dataset hash mismatch"' "$artifact"
                ;;
            evaluation)
                test -s "$artifact/final_results.jsonl"
                ;;
            generic)
                ;;
            *)
                echo "Unknown recovery validation kind: $kind" >&2
                exit 2
                ;;
        esac
        complete_stage "$stage" "$artifact" "recovered_after_atomic_move=true"
        echo "[resume] restored success marker for $stage"
        return 1
    fi
    return 0
}

complete_stage() {
    local stage=$1
    local artifact=$2
    shift 2
    local args=()
    local item
    for item in "$@"; do
        args+=(--meta "$item")
    done
    python3 "$METHOD_DIR/pipeline_state.py" complete \
        --state "$STATE_FILE" \
        --marker "$(marker_path "$stage")" \
        --stage "$stage" \
        --fingerprint "$RUN_FINGERPRINT" \
        --artifact "$artifact" \
        "${args[@]}"
}

ensure_model_upload() {
    local stage=$1
    local checkpoint=$2
    local repo=$3
    if [ "$UPLOAD_MODELS" != "true" ]; then
        return
    fi
    if stage_is_complete "$stage" "$checkpoint"; then
        echo "[resume] $stage is complete"
        return
    fi
    if [ -e "$(marker_path "$stage")" ]; then
        echo "Invalid model upload marker: $(marker_path "$stage")" >&2
        exit 2
    fi
    local privacy_flag=--private
    if [ "$HF_MODELS_PRIVATE" != "true" ]; then
        privacy_flag=--no-private
    fi
    python3 "$METHOD_DIR/upload_model.py" \
        --checkpoint "$checkpoint" --repo "$repo" "$privacy_flag"
    complete_stage "$stage" "$checkpoint" \
        "hf_repo=$repo" "private=$HF_MODELS_PRIVATE"
}

echo "Task-vector R-Zero run"
echo "  root: $RUN_ROOT"
echo "  Base: $BASE_MODEL"
echo "  Base source: $BASE_MODEL_SOURCE"
echo "  Base revision: $BASE_RESOLVED_REVISION"
echo "  Base identity: $BASE_IDENTITY"
echo "  rounds: $NUM_ROUNDS"
echo "  scales: $SCALES_CSV"
echo "  dataset mirror: $MIRROR_DATASETS"
echo "  model upload: $UPLOAD_MODELS"
echo "  evaluate each round: $EVALUATE_EACH_ROUND"

CURRENT_SOLVER=$BASE_MODEL
PREVIOUS_QUESTIONER=$BASE_MODEL
AUXILIARY_MODELS=()

for ((round=1; round<=NUM_ROUNDS; round++)); do
    echo
    echo "================ round $round / $NUM_ROUNDS ================"
    QUESTIONER_NAME="${MODEL_ABBR}_taskvec_questioner_v${round}"
    DATASET_NAME="${MODEL_ABBR}_taskvec_questions_v${round}"
    BASE_FIT_NAME="${MODEL_ABBR}_taskvec_basefit_v${round}"
    SOLVER_NAME="${MODEL_ABBR}_taskvec_solver_v${round}"

    QUESTIONER_DIR="$QUESTIONERS_DIR/q${round}"
    QUESTIONER_HF="$QUESTIONER_DIR/global_step_${QUESTIONER_MERGE_STEP}/actor/huggingface"
    QUESTIONER_STAGE="round_${round}/questioner"
    if guard_stage "$QUESTIONER_STAGE" "$QUESTIONER_HF" checkpoint; then
        QUESTIONER_TMP="$QUESTIONERS_DIR/.q${round}.inprogress"
        rm -rf "$QUESTIONER_TMP"
        QUESTIONER_OUTPUT_DIR="$QUESTIONER_TMP" \
        QUESTIONER_LOG_FILE="$LOG_DIR/questioner_v${round}.log" \
            bash scripts/questioner_train_penalty.sh \
                "$CURRENT_SOLVER" "$PREVIOUS_QUESTIONER" "$QUESTIONER_NAME"
        python3 "$METHOD_DIR/validate_checkpoint.py" \
            "$QUESTIONER_TMP/global_step_${QUESTIONER_MERGE_STEP}/actor/huggingface"
        mv "$QUESTIONER_TMP" "$QUESTIONER_DIR"
        complete_stage "$QUESTIONER_STAGE" "$QUESTIONER_HF" \
            "feedback_solver=$CURRENT_SOLVER" \
            "initial_questioner=$PREVIOUS_QUESTIONER"
    fi
    ensure_model_upload "round_${round}/questioner_hf_upload" "$QUESTIONER_HF" \
        "${HUGGINGFACENAME}/${QUESTIONER_NAME}"

    DATASET_DIR="$DATASETS_DIR/d${round}"
    DATASET_FILE="$DATASET_DIR/train.parquet"
    DATASET_STAGE="round_${round}/dataset"
    if guard_stage "$DATASET_STAGE" "$DATASET_FILE" dataset; then
        DATASET_TMP="$DATASETS_DIR/.d${round}.inprogress"
        rm -rf "$DATASET_TMP"
        mkdir -p "$DATASET_TMP/generated_question"
        IFS=',' read -r -a DATA_GPUS <<< "$QUESTION_GPU_IDS"
        NUM_SHARDS=${#DATA_GPUS[@]}
        echo "Generate with $QUESTIONER_HF; label with $CURRENT_SOLVER"
        STORAGE_PATH="$DATASET_TMP" \
            bash question_generate/question_generate.bash \
                "$QUESTIONER_HF" "$SOLVER_GENERATE_SAMPLES" "$DATASET_NAME"
        STORAGE_PATH="$DATASET_TMP" \
            bash question_evaluate/evaluate.sh "$CURRENT_SOLVER" "$DATASET_NAME"
        python3 "$METHOD_DIR/prepare_dataset.py" \
            --generated-dir "$DATASET_TMP/generated_question" \
            --experiment-name "$DATASET_NAME" \
            --num-shards "$NUM_SHARDS" \
            --output "$DATASET_TMP/train.parquet" \
            --min-score "$DATASET_MIN_SCORE" \
            --max-score "$DATASET_MAX_SCORE" \
            --no-upload
        mv "$DATASET_TMP" "$DATASET_DIR"
        DATASET_COUNT=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["filtered_count"])' "$DATASET_DIR/dataset_manifest.json")
        DATASET_SHA=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["parquet_sha256"])' "$DATASET_DIR/dataset_manifest.json")
        complete_stage "$DATASET_STAGE" "$DATASET_FILE" \
            "questioner=$QUESTIONER_HF" \
            "labeler_model=$CURRENT_SOLVER" \
            "manifest=$DATASET_DIR/dataset_manifest.json" \
            "filtered_count=$DATASET_COUNT" \
            "parquet_sha256=$DATASET_SHA"
    fi

    if [ "$MIRROR_DATASETS" = "true" ]; then
        MIRROR_STAGE="round_${round}/dataset_hf_mirror"
        MIRROR_MARKER="$(marker_path "$MIRROR_STAGE")"
        if ! stage_is_complete "$MIRROR_STAGE" "$DATASET_FILE"; then
            if [ -e "$MIRROR_MARKER" ]; then
                echo "Invalid dataset mirror marker: $MIRROR_MARKER" >&2
                exit 2
            fi
            python3 "$METHOD_DIR/upload_dataset.py" \
                --parquet "$DATASET_FILE" \
                --repo "${HUGGINGFACENAME}/${DATASET_NAME}" \
                --config "$DATASET_NAME"
            complete_stage "$MIRROR_STAGE" "$DATASET_FILE" \
                "hf_repo=${HUGGINGFACENAME}/${DATASET_NAME}" \
                "hf_config=$DATASET_NAME"
        else
            echo "[resume] $MIRROR_STAGE is complete"
        fi
    fi

    BASE_FIT_DIR="$BASE_FITS_DIR/a${round}"
    BASE_FIT_HF="$BASE_FIT_DIR/global_step_${SOLVER_MERGE_STEP}/actor/huggingface"
    BASE_FIT_STAGE="round_${round}/base_fit"
    if guard_stage "$BASE_FIT_STAGE" "$BASE_FIT_HF" checkpoint; then
        BASE_FIT_TMP="$BASE_FITS_DIR/.a${round}.inprogress"
        rm -rf "$BASE_FIT_TMP"
        bash "$METHOD_DIR/train_base_fit.sh" \
            "$BASE_MODEL" "$DATASET_FILE" "$BASE_FIT_TMP" "$BASE_FIT_NAME" \
            > >(tee -a "$LOG_DIR/base_fit_v${round}.log") 2>&1
        mv "$BASE_FIT_TMP" "$BASE_FIT_DIR"
        complete_stage "$BASE_FIT_STAGE" "$BASE_FIT_HF" \
            "train_init_model=$BASE_MODEL" \
            "dataset=$DATASET_FILE"
    fi
    ensure_model_upload "round_${round}/base_fit_hf_upload" "$BASE_FIT_HF" \
        "${HUGGINGFACENAME}/${BASE_FIT_NAME}"
    AUXILIARY_MODELS+=("$BASE_FIT_HF")

    SOLVER_DIR="$SOLVERS_DIR/v${round}"
    COMPOSE_STAGE="round_${round}/compose"
    if guard_stage "$COMPOSE_STAGE" "$SOLVER_DIR" composed; then
        COMPOSE_ARGS=(--base "$BASE_MODEL" --output "$SOLVER_DIR" \
            --base-provenance "$BASE_MANIFEST" \
            --chunk-elements "$TASK_VECTOR_CHUNK_ELEMENTS")
        for ((index=0; index<round; index++)); do
            COMPOSE_ARGS+=(--auxiliary "${AUXILIARY_MODELS[$index]}" \
                --scale "${TASK_VECTOR_SCALES[$index]}")
        done
        python3 "$METHOD_DIR/compose_task_vectors.py" "${COMPOSE_ARGS[@]}" \
            > >(tee -a "$LOG_DIR/compose_v${round}.log") 2>&1
        if [ "$FULL_LOAD_VALIDATE" = "true" ]; then
            python3 "$METHOD_DIR/validate_checkpoint.py" "$SOLVER_DIR" --full-load
        else
            python3 "$METHOD_DIR/validate_checkpoint.py" "$SOLVER_DIR"
        fi
        ROUND_SCALES=$(IFS=,; echo "${TASK_VECTOR_SCALES[*]:0:$round}")
        complete_stage "$COMPOSE_STAGE" "$SOLVER_DIR" \
            "base=$BASE_MODEL" \
            "auxiliary_count=$round" \
            "cumulative_scales=$ROUND_SCALES" \
            "manifest=$SOLVER_DIR/task_vector_manifest.json"
    fi
    ensure_model_upload "round_${round}/solver_hf_upload" "$SOLVER_DIR" \
        "${HUGGINGFACENAME}/${SOLVER_NAME}"

    if [ "$EVALUATE_EACH_ROUND" = "true" ]; then
        EVAL_DIR="$EVALUATIONS_DIR/v${round}"
        EVAL_STAGE="round_${round}/evaluation"
        if guard_stage "$EVAL_STAGE" "$EVAL_DIR" evaluation; then
            EVAL_TMP="$EVALUATIONS_DIR/.v${round}.inprogress"
            rm -rf "$EVAL_TMP"
            mkdir -p "$EVAL_TMP"
            STORAGE_PATH="$EVAL_TMP" \
            EVAL_ARTIFACT_DIR="$EVAL_TMP" \
            EVAL_LOG_DIR="$EVAL_TMP/logs" \
            EVAL_RUN_ID="${RUN_NAME}_v${round}" \
                bash evaluation/evaluate.bash "$SOLVER_DIR" \
                    > >(tee -a "$LOG_DIR/evaluation_v${round}.log") 2>&1
            mv "$EVAL_TMP" "$EVAL_DIR"
            complete_stage "$EVAL_STAGE" "$EVAL_DIR" "model=$SOLVER_DIR"
        fi
    fi

    CURRENT_SOLVER=$SOLVER_DIR
    PREVIOUS_QUESTIONER=$QUESTIONER_HF
done

echo
echo "Task-vector R-Zero completed successfully."
echo "Final solver: $CURRENT_SOLVER"
echo "Run state: $STATE_FILE"
