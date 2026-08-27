#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
source_run_dir=
solver_model=
output_dir=

while (($#)); do
  case "$1" in
    --source-run-dir) source_run_dir=$2; shift 2 ;;
    --solver-model) solver_model=$2; shift 2 ;;
    --output-dir) output_dir=$2; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "${source_run_dir}" || -z "${solver_model}" || -z "${output_dir}" ]]; then
  echo "usage: questioner_candidate_gate.sh --source-run-dir RUN --solver-model MODEL --output-dir OUTPUT" >&2
  exit 2
fi

raw="${source_run_dir}/round_01/diagnostics/post_train_candidates/qwen35_questioner_step1_thinking_off_raw_64.json"
candidates="${output_dir}/candidates.json"
scored="${output_dir}/scored_n9.json"
summary="${output_dir}/summary.json"
for required in "${raw}" "${solver_model}/config.json"; do
  [[ -s "${required}" ]] || { echo "missing candidate gate input: ${required}" >&2; exit 2; }
done

export VERL_SOURCE_ROOT=${VERL_SOURCE_ROOT:-/opt/verl}
export PYTHONPATH="${VERL_SOURCE_ROOT}:${repo_root}${PYTHONPATH:+:${PYTHONPATH}}"
export VLLM_USE_V1=${VLLM_USE_V1:-1}
export VLLM_NO_USAGE_STATS=${VLLM_NO_USAGE_STATS:-1}
unset ROCR_VISIBLE_DEVICES HIP_VISIBLE_DEVICES RAY_ADDRESS

cache_scope=${SLURM_JOB_ID:-interactive}
cache_root=${RZERO_NODE_CACHE_ROOT:-/tmp/rzero-qwen35-${UID}/${cache_scope}}
export XDG_CACHE_HOME="${cache_root}/xdg"
export TRITON_CACHE_DIR="${cache_root}/triton"
export TORCHINDUCTOR_CACHE_DIR="${cache_root}/torchinductor"
export CUDA_CACHE_PATH="${cache_root}/cuda"
export VLLM_CACHE_ROOT="${cache_root}/vllm"
export FLASHINFER_WORKSPACE_BASE="${cache_root}/flashinfer"
export TMPDIR="${cache_root}/tmp"
mkdir -p \
  "${XDG_CACHE_HOME}" "${TRITON_CACHE_DIR}" "${TORCHINDUCTOR_CACHE_DIR}" \
  "${CUDA_CACHE_PATH}" "${VLLM_CACHE_ROOT}" "${FLASHINFER_WORKSPACE_BASE}" \
  "${TMPDIR}" "${output_dir}/logs"

python3.12 -m qwen35.rzero.diagnostics.questioner_candidate_gate prepare \
  --raw "${raw}" \
  --output "${candidates}" 2>&1 | tee -a "${output_dir}/logs/prepare.log"

python3.12 -m qwen35.rzero.evaluate_candidates \
  --model "${solver_model}" \
  --input "${candidates}" \
  --output "${scored}" \
  --samples 9 \
  --seed 0 2>&1 | tee -a "${output_dir}/logs/evaluate.log"

python3.12 -m qwen35.rzero.diagnostics.questioner_candidate_gate summarize \
  --candidates "${candidates}" \
  --scored "${scored}" \
  --output "${summary}" \
  --min-score 0.3 \
  --max-score 0.8 2>&1 | tee -a "${output_dir}/logs/summarize.log"

echo "RZERO_QUESTIONER_CANDIDATE_GATE_OK"
echo "summary=${summary}"
