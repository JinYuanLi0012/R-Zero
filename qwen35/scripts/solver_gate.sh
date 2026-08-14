#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
source_run_dir=
output_dir=
config="${repo_root}/qwen35/configs/a100_4x_qwen35_4b_base_smoke.yaml"

while (($#)); do
  case "$1" in
    --source-run-dir) source_run_dir=$2; shift 2 ;;
    --output-dir) output_dir=$2; shift 2 ;;
    --config) config=$2; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "${source_run_dir}" || -z "${output_dir}" ]]; then
  echo "usage: solver_gate.sh --source-run-dir RUN --output-dir OUTPUT [--config CONFIG]" >&2
  exit 2
fi

model="${source_run_dir}/models/base"
train_file="${source_run_dir}/round_01/dataset/train.parquet"
val_file="${source_run_dir}/data/seed/solver_val.parquet"
for required in "${model}/config.json" "${train_file}" "${val_file}"; do
  [[ -s "${required}" ]] || { echo "missing gate input: ${required}" >&2; exit 1; }
done

export VERL_SOURCE_ROOT=${VERL_SOURCE_ROOT:-/opt/verl}
export PYTHONPATH="${VERL_SOURCE_ROOT}:${repo_root}${PYTHONPATH:+:${PYTHONPATH}}"
export VLLM_USE_V1=${VLLM_USE_V1:-1}
export VLLM_NO_USAGE_STATS=${VLLM_NO_USAGE_STATS:-1}
unset ROCR_VISIBLE_DEVICES HIP_VISIBLE_DEVICES RAY_ADDRESS
unset RAY_EXPERIMENTAL_NOSET_CUDA_VISIBLE_DEVICES
unset RAY_EXPERIMENTAL_NOSET_ROCR_VISIBLE_DEVICES
unset RAY_EXPERIMENTAL_NOSET_HIP_VISIBLE_DEVICES

cache_scope=${SLURM_JOB_ID:-interactive}
export RZERO_NODE_CACHE_ROOT=${RZERO_NODE_CACHE_ROOT:-/tmp/rzero-qwen35-${UID}/${cache_scope}}
export XDG_CACHE_HOME=${XDG_CACHE_HOME:-${RZERO_NODE_CACHE_ROOT}/xdg}
export TRITON_CACHE_DIR=${TRITON_CACHE_DIR:-${RZERO_NODE_CACHE_ROOT}/triton}
export TORCHINDUCTOR_CACHE_DIR=${TORCHINDUCTOR_CACHE_DIR:-${RZERO_NODE_CACHE_ROOT}/torchinductor}
export CUDA_CACHE_PATH=${CUDA_CACHE_PATH:-${RZERO_NODE_CACHE_ROOT}/cuda}
export VLLM_CACHE_ROOT=${VLLM_CACHE_ROOT:-${RZERO_NODE_CACHE_ROOT}/vllm}
export FLASHINFER_WORKSPACE_BASE=${FLASHINFER_WORKSPACE_BASE:-${RZERO_NODE_CACHE_ROOT}/flashinfer}
mkdir -p "${XDG_CACHE_HOME}" "${TRITON_CACHE_DIR}" "${TORCHINDUCTOR_CACHE_DIR}" \
  "${CUDA_CACHE_PATH}" "${VLLM_CACHE_ROOT}" "${FLASHINFER_WORKSPACE_BASE}" \
  "${output_dir}/logs"

checkpoint_root="${output_dir}/checkpoints"
export_dir="${output_dir}/export"

python3.12 -m qwen35.rzero.train_grpo \
  --role solver \
  --config "${config}" \
  --model "${model}" \
  --train-file "${train_file}" \
  --val-file "${val_file}" \
  --output-dir "${checkpoint_root}" \
  --experiment-name solver_gate \
  --resume 2>&1 | tee -a "${output_dir}/logs/train.log"

if [[ ! -s "${export_dir}/config.json" ]]; then
  temporary_export="${export_dir}.tmp"
  [[ ! -e "${temporary_export}" ]] || {
    echo "incomplete temporary export exists: ${temporary_export}" >&2
    exit 1
  }
  python3.12 -m qwen35.rzero.export_model \
    --checkpoint-root "${checkpoint_root}" \
    --step 1 \
    --target-dir "${temporary_export}" 2>&1 | tee -a "${output_dir}/logs/export.log"
  [[ -s "${temporary_export}/config.json" ]] || { echo "Solver gate export has no config.json" >&2; exit 1; }
  compgen -G "${temporary_export}/*.safetensors*" >/dev/null || {
    echo "Solver gate export has no safetensors" >&2
    exit 1
  }
  mv "${temporary_export}" "${export_dir}"
fi

echo "RZERO_SOLVER_GATE_OK"
