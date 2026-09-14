#!/usr/bin/env bash
set -euo pipefail
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
TOOLS=${CODE_EVAL_TOOLS:-${STORAGE_PATH:?Set STORAGE_PATH or CODE_EVAL_TOOLS}/code_eval_tools}
mkdir -p "$TOOLS"
TOOLS=$(cd "$TOOLS" && pwd)
PYTHON=${CODE_EVAL_SETUP_PYTHON:-python3}
"$PYTHON" -c 'import sys; assert sys.version_info >= (3, 10), "Python >= 3.10 required"'
if [ ! -x "$TOOLS/venv/bin/python" ]; then
  "$PYTHON" -m venv "$TOOLS/venv"
fi
"$TOOLS/venv/bin/python" -m pip install -r "$HERE/requirements-judge.txt"
for name in evalplus livecodebench; do
  revision=$("$TOOLS/venv/bin/python" -c 'import json,sys; print(json.load(open(sys.argv[1]))[sys.argv[2]])' "$HERE/versions.json" "$name")
  case "$name" in
    evalplus) url=https://github.com/evalplus/evalplus.git ;;
    livecodebench) url=https://github.com/LiveCodeBench/LiveCodeBench.git ;;
  esac
  if [ ! -d "$TOOLS/$name/.git" ]; then
    git clone "$url" "$TOOLS/$name"
  fi
  if [ -n "$(git -C "$TOOLS/$name" status --porcelain)" ]; then
    echo "Refusing to change modified official checkout: $TOOLS/$name" >&2
    exit 1
  fi
  if ! git -C "$TOOLS/$name" cat-file -e "$revision^{commit}"; then
    git -C "$TOOLS/$name" fetch origin "$revision"
  fi
  git -C "$TOOLS/$name" checkout --detach "$revision"
done
"$TOOLS/venv/bin/python" "$HERE/worker.py" check --tools "$TOOLS"
echo "Ready. Run with CODE_EVAL_TOOLS=$TOOLS"
