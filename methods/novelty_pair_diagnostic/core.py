"""Deterministic, label-blind sampling and diagnostic statistics (stdlib only)."""
import gzip
import hashlib
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path

LABELS = ('SAME_TYPE', 'DIFFERENT')
VERSION = 'novelty-pair-v1'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     allow_nan=False).encode()).hexdigest()


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def read_rows(path):
    opener = gzip.open if str(path).endswith('.gz') else open
    with opener(path, 'rt', encoding='utf-8') as f:
        return [json.loads(line) for line in f if line.strip()]


def atomic(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True,
                               allow_nan=False) + '\n', encoding='utf-8')
    temp.replace(path)


def write_rows(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(''.join(json.dumps(r, ensure_ascii=False, allow_nan=False) + '\n'
                            for r in rows), encoding='utf-8')
    temp.replace(path)


def normalize(text):
    return ' '.join(text.split())


def prepare_rows(rows, source, seed=42, per_round=200, fraction=.2, expected=2000):
    if per_round < 1 or not 0 < fraction < 1:
        raise ValueError('invalid sampling settings')
    selected = [r for r in rows if r.get('split') == 'train']
    if len(selected) != expected:
        raise ValueError(f'expected {expected} original train questions, got {len(selected)}')
    questions, ids = [], set()
    for row in selected:
        key, text, rnd = row['id'], row['question'], row['round']
        if not isinstance(key, str) or not key or key in ids:
            raise ValueError('empty or duplicate original ID')
        if not isinstance(text, str) or not normalize(text) or rnd not in {f'v{i}' for i in range(1, 6)}:
            raise ValueError('invalid question/round')
        ids.add(key)
        questions.append(dict(id=key, question=text, round=rnd, source=source,
                              source_split='train', source_row_index=row.get('source_row_index'),
                              text_group=digest(normalize(text))))
    by_round = defaultdict(list)
    for q in sorted(questions, key=lambda q: q['id']):
        by_round[q['round']].append(q)
    if len(by_round) != 5:
        raise ValueError('requires all five rounds')
    pairs = []
    for rnd, qs in sorted(by_round.items()):
        # Uniform sample of unordered record pairs, before any split or labeling.
        n = len(qs)
        if n * (n - 1) // 2 < per_round:
            raise ValueError(f'{rnd}: insufficient pairs from {n} questions')
        rng = random.Random(int(digest([seed, rnd])[:16], 16))
        ranks = set(rng.sample(range(n * (n - 1) // 2), per_round))
        rank = 0
        for i in range(n):
            for j in range(i + 1, n):
                if rank in ranks:
                    a, b = qs[i], qs[j]
                    pairs.append(dict(pair_id=digest([rnd, a['id'], b['id']])[:24],
                                      round=rnd, a=a['id'], b=b['id'],
                                      question_a=a['question'], question_b=b['question'],
                                      seed=seed, source=source))
                rank += 1
    # Union identical text globally and every sampled edge. Components cannot leak.
    parent = {q['id']: q['id'] for q in questions}
    def root(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def union(a, b):
        a, b = root(a), root(b)
        parent[max(a, b)] = min(a, b)
    texts = {}
    for q in questions:
        if q['text_group'] in texts:
            union(q['id'], texts[q['text_group']])
        texts[q['text_group']] = q['id']
    for p in pairs:
        union(p['a'], p['b'])
    components = defaultdict(list)
    for p in pairs:
        components[root(p['a'])].append(p)
    keys = sorted(components)
    random.Random(seed).shuffle(keys)
    target, count = round(len(pairs) * fraction), 0
    for key in keys:
        group = components[key]
        use_cal = abs(count + len(group) - target) < abs(count - target)
        if use_cal:
            count += len(group)
        for p in group:
            p.update(split='calibration' if use_cal else 'test', component=key)
    if not 0 < count < len(pairs):
        raise ValueError('components prevent a nonempty leakage-free split; choose a new protocol/output')
    stats = dict(question_count=len(questions), questions_by_round=dict(Counter(q['round'] for q in questions)),
                 pairs_by_round=dict(Counter(p['round'] for p in pairs)),
                 pairs_by_split=dict(Counter(p['split'] for p in pairs)),
                 round_split_counts=dict(Counter(p['round'] + '/' + p['split'] for p in pairs)),
                 component_sizes=sorted(map(len, components.values()), reverse=True),
                 duplicate_text_records_retained=len(questions) - len(texts),
                 split_rule='uniform pairs first; global normalized-text and pair-edge components; seeded greedy target')
    return questions, pairs, stats


def metrics(truth, prediction):
    if len(truth) != len(prediction) or any(x not in LABELS for x in truth + prediction):
        raise ValueError('metrics require aligned binary labels; failures are not negatives')
    tp = sum(t == p == 'SAME_TYPE' for t, p in zip(truth, prediction))
    tn = sum(t == p == 'DIFFERENT' for t, p in zip(truth, prediction))
    fp = sum(t == 'DIFFERENT' and p == 'SAME_TYPE' for t, p in zip(truth, prediction))
    fn = len(truth) - tp - tn - fp
    div = lambda a, b: a / b if b else None
    return dict(n=len(truth), positives=tp + fn, negatives=tn + fp,
                confusion=dict(TP=tp, FP=fp, TN=tn, FN=fn),
                false_negative_rate=div(fn, tp + fn), false_positive_rate=div(fp, tn + fp),
                precision=div(tp, tp + fp), recall=div(tp, tp + fn),
                f1=div(2 * tp, 2 * tp + fp + fn))


def calibrate(rows):
    if not rows or any(r['split'] != 'calibration' for r in rows):
        raise ValueError('calibration must contain only calibration pairs')
    if set(r['label'] for r in rows) != set(LABELS):
        raise ValueError('calibration requires both classes; no threshold fitted')
    scores = [r['score'] for r in rows]
    if any(not math.isfinite(s) for s in scores):
        raise ValueError('nonfinite score')
    candidates = sorted(set(scores)) + [math.nextafter(max(scores), math.inf)]
    def quality(t):
        m = metrics([r['label'] for r in rows],
                    ['SAME_TYPE' if r['score'] >= t else 'DIFFERENT' for r in rows])
        return m['f1'] or 0, t  # conservative higher threshold breaks ties
    threshold = max(candidates, key=quality)
    return dict(threshold=threshold, objective='maximum calibration F1; higher threshold ties',
                n=len(rows), positives=sum(r['label'] == 'SAME_TYPE' for r in rows))
