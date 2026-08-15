#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_ROOT=""
MODEL="Qwen/Qwen3-4B-Base"
GPU_IDS="0,1,2,3"
RESUME=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-root) RUN_ROOT="$2"; shift 2 ;;
    --model) MODEL="$2"; shift 2 ;;
    --gpu-ids) GPU_IDS="$2"; shift 2 ;;
    --resume) RESUME=1; shift ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "$RUN_ROOT" ]]; then
  echo "--run-root is required" >&2
  exit 2
fi

SOURCE="$RUN_ROOT/prepared/all_samples.jsonl"
TERRA="$RUN_ROOT/judge/judge_results.jsonl"
OUTPUT="$RUN_ROOT/base_judge"
if [[ ! -f "$SOURCE" || ! -f "$TERRA" ]]; then
  echo "Missing prepared questions or Terra reference under $RUN_ROOT" >&2
  exit 1
fi

COMMAND=(python "$HERE/base_judge.py"
  --input "$SOURCE"
  --output-dir "$OUTPUT"
  --model "$MODEL"
  --gpu-ids "$GPU_IDS")
if [[ "$RESUME" -eq 1 ]]; then
  COMMAND+=(--resume)
fi
"${COMMAND[@]}"

python "$HERE/base_judge_analyze.py" \
  --qwen-results "$OUTPUT/base_judge_results.jsonl" \
  --terra-results "$TERRA" \
  --output-dir "$OUTPUT/analysis"

python "$HERE/verify_base_judge.py" \
  --output-dir "$OUTPUT" \
  --require-analysis

echo "Base Judge completed: $OUTPUT"
