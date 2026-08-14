#!/usr/bin/env bash
set -euo pipefail

METHOD_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
: "${SMOKE_MODEL:=Qwen/Qwen3-4B-Base}"
: "${GPU_IDS:=0,1,2,3}"
: "${SMOKE_INPUT:?Set SMOKE_INPUT to a JSONL file containing exactly two prepared questions}"
: "${SMOKE_OUTPUT:=/tmp/rzero_epistemic_gpu_smoke}"

[[ $(wc -l < "$SMOKE_INPUT") -eq 2 ]] || { echo "SMOKE_INPUT must have exactly two lines" >&2; exit 1; }
python "$METHOD_DIR/population_driver.py" --model "$SMOKE_MODEL" --input "$SMOKE_INPUT" \
  --output-dir "$SMOKE_OUTPUT/raw" --round-index 1 --sigmas 0.0001 --gpu-ids "$GPU_IDS" \
  --population-size 8 --global-seed 42 --samples 2 --max-tokens 512 --batch-size 2
python "$METHOD_DIR/aggregate.py" --input "$SMOKE_INPUT" --raw-root "$SMOKE_OUTPUT/raw" \
  --output-dir "$SMOKE_OUTPUT/summary" --sigmas 0.0001 --population-size 8 --samples 2
echo "GPU smoke artifacts: $SMOKE_OUTPUT"
