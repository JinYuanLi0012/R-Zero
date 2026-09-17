"""R-Diverse equation (11), on original R-Zero majority/frontier rewards."""
from pathlib import Path
import tempfile

import numpy as np

from methods.r_diverse.core import (batch_penalties, memory_penalties, parse_question,
                                    read_json, write_json)
from methods.r_diverse.inference import run_workers, sam, sam_success_indices


def compute_score(predicts, ground_truths, config_path, solver_model, memory_path, round_dir):
    del ground_truths
    config = read_json(config_path)
    work = Path(tempfile.mkdtemp(prefix='reward_', dir=round_dir))
    parsed = [parse_question(text) for text in predicts]
    indices = [i for i, row in enumerate(parsed) if row['question']]
    # Paper does not specify malformed-output rewards. With its fixed coefficients,
    # parseable rewards are >= -1 - (0.5 * 0.5 + 0.5 * 0.75) = -1.625.
    # Keep this fallback strictly lower; leave equation (11) unchanged below.
    scores = [{'overall': -2.0, 'format': 0.0, 'accuracy': 0.0,
               'frontier': 0.0, 'batch_penalty': 0.0, 'map_penalty': 0.0,
               'history_max': 0.0, 'history_mean': 0.0, 'sam_failed': 0.0} for _ in parsed]
    if indices:
        rows = [parsed[i] for i in indices]
        evaluated = run_workers('solve', rows, solver_model, config['feedback_gpus'],
                                config, work, phase='reward', seed=config['seed'])
        embeddings, records = sam([r['question'] for r in rows], config, config['feedback_gpus'], work)
        history = np.load(memory_path, allow_pickle=False)
        local = batch_penalties(embeddings)
        global_penalty, maximum, mean = memory_penalties(embeddings, history)
        positions = {row_index: position for position, row_index in enumerate(sam_success_indices(records))}
        for j, index in enumerate(indices):
            support = evaluated[j]['score']
            frontier = min(support, 1 - support)
            if j not in positions:
                # Unknown SAM is not novel: use the upper bounds of the fixed paper penalties.
                # Keep format=1: this is encoder failure, not a malformed Q response.
                fallback_map = 0.625 if len(history) else 0.0
                scores[index] = dict(overall=float(frontier - 1.0 - fallback_map),
                                     format=1.0, accuracy=1.0, frontier=frontier,
                                     batch_penalty=1.0, map_penalty=fallback_map,
                                     history_max=0.0, history_mean=0.0, sam_failed=1.0)
                continue
            k = positions[j]
            scores[index] = {
                'overall': float(frontier - local[k] - global_penalty[k]),
                'format': 1.0, 'accuracy': float(local[k]), 'frontier': frontier,
                'batch_penalty': float(local[k]), 'map_penalty': float(global_penalty[k]),
                'history_max': float(maximum[k]), 'history_mean': float(mean[k]), 'sam_failed': 0.0,
            }
        write_json(work / 'questions.json', [dict(evaluated[j], original_index=index,
                   reward=scores[index], sam_key=records[j]['key']) for j, index in enumerate(indices)])
    write_json(work / 'scores.json', scores)
    print('[r_diverse] reward artifacts:', work, flush=True)
    return scores
