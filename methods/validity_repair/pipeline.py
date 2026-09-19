#!/usr/bin/env python3
"""Stage 1 only: concurrent or Batch repair, independent review, paired question-only exports."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter
from pathlib import Path

# Reuse the established Terra IO/Batch transport without changing its pipelines.
TERRA_DIR = Path(__file__).resolve().parents[1] / 'validity_rl_terra_dataset'
sys.path.insert(0, str(TERRA_DIR))
from common import atomic_json, read_jsonl, write_jsonl
from batch_annotate import download_file, extract_output_text, load_state, submit_record, wait_for_batch, utc_now
from protocol import VERSION, SETTINGS, accepted, apply_edits, validate


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def prepare(input_path, output_dir, limit, seed, expected_count):
    source = read_jsonl(input_path)
    if len(source) != expected_count:
        raise ValueError(f'expected {expected_count} train rows, got {len(source)}')
    rows = []
    for r in source:
        if (not isinstance(r.get('id'), str) or not re.fullmatch(r'[A-Za-z0-9_-]+', r['id'])
                or not isinstance(r.get('question'), str) or not r['question'].strip()
                or r.get('terra_validity') not in ('VALID', 'INVALID') or r.get('split') != 'train'
                or r.get('round') not in ('v1', 'v2', 'v3', 'v4', 'v5')):
            raise ValueError('invalid input row: requires safe ID, question, train split, round, validity')
        rows.append({k: r[k] for k in ('id', 'question', 'round', 'split', 'terra_validity')})
    if len({r['id'] for r in rows}) != len(rows) or len({r['question'] for r in rows}) != len(rows):
        raise ValueError('duplicate ID or question')
    counts = dict(Counter(r['terra_validity'] for r in rows))
    if expected_count == 1993 and counts != {'VALID': 852, 'INVALID': 1141}:
        raise ValueError(f'expected 852 VALID / 1141 INVALID, got {counts}')
    candidates = [r for r in rows if r['terra_validity'] == 'INVALID']
    random.Random(seed).shuffle(candidates)
    selected = candidates[:limit] if limit else candidates
    selected_ids = {r['id'] for r in selected}
    items = [{'id': r['id'], 'question': r['question']} for r in rows if r['id'] in selected_ids]
    config = {'protocol': VERSION, 'source_sha256': digest(rows), 'source_counts': counts,
              'source_count': len(rows), 'repair_limit': limit, 'seed': seed,
              'selected_ids': [r['id'] for r in items]}
    path = output_dir / 'prepare_manifest.json'
    if path.exists() and json.loads(path.read_text()) != config:
        raise ValueError('input/selection changed; use a new OUTPUT_DIR')
    atomic_json(path, config)
    write_jsonl(output_dir / 'source_questions.jsonl', rows)
    write_jsonl(output_dir / 'repair_input.jsonl', items)
    return rows, items, config


def request(item, stage, model, effort, max_tokens):
    prompt, schema = SETTINGS[stage]
    return {'custom_id': f'{stage}:{item["id"]}:a1', 'method': 'POST', 'url': '/v1/responses',
            'body': {'model': model,
                     'input': [{'role': 'system', 'content': prompt},
                               {'role': 'user', 'content': json.dumps(item, ensure_ascii=False)}],
                     'reasoning': {'effort': effort}, 'max_output_tokens': max_tokens,
                     'text': {'format': {'type': 'json_schema', 'name': f'rzero_{stage}',
                                        'strict': True, 'schema': schema}}}}


def parse_line(line, item, stage):
    response = line.get('response') or {}
    if response.get('status_code') != 200:
        raise ValueError(f'API request failed: {line.get("error") or response.get("status_code")}')
    body = response.get('body') or {}
    if body.get('status') not in (None, 'completed'):
        raise ValueError(f'Responses status: {body.get("status")}')
    result = json.loads(extract_output_text(body))
    validate(result, SETTINGS[stage][1])
    if stage == 'repair':
        apply_edits(item['question'], result)
    return result


def run_stage(client, items, stage, out, model, effort, max_tokens, poll):
    directory = out / 'batch' / stage
    directory.mkdir(parents=True, exist_ok=True)
    config = {'pass': stage, 'protocol': VERSION, 'model': model, 'reasoning_effort': effort,
              'max_output_tokens': max_tokens, 'prompt_schema_hash': digest(SETTINGS[stage]),
              'input_hash': digest(items), 'semantic_attempts': 1}
    state_path = directory / 'state.json'
    state = load_state(state_path, config)
    if not items:
        return {}
    if not state['batches']:
        payload = [request(i, stage, model, effort, max_tokens) for i in items]
        input_path = directory / 'input_01.jsonl'
        write_jsonl(input_path, payload)
        if input_path.stat().st_size > 200 * 1024 * 1024:
            raise ValueError('Batch input exceeds 200 MB')
        state['batches'].append({'sequence': 1, 'input_path': str(input_path),
            'output_path': str(directory / 'output_01.jsonl'),
            'error_path': str(directory / 'errors_01.jsonl'),
            'custom_ids': [r['custom_id'] for r in payload],
            'input_file_id': None, 'batch_id': None, 'processed_at_utc': None})
        atomic_json(state_path, state)
    record = state['batches'][0]
    if not record['processed_at_utc']:
        submit_record(client, record, state, state_path)
        snapshot = wait_for_batch(client, record, state, state_path, poll)
        if snapshot['status'] in ('failed', 'cancelled'):
            raise RuntimeError(f'Batch {record["batch_id"]}: {snapshot["status"]}; {snapshot.get("errors")}')
        download_file(client, snapshot.get('output_file_id'), Path(record['output_path']))
        download_file(client, snapshot.get('error_file_id'), Path(record['error_path']))
        record.update(terminal_status=snapshot['status'], processed_at_utc=utc_now(),
                      output_file_id=snapshot.get('output_file_id'), error_file_id=snapshot.get('error_file_id'))
        atomic_json(state_path, state)
    indexed = {}
    for filename in (record['output_path'], record['error_path']):
        if Path(filename).exists():
            for line in read_jsonl(Path(filename)):
                key = line.get('custom_id')
                if key not in record['custom_ids'] or key in indexed:
                    raise ValueError(f'unknown/duplicate Batch custom_id: {key}')
                indexed[key] = line
    artifacts = {}
    for item in items:
        raw = indexed.get(f'{stage}:{item["id"]}:a1', {})
        artifact = {'id': item['id'], 'stage': stage, 'input_sha256': digest(item), 'raw_batch_result': raw}
        try:
            artifact.update(status='complete', result=parse_line(raw, item, stage))
        except (ValueError, TypeError, KeyError) as error:
            artifact.update(status='failed', result=None, error=str(error))
        atomic_json(out / 'artifacts' / stage / f'{item["id"]}.json', artifact)
        artifacts[item['id']] = artifact
    print(f'[{stage}] {dict(Counter(a["status"] for a in artifacts.values()))}', flush=True)
    return artifacts


def run_sync_stage(client, items, stage, out, model, effort, max_tokens, concurrency):
    """Identical request bodies and parsing, with per-item persistent results."""
    config = {'mode': 'sync', 'pass': stage, 'protocol': VERSION, 'model': model,
              'reasoning_effort': effort, 'max_output_tokens': max_tokens,
              'prompt_schema_hash': digest(SETTINGS[stage]), 'input_hash': digest(items)}
    state_path = out / 'sync' / stage / 'state.json'
    load_state(state_path, config)
    directory = out / 'artifacts' / stage
    directory.mkdir(parents=True, exist_ok=True)
    artifacts, pending = {}, []
    for item in items:
        path = directory / f'{item["id"]}.json'
        if path.exists():
            artifact = json.loads(path.read_text())
            if (artifact.get('input_sha256') != digest(item) or artifact.get('stage') != stage
                    or artifact.get('id') != item['id'] or artifact.get('mode') != 'sync'):
                raise ValueError(f'cached artifact mismatch: {path}')
            artifacts[item['id']] = artifact
        else:
            pending.append(item)

    def execute(item):
        body = request(item, stage, model, effort, max_tokens)['body']
        artifact = {'id': item['id'], 'stage': stage, 'mode': 'sync',
                    'input_sha256': digest(item), 'request_body': body}
        # Only request/API exceptions become failed items; local disk errors stop the run.
        try:
            response = client.responses.create(**body)
            raw = response.model_dump(mode='json')
            artifact['raw_response'] = raw
            line = {'response': {'status_code': 200, 'body': raw}}
            artifact.update(status='complete', result=parse_line(line, item, stage))
        except Exception as error:
            artifact.update(status='failed', result=None, error_type=type(error).__name__, error=str(error))
        atomic_json(directory / f'{item["id"]}.json', artifact)
        return artifact

    print(f'[sync:{stage}] total={len(items)} cached={len(artifacts)} pending={len(pending)} concurrency={concurrency}', flush=True)
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = [pool.submit(execute, item) for item in pending]
        for future in as_completed(futures):
            artifact = future.result()
            artifacts[artifact['id']] = artifact
            counts = dict(Counter(a['status'] for a in artifacts.values()))
            print(f'[sync:{stage}] {len(artifacts)}/{len(items)} {counts}', flush=True)
    return artifacts


def proposals(items, repairs):
    return [{'id': i['id'], 'original_question': i['question'],
             'repaired_question': apply_edits(i['question'], repairs[i['id']]['result'])}
            for i in items if repairs[i['id']]['status'] == 'complete'
            and repairs[i['id']]['result']['decision'] == 'proposed']


def finalize(rows, items, repairs, reviews, out, confidence):
    selected = {i['id'] for i in items}
    original, repaired, audit = [], [], []
    for row in rows:
        key, question = row['id'], row['question']
        candidate, status, review = None, 'unchanged_valid', None
        repair = repairs.get(key)
        if row['terra_validity'] == 'INVALID':
            status = 'not_selected'
            if key in selected:
                status = 'repair_failed'
                if repair and repair['status'] == 'complete':
                    result = repair['result']
                    status = result['decision']
                    if status == 'proposed':
                        candidate = apply_edits(question, result)
                        review = reviews.get(key)
                        status = 'review_failed'
                        if review and review['status'] == 'complete':
                            status = 'accepted' if accepted(review['result'], confidence) else 'review_rejected'
        changed = status == 'accepted'
        base = {'id': key, 'question': question, 'round': row['round'], 'split': 'train'}
        original.append(base)
        repaired.append({**base, 'question': candidate if changed else question})
        audit.append({'id': key, 'round': row['round'], 'source_validity': row['terra_validity'],
                      'status': status, 'original_question': question, 'candidate_question': candidate,
                      'final_question': candidate if changed else question,
                      'repair_result': repair.get('result') if repair else None,
                      'review_result': review.get('result') if review else None})
    counts = Counter(r['status'] for r in audit)
    nvalid = sum(r['terra_validity'] == 'VALID' for r in rows)
    ninvalid = len(rows) - nvalid
    changed = counts['accepted']
    stats = {'total_questions': len(rows), 'source_valid': nvalid, 'source_invalid': ninvalid,
             'selected_invalid': len(items), 'accepted_repairs': changed, 'status_counts': dict(counts),
             'acceptance_rate_among_selected': changed / len(items) if items else 0,
             'original_label_valid_rate': nvalid / len(rows),
             'nominal_repaired_valid_rate': (nvalid + changed) / len(rows),
             'unresolved_original_invalid': ninvalid - changed,
             'repaired_exact_unique_questions': len({r['question'] for r in repaired}),
             'valid_rate_note': 'Nominal: inherited original VALID labels + independently accepted repairs; not a fresh full-dataset audit.',
             'training_labels_generated': False}
    write_jsonl(out / 'original_questions.jsonl', original)
    write_jsonl(out / 'repaired_questions.jsonl', repaired)
    write_jsonl(out / 'repair_audit.jsonl', audit)
    write_jsonl(out / 'accepted_repairs.jsonl', [r for r in audit if r['status'] == 'accepted'])
    write_jsonl(out / 'unresolved.jsonl', [r for r in audit if r['source_validity'] == 'INVALID' and r['status'] != 'accepted'])
    atomic_json(out / 'analysis' / 'statistics.json', stats)
    report = ['# Paired validity repair — stage 1', '',
              f'- Questions in each arm: {len(rows)}', f'- Selected INVALID: {len(items)} / {ninvalid}',
              f'- Accepted repairs: {changed}',
              f'- Nominal validity: {nvalid / len(rows):.2%} → {(nvalid + changed) / len(rows):.2%}',
              '- Rate combines inherited VALID labels with accepted repairs; it is not a fresh global audit.',
              '- Failed, rejected, unrepairable and unselected questions retain their exact original text.',
              '- Question-only exports contain no API answers, Terra reward targets, or solver labels.',
              '', '| Outcome | Count |', '|---|---:|']
    report += [f'| {k} | {v} |' for k, v in sorted(counts.items())]
    report += ['', '## By source round', '', '| Round | Total | Selected | Accepted |', '|---|---:|---:|---:|']
    for rd in sorted({r['round'] for r in rows}):
        subset = [r for r in audit if r['round'] == rd]
        report.append(f'| {rd} | {len(subset)} | {sum(r["id"] in selected for r in subset)} | {sum(r["status"] == "accepted" for r in subset)} |')
    (out / 'analysis' / 'report.md').write_text('\n'.join(report) + '\n', encoding='utf-8')
    return stats


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=Path('analysis_results/validity_rl_terra_dataset_v1/train.jsonl'))
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--repair-limit', type=int, default=0, help='0 = all INVALID; positive = deterministic smoke subset')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--expected-count', type=int, default=1993)
    parser.add_argument('--model', default='gpt-5.6-sol')
    parser.add_argument('--reasoning-effort', default='high', choices=['low', 'medium', 'high'])
    parser.add_argument('--max-output-tokens', type=int, default=16384)
    parser.add_argument('--min-review-confidence', type=float, default=0.8)
    parser.add_argument('--poll-seconds', type=int, default=60)
    parser.add_argument('--annotation-mode', choices=['sync', 'batch'], default='sync')
    parser.add_argument('--concurrency', type=int, default=16)
    parser.add_argument('--prepare-only', action='store_true')
    args = parser.parse_args()
    if args.concurrency < 1 or args.repair_limit < 0 or args.expected_count < 1 or args.poll_seconds < 5 or args.max_output_tokens < 1 or not 0 <= args.min_review_confidence <= 1:
        parser.error('invalid numeric setting')
    out = args.output_dir.resolve()
    # One process owns a run directory; OS releases this lock after interruption.
    import fcntl
    out.mkdir(parents=True, exist_ok=True)
    with (out / '.run.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        rows, items, prepared = prepare(args.input, out, args.repair_limit, args.seed, args.expected_count)
        run_config = {**prepared, 'annotation_mode': args.annotation_mode, 'model': args.model, 'effort': args.reasoning_effort,
                      'max_output_tokens': args.max_output_tokens, 'min_review_confidence': args.min_review_confidence,
                      'prompts_and_schemas': SETTINGS, 'semantic_attempts_per_stage': 1}
        config_path = out / 'manifest.json'
        if config_path.exists():
            cached_config = json.loads(config_path.read_text())
            cached_config.setdefault('annotation_mode', 'batch')  # old release used only Batch
            if cached_config != json.loads(json.dumps(run_config)):
                raise ValueError('run settings changed; use a new OUTPUT_DIR')
        atomic_json(config_path, run_config)
        print(f'[prepare] {len(rows)} questions; {len(items)} INVALID selected; output={out}', flush=True)
        if args.prepare_only:
            print('[prepare] no API requests submitted', flush=True)
            return
        if not os.environ.get('OPENAI_API_KEY'):
            raise RuntimeError('export OPENAI_API_KEY before running live API calls')
        from openai import OpenAI
        client = OpenAI()
        stage_runner = run_sync_stage if args.annotation_mode == 'sync' else run_stage
        scheduling = args.concurrency if args.annotation_mode == 'sync' else args.poll_seconds
        repairs = stage_runner(client, items, 'repair', out, args.model, args.reasoning_effort, args.max_output_tokens, scheduling)
        review_items = proposals(items, repairs)
        write_jsonl(out / 'review_input.jsonl', review_items)
        reviews = stage_runner(client, review_items, 'review', out, args.model, args.reasoning_effort, args.max_output_tokens, scheduling)
        stats = finalize(rows, items, repairs, reviews, out, args.min_review_confidence)
        print(f'[complete] accepted={stats["accepted_repairs"]}; report={out / "analysis/report.md"}', flush=True)


if __name__ == '__main__':
    main()
