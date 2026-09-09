#!/usr/bin/env bash
set -euo pipefail
METHOD_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "$METHOD_DIR/../../.." && pwd)
cd "$REPO_ROOT"
export PYTHONPATH="$REPO_ROOT:${PYTHONPATH:-}"
python -m methods.validity_rzero.three_question_pilot.run "$@"
