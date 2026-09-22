"""python -m methods.novelty_pair_diagnostic.pipeline STAGE --config config.json"""
import argparse
import csv
import fcntl
import json
import os
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from . import backends as b
from .core import (VERSION, LABELS, atomic, calibrate, digest, file_hash, metrics,
                   prepare_rows, read_rows, write_rows)

ROOT = Path(__file__).resolve().parents[2]
SOURCES = ['examples/reward_function/caller_penalty.py',
           'methods/validity_rzero/semantic_judge_offline/run_pair_judge_v2.py',
           'methods/validity_rzero/semantic_judge_offline/run_pair_judge_v3_vllm.py']
DEFAULT = dict(seed=42, pairs_per_round=200, calibration_fraction=.2, expected_questions=2000,
               source_kind='solver_training_sample_before_answer_verification',
               base=dict(model='Qwen/Qwen3-4B-Base', revision=None),
               api=dict(model='gpt-5.6-sol', effort='high', max_output_tokens=16384, concurrency=8),
               embedding=dict(batch_size=8, max_length=8192, dtype='bfloat16', device='cuda'),
               judge=dict(batch_size=32, max_model_len=8192, max_tokens=1024, dtype='bfloat16',
                          tensor_parallel_size=1, gpu_memory_utilization=.85, seed=42),
               min_calibration_positives=5)


def configuration(path):
    supplied = json.loads(Path(path).read_text())
    unknown = set(supplied) - set(DEFAULT) - {'input', 'output', 'source_manifest'}
    if unknown:
        raise ValueError(f'unknown settings {unknown}')
    config = {**DEFAULT, **supplied}
    for k in ('base', 'api', 'embedding', 'judge'):
        if set(supplied.get(k, {})) - set(DEFAULT[k]):
            raise ValueError(f'unknown {k} setting')
        config[k] = {**DEFAULT[k], **supplied.get(k, {})}
    for key in ('input', 'output', 'source_manifest'):
        if config.get(key):
            config[key] = str(Path(os.path.expandvars(config[key])).expanduser().resolve())
            if '$' in config[key]:
                raise ValueError(f'unset environment variable in {key}')
    if Path(config['output']) == Path(config['input']) or Path(config['output']) in Path(config['input']).parents:
        raise ValueError('input must be outside output directory')
    for block, keys in [('api', ['concurrency', 'max_output_tokens']),
                        ('embedding', ['batch_size', 'max_length']),
                        ('judge', ['batch_size', 'max_model_len', 'max_tokens', 'tensor_parallel_size'])]:
        if any(config[block][k] < 1 for k in keys):
            raise ValueError(f'invalid {block} settings')
    if config['expected_questions'] < 1 or config['min_calibration_positives'] < 1:
        raise ValueError('invalid count')
    if config['judge']['max_tokens'] >= config['judge']['max_model_len']:
        raise ValueError('judge must leave room for the prompt')
    return config


def bind(path, value):
    if path.exists() and json.loads(path.read_text()) != value:
        raise ValueError(f'configuration/data/code changed at {path}; use a new output directory')
    atomic(path, value)


class Cache:
    """One atomic artifact per identity; retry history remains inspectable."""
    def __init__(self, directory, context, inputs):
        self.directory, self.context, self.inputs = directory, digest(context), inputs
        bind(directory / 'manifest.json', context)

    def path(self, key):
        return self.directory / 'artifacts' / (digest(key) + '.json')

    def get(self, key):
        path = self.path(key)
        if not path.exists():
            return None
        a = json.loads(path.read_text())
        if a.get('context') != self.context or a.get('input_hash') != digest(self.inputs[key]) or a.get('id') != key:
            raise ValueError(f'cached identity mismatch: {path}')
        value = a.pop('checksum')
        if value != digest(a):
            raise ValueError(f'cached content mismatch: {path}')
        return a

    def put(self, key, result):
        old = self.get(key)
        history = [] if old is None else old.get('history', []) + [
            {k: v for k, v in old.items() if k != 'history'}]
        a = dict(result, id=key, context=self.context, input_hash=digest(self.inputs[key]), history=history)
        atomic(self.path(key), dict(a, checksum=digest(a)))


def code_hashes():
    files = [*Path(__file__).parent.glob('*.py'), Path(__file__).with_name('source_provenance.json'), *(ROOT / p for p in SOURCES)]
    return {str(p.relative_to(ROOT)): file_hash(p) for p in files}


def prepare(config, out):
    source_hash = file_hash(config['input'])
    source = dict(path=config['input'], sha256=source_hash, kind=config['source_kind'])
    if config.get('source_manifest'):
        source['upstream_manifest'] = json.loads(Path(config['source_manifest']).read_text())
    rows = read_rows(config['input'])
    known = json.loads(Path(__file__).with_name('source_provenance.json').read_text())
    identity = sorted([{'id': r['id'], 'round': r['round'], 'question': r['question']}
                       for r in rows if r.get('split') == 'train'], key=lambda r: r['id'])
    if digest(identity) == known['train_identity_sha256']:
        source['verified_original_provenance'] = known
    questions, pairs, stats = prepare_rows(rows, source, config['seed'],
                                           config['pairs_per_round'], config['calibration_fraction'],
                                           config['expected_questions'])
    manifest = dict(protocol=VERSION, config=config, code_hashes=code_hashes(), source=source,
                    stats=stats, questions_hash=digest(questions), pairs_hash=digest(pairs),
                    orientation='ascending original record ID; a=hypothesis, b=reference',
                    calibration_objective='max F1; ties choose higher threshold; no test labels')
    bind(out / 'manifest.json', manifest)
    write_rows(out / 'questions.jsonl', questions)
    write_rows(out / 'pairs.jsonl', pairs)
    print(json.dumps({k: v for k, v in stats.items() if k != 'component_sizes'}, indent=2))


def load_run(config, out):
    m = json.loads((out / 'manifest.json').read_text())
    if m['config'] != config or m['code_hashes'] != code_hashes() or m['source']['sha256'] != file_hash(config['input']):
        raise ValueError('run config/code/input changed; use a new output directory')
    if config.get('source_manifest') and m['source']['upstream_manifest'] != json.loads(Path(config['source_manifest']).read_text()):
        raise ValueError('upstream manifest changed')
    qs, ps = read_rows(out / 'questions.jsonl'), read_rows(out / 'pairs.jsonl')
    if digest(qs) != m['questions_hash'] or digest(ps) != m['pairs_hash']:
        raise ValueError('prepared data modified')
    return m, qs, ps


def stage_cache(out, stage, manifest, inputs, extra=None, create=True):
    path = out / stage / 'manifest.json'
    if not create and not path.exists():
        return None
    context = dict(run_hash=digest(manifest), stage=stage)
    if create:
        context.update(extra or {})
    else:
        saved = json.loads(path.read_text())
        if saved.get('run_hash') != context['run_hash'] or saved.get('stage') != stage:
            raise ValueError(f'{stage}: mismatched run')
        context = saved
    return Cache(out / stage, context, inputs)


def model_identity(config, out):
    identity = b.resolve_model(config['base'])
    bind(out / 'base_identity.json', identity)
    return identity


def read_method(out, stage, manifest, inputs):
    cache = stage_cache(out, stage, manifest, inputs, create=False)
    return {key: cache.get(key) if cache else None for key in inputs}


def complete_label(a):
    return bool(a and a.get('status') == 'complete' and a.get('label') in LABELS)


def complete_score(a):
    import math
    return bool(a and a.get('status') == 'complete' and isinstance(a.get('score'), (int, float))
                and math.isfinite(a['score']))


def calibration_data(out, manifest, pairs):
    # Deliberately construct the subset BEFORE opening reference artifacts.
    inputs = {p['pair_id']: p for p in pairs if p['split'] == 'calibration'}
    labels = read_method(out, 'reference', manifest, inputs)
    data = {}
    for method in ('bleu', 'embedding'):
        scores = read_method(out, method, manifest, inputs)
        if any(not complete_label(labels[k]) or not complete_score(scores[k]) for k in inputs):
            raise ValueError('calibration incomplete/uncertain; inspect review export and retry; no thresholds fitted')
        data[method] = [dict(pair_id=k, split='calibration', label=labels[k]['label'], score=scores[k]['score']) for k in inputs]
    return data


def fit(out, manifest, pairs, config):
    data = calibration_data(out, manifest, pairs)
    results = {name: calibrate(rows) for name, rows in data.items()}
    if min(r['positives'] for r in results.values()) < config['min_calibration_positives']:
        raise ValueError('too few calibration SAME_TYPE pairs; no threshold fitted; report insufficiency without using test labels')
    value = dict(run_hash=digest(manifest), calibration_hash=digest(data), methods=results)
    # Immutable once fitted. Any revised reference requires a separate run/output.
    value['checksum'] = digest(value)
    bind(out / 'thresholds.json', value)
    print(json.dumps(value, indent=2))


def report(out, manifest, pairs):
    inputs = {p['pair_id']: p for p in pairs}
    labels = read_method(out, 'reference', manifest, inputs)
    predictions = {name: read_method(out, name, manifest, inputs) for name in ('bleu', 'embedding', 'judge')}
    threshold_path = out / 'thresholds.json'
    thresholds = None
    if threshold_path.exists():
        thresholds = json.loads(threshold_path.read_text())
        checksum = thresholds.pop('checksum')
        if checksum != digest(thresholds):
            raise ValueError('threshold file changed')
        if thresholds['run_hash'] != digest(manifest) or thresholds['calibration_hash'] != digest(calibration_data(out, manifest, pairs)):
            raise ValueError('threshold provenance no longer matches calibration')
    test = [p for p in pairs if p['split'] == 'test']
    output = dict(protocol=VERSION, threshold_status='fitted' if thresholds else 'not_fitted',
                  warnings=[], results={})
    for rnd in ['overall', *sorted({p['round'] for p in test})]:
        selected = [p for p in test if rnd == 'overall' or p['round'] == rnd]
        valid = [p for p in selected if complete_label(labels[p['pair_id']])]
        positives = sum(labels[p['pair_id']]['label'] == 'SAME_TYPE' for p in valid)
        if positives < 20:
            output['warnings'].append(f'{rnd}: only {positives} labeled test positives; rates may be unstable/undefined')
        output['results'][rnd] = {}
        for method, artifacts in predictions.items():
            truth, preds = [], []
            failures = Counter()
            for p in selected:
                k = p['pair_id']
                if not complete_label(labels[k]):
                    failures['reference_missing_uncertain_or_failed'] += 1
                    continue
                a = artifacts[k]
                if method == 'judge':
                    pred = a['label'] if complete_label(a) else None
                else:
                    pred = ('SAME_TYPE' if a['score'] >= thresholds['methods'][method]['threshold'] else 'DIFFERENT') if thresholds and complete_score(a) else None
                if pred is None:
                    failures['method_missing_failed_or_uncalibrated'] += 1
                    continue
                truth.append(labels[k]['label'])
                preds.append(pred)
            output['results'][rnd][method] = dict(metrics(truth, preds), planned_n=len(selected),
                                                   labeled_n=len(valid), excluded_reasons=dict(failures),
                                                   status='complete' if len(truth) == len(selected) else 'INCOMPLETE_subset_only')
    output['status'] = 'complete' if all(v['status'] == 'complete' for v in output['results']['overall'].values()) else 'INCOMPLETE'
    atomic(out / 'report.json', output)
    lines = ['# Novelty pair diagnostic', '', f"Status: **{output['status']}**. SAME_TYPE is positive.",
             'Incomplete rows describe observed subsets only, not the full test set.', '',
             '| Round | Method | Status | n/planned | TP FP TN FN | FNR | FPR | Precision | Recall | F1 |',
             '|---|---|---|---|---|---|---|---|---|---|']
    def fmt(value):
        return 'NA' if value is None else f'{value:.4f}'
    for rnd, methods in output['results'].items():
        for name, v in methods.items():
            cells = [rnd, name, v['status'], f"{v['n']}/{v['planned_n']}",
                     ' '.join(str(v['confusion'][k]) for k in ('TP', 'FP', 'TN', 'FN')),
                     *(fmt(v[k]) for k in ('false_negative_rate', 'false_positive_rate', 'precision', 'recall', 'f1'))]
            lines.append('| ' + ' | '.join(cells) + ' |')
    lines += ['', *output['warnings'], '', 'See report.json for reference coverage and method failure counts.']
    (out / 'report.md').write_text('\n'.join(lines) + '\n')
    print(output['status'], out / 'report.md')


def export_review(out, manifest, pairs):
    inputs = {p['pair_id']: p for p in pairs}
    labels = read_method(out, 'reference', manifest, inputs)
    rows = []
    for p in pairs:
        a = labels[p['pair_id']] or {}
        rows.append({**p, 'reference_status': a.get('status', 'missing'),
                     'reference_label': a.get('label'), 'shared_setup': a.get('shared_setup'),
                     'task_comparison': a.get('task_comparison'), 'reason': a.get('reason'),
                     'human_label': '', 'human_reason': ''})
    write_rows(out / 'review.jsonl', rows)
    # Blind review export contains NO method predictions/scores or historical validity.
    fields = ['pair_id', 'round', 'split', 'a', 'b', 'question_a', 'question_b',
              'reference_status', 'reference_label', 'shared_setup', 'task_comparison', 'reason',
              'human_label', 'human_reason']
    with (out / 'review.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['prepare', 'reference', 'review-export', 'bleu', 'embedding', 'judge', 'calibrate', 'report'])
    parser.add_argument('--config', required=True)
    parser.add_argument('--retry-failed', action='store_true', help='retry non-complete reference/judge items, retain attempt history')
    args = parser.parse_args()
    config = configuration(args.config)
    out = Path(config['output'])
    out.mkdir(parents=True, exist_ok=True)
    with (out / '.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if args.stage == 'prepare':
            prepare(config, out)
            return
        manifest, questions, pairs = load_run(config, out)
        inputs = {p['pair_id']: p for p in pairs}
        stage = args.stage
        if stage == 'reference':
            cache = stage_cache(out, stage, manifest, inputs, dict(api=config['api'],
                                 prompt=b.API_PROMPT, schema=b.API_SCHEMA, runtime=b.versions(['openai'])))
            pending = [p for p in pairs if cache.get(p['pair_id']) is None or
                       (args.retry_failed and cache.get(p['pair_id'])['status'] != 'complete')]
            if pending:
                from openai import OpenAI
                client = OpenAI(max_retries=2)
                def execute(p):
                    try:
                        result = b.reference_call(client, p, config['api'])
                    except Exception as error:
                        result = dict(status='request_error', label=None, error_type=type(error).__name__, error=str(error))
                    # Disk/cache errors must propagate, never masquerade as failed API requests.
                    cache.put(p['pair_id'], result)
                    return result['status']
                with ThreadPoolExecutor(max_workers=config['api']['concurrency']) as pool:
                    futures = [pool.submit(execute, p) for p in pending]
                    for i, future in enumerate(as_completed(futures), 1):
                        print(f'reference {i}/{len(pending)}: {future.result()}', flush=True)
            export_review(out, manifest, pairs)
        elif stage == 'bleu':
            cache = stage_cache(out, stage, manifest, inputs, dict(runtime=b.versions(['nltk'])))
            for p in pairs:
                if cache.get(p['pair_id']) is None:
                    cache.put(p['pair_id'], dict(status='complete', score=b.bleu(p['question_a'], p['question_b'])))
        elif stage in ('embedding', 'judge'):
            identity = model_identity(config, out)
            extra = dict(model=identity, settings=config[stage], runtime=b.versions(['torch', 'transformers', 'vllm']))
            cache = stage_cache(out, stage, manifest, inputs, extra)
            if stage == 'embedding':
                used = {p[k] for p in pairs for k in ('a', 'b')}
                qs = [q for q in questions if q['id'] in used]
                vectors = stage_cache(out, 'vectors', manifest, {q['id']: q for q in qs}, extra)
                for key, value in b.embedding_run(qs, pairs, vectors, identity, config[stage]).items():
                    if cache.get(key) is None:
                        cache.put(key, value)
            else:
                b.judge_run(pairs, cache, identity, config[stage], args.retry_failed)
        elif stage == 'review-export':
            export_review(out, manifest, pairs)
        elif stage == 'calibrate':
            fit(out, manifest, pairs, config)
        elif stage == 'report':
            report(out, manifest, pairs)


if __name__ == '__main__':
    main()
