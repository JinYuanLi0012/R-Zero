"""CPU-only MAP, SAM clustering, and original R-Zero data semantics."""
from collections import Counter
import json
import math
from pathlib import Path
import random
import re

import numpy as np


def read_json(path):
    return json.loads(Path(path).read_text())


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    tmp.replace(path)


def parse_question(text):
    """Last question block + last balanced box (no validity/novelty gate)."""
    questions = re.findall(r'<question>(.*?)</question>', text, re.S)
    boxes = []
    pos = 0
    while True:
        start = text.find(r'\boxed{', pos)
        if start < 0:
            break
        begin = start + len(r'\boxed{')
        depth, end = 1, begin
        while end < len(text) and depth:
            depth += (text[end] == '{') - (text[end] == '}')
            end += 1
        if depth == 0:
            boxes.append(text[begin:end - 1].strip())
        pos = end
    if questions and boxes and questions[-1].strip() and boxes[-1]:
        return {'question': questions[-1].strip(), 'answer': boxes[-1], 'score': 0.0}
    return {'question': '', 'answer': '', 'score': -1.0}


def normalize(vectors):
    vectors = np.asarray(vectors, dtype=np.float32)
    if vectors.ndim != 2 or not np.isfinite(vectors).all():
        raise ValueError('Embedding matrix must be finite and two-dimensional')
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    if (norms <= 0).any():
        raise ValueError('Zero embedding is not a valid SAM representation')
    return vectors / norms


def batch_penalties(vectors, threshold=0.5):
    """Original average-linkage cluster share; cosine replaces BLEU distance."""
    from sklearn.cluster import AgglomerativeClustering
    x = normalize(vectors)
    if len(x) <= 1:
        return np.ones(len(x), dtype=np.float32)
    distances = np.clip(1 - x @ x.T, 0, 2)
    np.fill_diagonal(distances, 0)
    labels = AgglomerativeClustering(
        n_clusters=None, metric='precomputed', linkage='average',
        distance_threshold=threshold,
    ).fit_predict(distances)
    counts = Counter(labels)
    return np.asarray([counts[label] / len(x) for label in labels])


def memory_penalties(vectors, memory, gamma=0.5, tau_max=0.5, tau_mean=0.25):
    x = normalize(vectors)
    if len(memory) == 0:
        zeros = np.zeros(len(x), dtype=np.float32)
        return zeros, zeros.copy(), zeros.copy()
    history = normalize(memory)
    # Do NOT normalize the mean: that would change equation (8).
    mean_sim = np.clip(x @ history.mean(axis=0), -1, 1)
    maximum = np.full(len(x), -np.inf, dtype=np.float32)
    for begin in range(0, len(history), 4096):
        maximum = np.maximum(maximum, (x @ history[begin:begin + 4096].T).max(axis=1))
    maximum = np.clip(maximum, -1, 1)
    penalty = gamma * np.maximum(maximum - tau_max, 0)
    penalty += (1 - gamma) * np.maximum(mean_sim - tau_mean, 0)
    return penalty, maximum, mean_sim


def retained(row):
    """Upstream Phase-B exclusions, then paper's inclusive [0.3, 0.8]."""
    q, answer = row.get('question', ''), row.get('answer', '')
    return bool(q and answer and answer != 'None'
                and 0.3 <= row.get('score', -1) <= 0.8
                and '证明' not in q and 'box' not in q.lower()
                and 'text' not in answer.lower())


def replay_rows(current, history, ratio=0.3, seed=1):
    if not 0 <= ratio < 1:
        raise ValueError('Replay ratio must be in [0, 1)')
    rng = random.Random(seed)
    count = math.floor(len(current) * ratio / (1 - ratio)) if history else 0
    # Unspecified in paper: uniform rows, without replacement unless exhausted.
    replay = (rng.sample(history, count) if count <= len(history)
              else rng.choices(history, k=count))
    mixed = [dict(row, replay=False) for row in current]
    mixed += [dict(row, replay=True) for row in replay]
    rng.shuffle(mixed)
    return mixed
