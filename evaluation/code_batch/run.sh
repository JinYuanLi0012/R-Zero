#!/usr/bin/env bash
set -euo pipefail
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
exec "${CODE_EVAL_PYTHON:-python}" -u "$HERE/run.py" "$@"
