#!/usr/bin/env bash
# Five-round original experiment, replacing only the frozen semantic judge.
set -euo pipefail
METHOD_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
: "${STORAGE_PATH:?Source the server environment first}"
: "${OCTO_FROZEN_JUDGE_MODEL:?Set the checksum-pinned merged SFT judge directory}"
if [[ $# -gt 1 || ( $# -eq 1 && "$1" != --resume ) ]]; then
    echo "Usage: bash $0 [--resume]" >&2; exit 2
fi
export OCTO_MODEL_ABBR=${OCTO_MODEL_ABBR:-octothinker_3b_hybrid_validity_rzero_semantic_novelty_gate_k8_4gpu_sftjudge_v1}
export OCTO_NUM_ROUNDS=5
RUN_ROOT=${RZERO_RUN_ROOT:-$STORAGE_PATH/rzero_runs/$OCTO_MODEL_ABBR}
if [[ ${1:-} == --resume ]]; then
    if [[ ! -s "$RUN_ROOT/state/run_state.json" ]]; then
        echo "Refuse resume without existing pipeline state: $RUN_ROOT" >&2; exit 2
    fi
elif [[ -e "$RUN_ROOT" || \
      -e "$STORAGE_PATH/models/${OCTO_MODEL_ABBR}_questioner_v1" || \
      -e "$STORAGE_PATH/models/${OCTO_MODEL_ABBR}_solver_v1" ]]; then
    echo "Refuse to start fresh over existing run/checkpoint: $OCTO_MODEL_ABBR" >&2; exit 2
fi
bash "$METHOD_DIR/run_octothinker.sh" "$@"
