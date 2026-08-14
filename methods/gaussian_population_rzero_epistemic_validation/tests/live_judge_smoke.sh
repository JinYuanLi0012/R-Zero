#!/usr/bin/env bash
set -euo pipefail

METHOD_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
INPUT=${1:?Pass a one-row prepared JSONL file}
OUTPUT=${2:-/tmp/rzero_epistemic_judge_smoke}
[[ $(wc -l < "$INPUT") -eq 1 ]] || { echo "input must contain one row" >&2; exit 1; }
python "$METHOD_DIR/judge.py" --input "$INPUT" --output-dir "$OUTPUT" \
  --model "${JUDGE_MODEL:-gpt-5.6}" --concurrency 1 --human-review-size 1
