#!/usr/bin/env bash
set -euo pipefail

output=${1:-qwen35/environment/requirements.lock}
python3.12 -m pip freeze --all | LC_ALL=C sort > "${output}"
python3.12 -m verl.utils.collect_env > "${output%.lock}.environment.txt" 2>&1 || true
echo "Wrote ${output} and ${output%.lock}.environment.txt"
