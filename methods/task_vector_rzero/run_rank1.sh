#!/usr/bin/env bash
set -euo pipefail

METHOD_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
export TASK_VECTOR_METHOD=relex_rank1
export RUN_VARIANT_SUFFIX=relex_rank1
exec bash "$METHOD_DIR/run.sh" "$@"
