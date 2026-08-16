#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_ROOT=""
MODEL="Qwen/Qwen3-4B-Base"
GPU_IDS="0,1,2,3"
SCORE_BATCH_SIZE=1
RESUME=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-root) RUN_ROOT="$2"; shift 2 ;;
    --model) MODEL="$2"; shift 2 ;;
    --gpu-ids) GPU_IDS="$2"; shift 2 ;;
    --score-batch-size) SCORE_BATCH_SIZE="$2"; shift 2 ;;
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
OUTPUT="$RUN_ROOT/base_judge_binary_logprob"
if [[ ! -f "$SOURCE" || ! -f "$TERRA" ]]; then
  echo "Missing prepared questions or Terra reference under $RUN_ROOT" >&2
  exit 1
fi

COMMAND=(python "$HERE/binary_logprob_judge.py"
  --input "$SOURCE"
  --output-dir "$OUTPUT"
  --model "$MODEL"
  --gpu-ids "$GPU_IDS"
  --score-batch-size "$SCORE_BATCH_SIZE")
if [[ "$RESUME" -eq 1 ]]; then
  COMMAND+=(--resume)
fi
"${COMMAND[@]}"

python "$HERE/binary_logprob_analyze.py" \
  --results "$OUTPUT/binary_logprob_results.jsonl" \
  --terra-results "$TERRA" \
  --output-dir "$OUTPUT/analysis"

python "$HERE/verify_binary_logprob_judge.py" \
  --output-dir "$OUTPUT" \
  --require-analysis

echo "Binary logprob Judge completed: $OUTPUT"
