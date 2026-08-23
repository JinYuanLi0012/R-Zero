#!/usr/bin/env bash
set -euo pipefail

METHOD_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

: "${MODEL_ABBR:?set a dedicated smoke MODEL_ABBR}"
export RZERO_NUM_ROUNDS=1
export QUESTIONER_MAX_STEPS=1
export QUESTIONER_MERGE_STEP=1
export SOLVER_MAX_STEPS=1
export SOLVER_MERGE_STEP=1
export SOLVER_GENERATE_SAMPLES=${SOLVER_GENERATE_SAMPLES:?set a smaller value that still yields one full Solver batch}

bash "${METHOD_DIR}/run.sh" "$@"
