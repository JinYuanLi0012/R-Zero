#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../../.."
export PYTHONPATH="$PWD:${PYTHONPATH:-}"
exec python3 -m methods.validity_rzero.three_question_pilot.train_solver "$@"
