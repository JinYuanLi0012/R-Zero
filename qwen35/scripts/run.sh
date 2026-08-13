#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
export VERL_SOURCE_ROOT=${VERL_SOURCE_ROOT:-/opt/verl}
export PYTHONPATH="${VERL_SOURCE_ROOT}:${repo_root}${PYTHONPATH:+:${PYTHONPATH}}"
export VLLM_USE_V1=${VLLM_USE_V1:-1}
# RIS Home is quota-limited. vLLM's optional telemetry writes below $HOME and
# is unnecessary for a reproducible training run.
export VLLM_NO_USAGE_STATS=${VLLM_NO_USAGE_STATS:-1}

# Pyxis may expose ROCm compatibility variables even on an NVIDIA allocation.
# verl/Ray deliberately reject ROCR plus CUDA visibility because the two use
# different index spaces. This pipeline is pinned to NVIDIA CUDA, so retain
# CUDA_VISIBLE_DEVICES and remove the inapplicable AMD selectors before Ray
# starts and snapshots the driver environment.
unset ROCR_VISIBLE_DEVICES HIP_VISIBLE_DEVICES

# GPU nodes commonly expose a small quota-backed $HOME. Keep compiler and
# rollout caches on node-local storage so Triton/FlashInfer JIT compilation
# cannot exhaust that quota during a long run. A scheduler wrapper may set
# RZERO_NODE_CACHE_ROOT explicitly; otherwise each Slurm job gets an isolated
# directory and non-Slurm runs share an interactive directory.
cache_scope=${SLURM_JOB_ID:-interactive}
export RZERO_NODE_CACHE_ROOT=${RZERO_NODE_CACHE_ROOT:-/tmp/rzero-qwen35-${UID}/${cache_scope}}
export XDG_CACHE_HOME=${XDG_CACHE_HOME:-${RZERO_NODE_CACHE_ROOT}/xdg}
export TRITON_CACHE_DIR=${TRITON_CACHE_DIR:-${RZERO_NODE_CACHE_ROOT}/triton}
export TORCHINDUCTOR_CACHE_DIR=${TORCHINDUCTOR_CACHE_DIR:-${RZERO_NODE_CACHE_ROOT}/torchinductor}
export CUDA_CACHE_PATH=${CUDA_CACHE_PATH:-${RZERO_NODE_CACHE_ROOT}/cuda}
export VLLM_CACHE_ROOT=${VLLM_CACHE_ROOT:-${RZERO_NODE_CACHE_ROOT}/vllm}
export FLASHINFER_WORKSPACE_BASE=${FLASHINFER_WORKSPACE_BASE:-${RZERO_NODE_CACHE_ROOT}/flashinfer}

mkdir -p \
  "${XDG_CACHE_HOME}" \
  "${TRITON_CACHE_DIR}" \
  "${TORCHINDUCTOR_CACHE_DIR}" \
  "${CUDA_CACHE_PATH}" \
  "${VLLM_CACHE_ROOT}" \
  "${FLASHINFER_WORKSPACE_BASE}"

exec python3.12 -m qwen35.rzero.pipeline.orchestrator "$@"
