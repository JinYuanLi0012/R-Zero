#!/usr/bin/env bash
# One-round GPU acceptance profile. Override BASE_MODEL with a small local HF checkpoint.
METHOD_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
RUN_NAME=${RUN_NAME:-gaussian_population_smoke}
# shellcheck disable=SC1090
source "$METHOD_DIR/config.sh"

NUM_ROUNDS=1
QUESTIONER_POPULATION_SIZE=3
SOLVER_POPULATION_SIZE=3
QUESTION_TOTAL_BUDGET=7

# Keep the smoke run short while exercising both GRPO checkpoint transitions.
QUESTIONER_MAX_STEPS=2
QUESTIONER_MERGE_STEP=1
QUESTIONER_SAVE_FREQ=1
QUESTIONER_ROLLOUT_BATCH_SIZE=8
SOLVER_MAX_STEPS=2
SOLVER_MERGE_STEP=1
SOLVER_SAVE_FREQ=1
SOLVER_SAVE_LIMIT=2
EVALUATE_EACH_ROUND=false
