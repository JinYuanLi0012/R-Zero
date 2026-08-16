#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 RUN_ROOT" >&2
  exit 2
fi

RUN_ROOT="$1"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SMOKE_ROOT="$(mktemp -d)"
trap 'echo "Smoke artifacts: $SMOKE_ROOT"' EXIT
head -n 2 "$RUN_ROOT/prepared/all_samples.jsonl" > "$SMOKE_ROOT/two_questions.jsonl"

python "$HERE/binary_logprob_judge.py" \
  --input "$SMOKE_ROOT/two_questions.jsonl" \
  --output-dir "$SMOKE_ROOT/binary_logprob" \
  --model Qwen/Qwen3-4B-Base \
  --gpu-ids 0,1,2,3 \
  --expected-count 2 \
  --max-analysis-tokens 256 \
  --batch-size 2

python "$HERE/verify_binary_logprob_judge.py" \
  --output-dir "$SMOKE_ROOT/binary_logprob" \
  --expected-count 2
