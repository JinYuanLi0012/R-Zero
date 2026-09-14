"""R-Diverse equation (11), on original R-Zero majority/frontier rewards."""
from pathlib import Path
import tempfile

import numpy as np

from methods.r_diverse.core import (batch_penalties, memory_penalties, parse_question,
                                    read_json, write_json)
from methods.r_diverse.inference import run_workers, sam


def compute_score(predicts, ground_truths, config_path, solver_model, memory_path, round_dir):
    del ground_truths
    config = read_json(config_path)
    work = Path(tempfile.mkdtemp(prefix='reward_', dir=round_dir))
    parsed = [parse_question(text) for text in predicts]
    indices = [i for i, row in enumerate(parsed) if row['question']]
    scores = [{'overall': -1.0, 'format': 0.0, 'accuracy': 0.0,
               'frontier': 0.0, 'batch_penalty': 0.0, 'map_penalty': 0.0,
               'history_max': 0.0, 'history_mean': 0.0} for _ in parsed]
    if indices:
        rows = [parsed[i] for i in indices]
        evaluated = run_workers('solve', rows, solver_model, config['feedback_gpus'],
                                config, work, phase='reward', seed=config['seed'])
        embeddings, records = sam([r['question'] for r in rows], config, config['feedback_gpus'], work)
        history = np.load(memory_path, allow_pickle=False)
        local = batch_penalties(embeddings)
        global_penalty, maximum, mean = memory_penalties(embeddings, history)
        for j, index in enumerate(indices):
            support = evaluated[j]['score']
            frontier = min(support, 1 - support)
            scores[index] = {
                'overall': float(frontier - local[j] - global_penalty[j]),
                'format': 1.0, 'accuracy': float(local[j]), 'frontier': frontier,
                'batch_penalty': float(local[j]), 'map_penalty': float(global_penalty[j]),
                'history_max': float(maximum[j]), 'history_mean': float(mean[j]),
            }
        write_json(work / 'questions.json', [dict(evaluated[j], original_index=index,
                   reward=scores[index], sam_key=records[j]['key']) for j, index in enumerate(indices)])
    write_json(work / 'scores.json', scores)
    print('[r_diverse] reward artifacts:', work, flush=True)
    return scores
