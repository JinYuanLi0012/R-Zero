#!/usr/bin/env bash

# Source this from the R-Zero repo root:
#   source env_rzero.sh

conda activate rzero-py310

export CUDA_HOME="${CONDA_PREFIX}"
export PATH="${CUDA_HOME}/bin:${PATH}"

export STORAGE_PATH="/data/jinyuan/rzero_storage"
export CUDA_VISIBLE_DEVICES="4,5,6,7"

# Set this before training, for example:
#   export HUGGINGFACENAME="your-hf-username"
export HUGGINGFACENAME="${HUGGINGFACENAME:-jinyuan222}"

export VLLM_DISABLE_COMPILE_CACHE=1

if [ -z "${OPENAI_API_KEY:-}" ] && [ -f "tokens.json" ]; then
  export OPENAI_API_KEY="$(python -c 'import json; from pathlib import Path; p=Path("tokens.json"); print(json.loads(p.read_text()).get("openai", ""))')"
fi
