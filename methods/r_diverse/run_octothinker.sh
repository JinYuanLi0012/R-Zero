#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
exec bash methods/r_diverse/run.sh \
  --base-model OctoThinker/OctoThinker-3B-Hybrid-Base \
  --backbone-prompt octothinker \
  --run-name octothinker_3b_hybrid_r_diverse_v1 "$@"
