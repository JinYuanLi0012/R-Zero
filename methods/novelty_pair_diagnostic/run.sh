#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
config=${1:?Usage: bash methods/novelty_pair_diagnostic/run.sh CONFIG_JSON}
for stage in prepare bleu reference embedding judge; do
  python -m methods.novelty_pair_diagnostic.pipeline "$stage" --config "$config"
done
# A failed calibration still yields an explicitly incomplete diagnostic report.
if ! python -m methods.novelty_pair_diagnostic.pipeline calibrate --config "$config"; then
  python -m methods.novelty_pair_diagnostic.pipeline report --config "$config"
  exit 1
fi
python -m methods.novelty_pair_diagnostic.pipeline report --config "$config"
