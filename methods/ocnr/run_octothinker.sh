#!/usr/bin/env bash
set -euo pipefail
if [[ $# -gt 1 || ( $# -eq 1 && "$1" != --resume ) ]]; then
    echo "Usage: bash methods/ocnr/run_octothinker.sh [--resume]" >&2
    exit 2
fi
METHOD_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
exec bash "$METHOD_DIR/run.sh" --config "$METHOD_DIR/config_octothinker.json" "$@"
