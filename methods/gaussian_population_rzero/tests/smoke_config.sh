#!/usr/bin/env bash
# Production-shaped, one-round/one-update acceptance profile.
# Use the same BASE_MODEL as the formal run; only population size and run length
# are reduced. All rollout, sampling, filtering, token, and GPU settings are
# inherited unchanged from config.sh.
METHOD_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
RUN_NAME=${RUN_NAME:-gaussian_population_smoke}
# shellcheck disable=SC1090
source "$METHOD_DIR/config.sh"

NUM_ROUNDS=1
QUESTIONER_POPULATION_SIZE=4
SOLVER_POPULATION_SIZE=4
QUESTION_TOTAL_BUDGET=1024

# Save and inherit the first real update for each central model.
QUESTIONER_MAX_STEPS=1
QUESTIONER_MERGE_STEP=1
QUESTIONER_SAVE_FREQ=1
SOLVER_MAX_STEPS=1
SOLVER_MERGE_STEP=1
SOLVER_SAVE_FREQ=1
EVALUATE_EACH_ROUND=false
