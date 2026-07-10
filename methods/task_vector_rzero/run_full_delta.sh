#!/usr/bin/env bash
set -euo pipefail

METHOD_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
export TASK_VECTOR_METHOD=full
export RUN_VARIANT_SUFFIX=full_delta
exec bash "$METHOD_DIR/run.sh" "$@"
