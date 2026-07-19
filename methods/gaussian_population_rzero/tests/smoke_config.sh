#!/usr/bin/env bash
# One-round GPU acceptance profile. Override BASE_MODEL with a small local HF checkpoint.
METHOD_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
RUN_NAME=${RUN_NAME:-gaussian_population_smoke}
# shellcheck disable=SC1090
source "$METHOD_DIR/config.sh"

NUM_ROUNDS=1
QUESTIONER_POPULATION_SIZE=3
SOLVER_POPULATION_SIZE=3
# Keep this small, but large enough that standard filtering reliably leaves one
# four-GPU Solver rollout batch.
QUESTION_TOTAL_BUDGET=32

# Preserve the formal experiment's stage layout: two center-Questioner GPUs,
# two concurrent Solver-expert GPUs, then all four GPUs for generation/labeling
# and central-Solver FSDP training.
QUESTIONER_TRAIN_GPU_IDS=0,1
SOLVER_EXPERT_GPU_IDS=2,3
QUESTION_GENERATION_GPU_IDS=0,1,2,3
CENTER_ROLLOUT_TENSOR_PARALLEL_SIZE=2

# Keep the smoke run short while exercising both GRPO checkpoint transitions.
QUESTIONER_MAX_STEPS=2
QUESTIONER_MERGE_STEP=1
QUESTIONER_SAVE_FREQ=1
QUESTIONER_ROLLOUT_BATCH_SIZE=4
SOLVER_MAX_STEPS=2
SOLVER_MERGE_STEP=1
SOLVER_SAVE_FREQ=1
SOLVER_SAVE_LIMIT=2
SOLVER_ROLLOUT_BATCH_SIZE=4
SOLVER_ROLLOUT_N=5
SOLVER_GLOBAL_BATCH_SIZE=4
DATASET_MIN_SCORE=0.0
DATASET_MAX_SCORE=1.0
EVALUATE_EACH_ROUND=false
