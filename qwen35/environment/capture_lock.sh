#!/usr/bin/env bash
set -euo pipefail

output=${1:-qwen35/environment/requirements.lock}
verl_source_root=${VERL_SOURCE_ROOT:-/opt/verl}
python3.12 -m pip freeze --all | LC_ALL=C sort > "${output}"
(cd "${verl_source_root}" && python3.12 -m verl.utils.collect_env) > "${output%.lock}.environment.txt" 2>&1 || true
echo "Wrote ${output} and ${output%.lock}.environment.txt"
