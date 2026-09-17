"""Inspect corrected SAM on saved questions; no training, reward, or history updates."""
import argparse
from collections import Counter
from pathlib import Path
import tempfile

import numpy as np

from methods.r_diverse.core import read_json, write_json
from methods.r_diverse.inference import sam, sam_success_indices
from methods.r_diverse.run import clean_environment
from methods.r_diverse.sam_protocol import CODE_PROTOCOL


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reward-dir', type=Path, required=True)
    parser.add_argument('--gpu-ids', default='2,3')
    parser.add_argument('--limit', type=int, default=8)
    parser.add_argument('--coder-prompt-mode', choices=['completion', 'chat'], default='completion')
    args = parser.parse_args()
    gpus = args.gpu_ids.split(',')
    if args.limit < 2 or len(set(gpus)) != len(gpus) or any(not g.isdigit() for g in gpus):
        parser.error('Use at least two questions and distinct numeric GPU indices')
    config = read_json(args.reward_dir / 'code_0.input.json')['config']
    rows = read_json(args.reward_dir / 'questions.json')
    questions = list(dict.fromkeys(row['question'] for row in rows))[:args.limit]
    if len(questions) < 2:
        parser.error('Saved reward batch must contain at least two distinct questions')
    # A fresh directory/cache leaves the old run and its memory untouched.
    directory = Path(tempfile.mkdtemp(prefix='sam_inspect_v2_', dir=args.reward_dir.parent))
    config.update(run_root=str(directory.resolve()), coder_prompt_mode=args.coder_prompt_mode)
    clean_environment()
    write_json(directory / 'config.json', config)
    print(f'SAM artifacts: {directory}', flush=True)
    vectors, records = sam(questions, config, gpus, directory)
    keep = sam_success_indices(records)
    counts = Counter(records[i]['code'] for i in keep)
    summary = {'code_protocol': CODE_PROTOCOL, 'questions': len(questions),
               'unique_code': len(counts), 'most_common_code_count': max(counts.values()),
               'syntax_ok': sum(r['code_syntax_ok'] for r in records),
               'sam_failed': len(records) - len(keep), 'cosine_original_indices': keep,
               'cosine_matrix': (vectors @ vectors.T).tolist()}
    write_json(directory / 'summary.json', summary)
    for i, row in enumerate(records):
        print(f'\n[{i}] {row["question"]}\n{row.get("sam_error") or row["code"]}', flush=True)
    print(f'\nCosines (successful original indices {keep}):\n', np.round(vectors @ vectors.T, 3), flush=True)
    print(f'Unique code: {len(counts)}/{len(questions)}; syntax OK: {summary["syntax_ok"]}; '
          f'review question/code correspondence in {directory}', flush=True)


if __name__ == '__main__':
    main()
