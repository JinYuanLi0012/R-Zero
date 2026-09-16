"""Commit a complete annotation shard before removing its generated input."""

import json
import os
from pathlib import Path


def save_results(results, output_file, input_file):
    output = Path(output_file)
    temporary = output.with_name(f'.{output.name}.tmp-{os.getpid()}')
    try:
        with temporary.open('w', encoding='utf-8') as stream:
            json.dump(results, stream, indent=4)
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)
    Path(input_file).unlink()
