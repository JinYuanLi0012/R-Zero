#!/usr/bin/env bash

# Source this from the R-Zero repo root:
#   source env_rzero.sh

conda activate rzero-py310

export CUDA_HOME="${CONDA_PREFIX}"
export PATH="${CUDA_HOME}/bin:${PATH}"

# Keep source code on /storage1 and all large runtime artifacts on /engrfs.
export RZERO_CODE_ROOT="/storage1/jiaxinh/Active/jinyuan/R-zero"
export STORAGE_PATH="/engrfs/project/jiaxinh/jinyuan/R-zero-storage"

# Model/dataset downloads and local experiment metadata must not fill the code disk.
export HF_HOME="${STORAGE_PATH}/cache/huggingface"
export HF_HUB_CACHE="${HF_HOME}/hub"
export HF_DATASETS_CACHE="${HF_HOME}/datasets"
export WANDB_DIR="${STORAGE_PATH}/wandb"
export TMPDIR="${STORAGE_PATH}/tmp"

mkdir -p \
  "${STORAGE_PATH}" \
  "${HF_HUB_CACHE}" \
  "${HF_DATASETS_CACHE}" \
  "${WANDB_DIR}" \
  "${TMPDIR}"

export CUDA_VISIBLE_DEVICES="4,5,6,7"

# Set this before training, for example:
#   export HUGGINGFACENAME="your-hf-username"
export HUGGINGFACENAME="${HUGGINGFACENAME:-jinyuan222}"

export VLLM_DISABLE_COMPILE_CACHE=1

if [ -z "${OPENAI_API_KEY:-}" ] && [ -f "tokens.json" ]; then
  export OPENAI_API_KEY="$(python -c 'import json; from pathlib import Path; p=Path("tokens.json"); print(json.loads(p.read_text()).get("openai", ""))')"
fi
