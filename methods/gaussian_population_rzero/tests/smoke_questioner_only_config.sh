#!/usr/bin/env bash
# One-round GPU acceptance profile for Questioner-only Gaussian population.
METHOD_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
# shellcheck disable=SC1090
source "$METHOD_DIR/tests/smoke_config.sh"

RUN_NAME=gaussian_questioner_only_smoke
SOLVER_POPULATION_ENABLED=false
