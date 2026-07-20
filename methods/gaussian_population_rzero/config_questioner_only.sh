#!/usr/bin/env bash

# Questioner-population-only experiment: keep Gaussian Questioner generation,
# but use the unperturbed current Solver for standard R-Zero feedback.
METHOD_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck disable=SC1090
source "$METHOD_DIR/config.sh"

RUN_NAME=qwen3_4b_gaussian_questioner_only_kq16_sq0p001_b4000_vb32_seed42_r5
SOLVER_POPULATION_ENABLED=false
