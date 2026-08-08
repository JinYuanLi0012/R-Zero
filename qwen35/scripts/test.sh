#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
cd "${repo_root}"
export PYTHONPATH="${repo_root}${PYTHONPATH:+:${PYTHONPATH}}"
python3 -m unittest discover -s qwen35/tests -v
python3 - <<'PY'
import ast
from pathlib import Path

for path in Path("qwen35").rglob("*.py"):
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
print("AST syntax check passed")
PY
