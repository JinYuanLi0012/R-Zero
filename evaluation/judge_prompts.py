"""Versioned math recheck prompts; original mode intentionally preserves reversed roles."""

import json
import os
from pathlib import Path

MODES = ('corrected', 'rzero-original')
UPSTREAM_COMMIT = '5699329d018d79535b7910abdedf5a6eebf355fd'
UPSTREAM_SOURCE = f'https://github.com/Chengsong-Huang/R-Zero/blob/{UPSTREAM_COMMIT}/evaluation/results_recheck.py'
ORIGINAL_TEMPLATE = ('Hi, there is a answer: {answer}\n\n, and the ground truth answer is: {response}'
                     '\n\n, please check whether the answer is correct or not, and return the **only** Yes or No.')


def prompt_mode(mode=None):
    mode = os.getenv('RECHECK_JUDGE_PROMPT_MODE', 'corrected') if mode is None else mode
    if mode not in MODES:
        raise ValueError('RECHECK_JUDGE_PROMPT_MODE must be corrected or rzero-original')
    return mode


def prompt_metadata(mode=None):
    mode = prompt_mode(mode)
    metadata = {'prompt_mode': mode, 'prompt_version': 'math-recheck-local-v1'}
    if mode == 'rzero-original':
        metadata.update(prompt_version='rzero-original-5699329d-v1',
                        prompt_source_commit=UPSTREAM_COMMIT, prompt_source=UPSTREAM_SOURCE)
    return metadata


def messages(answer, response, mode=None, *, resume_api=False):
    if prompt_mode(mode) == 'rzero-original':
        # Upstream process_example receives (benchmark reference, solver output).
        # Do NOT fix this mapping in the compatibility mode.
        content = ORIGINAL_TEMPLATE.format(answer=answer, response=response)
    else:
        # Preserve the existing corrected bytes, including the resume API variant.
        content = (f'Hi, there is a model response: {response}\n\n'
                   f', and the ground truth answer is: {answer}\n\n'
                   + ('' if resume_api else ', ')
                   + 'please check whether the model response is correct or not, '
                   'and return the **only** Yes or No.')
    return [{'role': 'system', 'content': 'You are a math answer checker.'},
            {'role': 'user', 'content': content}]


def normalized_metadata(metadata):
    """Old tagged local results used the corrected v1 prompt before mode existed."""
    if isinstance(metadata, dict) and metadata.get('prompt_version') == 'math-recheck-local-v1':
        return dict(metadata, prompt_mode=metadata.get('prompt_mode', 'corrected'))
    return metadata


def ensure_output_mode(path, mode=None):
    """Never append another mode to an existing results file, including legacy files."""
    path = Path(path)
    mode = prompt_mode(mode)
    if not path.exists():
        return
    for number, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
            metadata = record.get('recheck') or {}
            previous = metadata.get('prompt_mode', 'corrected')
        except (ValueError, AttributeError, TypeError):
            raise ValueError(f'Cannot verify prompt mode in {path}, line {number}; use a new output file') from None
        if previous != mode:
            raise ValueError(f'Prompt mode mismatch in {path}: existing={previous}, requested={mode}; use a new output file')
