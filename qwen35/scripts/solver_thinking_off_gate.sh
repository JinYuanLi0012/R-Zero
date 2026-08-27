#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
candidates=
solver_model=
output_dir=

while (($#)); do
  case "$1" in
    --candidates) candidates=$2; shift 2 ;;
    --solver-model) solver_model=$2; shift 2 ;;
    --output-dir) output_dir=$2; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "${candidates}" || -z "${solver_model}" || -z "${output_dir}" ]]; then
  echo "usage: solver_thinking_off_gate.sh --candidates JSON --solver-model MODEL --output-dir OUTPUT" >&2
  exit 2
fi
for required in "${candidates}" "${solver_model}/config.json" "${solver_model}/RZERO_MODEL_REVISION"; do
  [[ -s "${required}" ]] || { echo "missing Solver thinking-off gate input: ${required}" >&2; exit 2; }
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

python3.12 -m qwen35.rzero.diagnostics.evaluate_solver_thinking_off \
  --model "${solver_model}" \
  --input "${candidates}" \
  --output-dir "${output_dir}" \
  --samples 9 \
  --seed 0 \
  --temperature 1.0 \
  --top-p 1.0 \
  --top-k 40 \
  --max-tokens 4096 \
  --min-score 0.3 \
  --max-score 0.8 \
  --expected-total-candidates 64 \
  --expected-parseable-candidates 60 \
  --expected-revision 1001bb4 \
  --resume 2>&1 | tee -a "${output_dir}/logs/evaluate.log"

echo "RZERO_SOLVER_THINKING_OFF_GATE_OK"
echo "summary=${output_dir}/summary.json"
