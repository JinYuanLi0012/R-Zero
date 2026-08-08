#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
export PYTHONPATH="${repo_root}${PYTHONPATH:+:${PYTHONPATH}}"
export VLLM_USE_V1=${VLLM_USE_V1:-1}

exec python3.12 -m qwen35.rzero.pipeline.orchestrator "$@"
