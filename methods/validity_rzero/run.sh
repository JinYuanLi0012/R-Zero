#!/usr/bin/env bash
set -euo pipefail

METHOD_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "${METHOD_DIR}/../.." && pwd)
cd "${REPO_ROOT}"

export VALIDITY_RZERO_ENABLED=1
export VALIDITY_RZERO_INITIAL_SOLVER=${VALIDITY_RZERO_INITIAL_SOLVER:-/engrfs/project/jiaxinh/jinyuan/R-zero-storage/models/qwen3_4b_validity_rl_terra_clean_v1/global_step_10/actor/huggingface}
: "${TERRA_REPLAY_DATASET:?set TERRA_REPLAY_DATASET to the Terra replay dataset}"
: "${TERRA_REPLAY_RATIO:?set TERRA_REPLAY_RATIO to the formal experiment value}"

BASE_MODEL=${BASE_MODEL:-Qwen/Qwen3-4B-Base}
MODEL_ABBR=${MODEL_ABBR:-qwen3_4b_validity_rzero}

bash scripts/main.sh --no-eval "$@" "${BASE_MODEL}" "${MODEL_ABBR}"
