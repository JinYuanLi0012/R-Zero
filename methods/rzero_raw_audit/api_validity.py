"""Blind API validity labels joined to every original raw-audit row."""
from __future__ import annotations
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time

# Reuse the historical A-F rubric, schema, consistency checks and API call.
TERRA = Path(__file__).resolve().parents[1] / 'validity_rl_terra_dataset'
sys.path.insert(0, str(TERRA))
from methods.validity_rl_terra_dataset import annotate as legacy
from methods.validity_rl_terra_dataset.common import atomic_json
from .worker import write_rows


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def prepare(source, rounds, per_round):
    text = Path(source).read_text()
    rows = [json.loads(line) for line in text.splitlines() if line.strip()]
    if Counter(row['round'] for row in rows) != Counter({r: per_round for r in rounds}):
        raise ValueError('Input is incomplete or round counts differ; wait for the sampling run to finish')
    ids = [row['id'] for row in rows]
    if any(not isinstance(i, str) or not i for i in ids) or len(set(ids)) != len(ids):
        raise ValueError('Source IDs must be nonempty and unique')
    if any(any(key.startswith('api_') for key in row) for row in rows):
        raise ValueError('Use the original unannotated input')
    mapping, blind = {}, []
    for row in rows:
        question = row.get('question')
        origin = 'question'
        if not isinstance(question, str) or not question.strip():
            # Missing boxed answers do not prevent judging a tagged question.
            # Never expose a full raw completion (potential answer/reasoning).
            tags = re.findall(r'<question>(.*?)</question>', row.get('questioner_raw', ''), re.DOTALL)
            question = tags[-1].strip() if tags else ''
            origin = 'questioner_raw_question_tag'
        key = 'q_' + digest(row['id'])
        mapping[row['id']] = dict(api_id=key, question=question, question_source=origin)
        if question.strip():
            blind.append(dict(id=key, question=question))
    return rows, blind, mapping, digest(text)


def judge_one(item, destination, config, max_attempts):
    identity = dict(id=item['id'], question_sha256=digest(item['question']),
                    configuration_sha256=digest(json.dumps(config, sort_keys=True)))
    artifact = dict(identity, status='failed', result=None, attempts=[])
    if destination.exists():
        artifact = json.loads(destination.read_text())
        if any(artifact.get(k) != v for k, v in identity.items()):
            raise ValueError('Cached API input/configuration mismatch')
        if artifact['status'] == 'complete':
            return artifact
    for attempt in range(max_attempts):
        raw = None
        record = dict(attempt=len(artifact['attempts']) + 1)
        try:
            text, raw = legacy.api_call(config['model'], legacy.VALIDITY_SYSTEM_PROMPT,
                'rzero_question_validity', legacy.VALIDITY_SCHEMA, item,
                config['reasoning_effort'], config['max_output_tokens'])
            if raw.get('status') != 'completed':
                raise ValueError(f"API response did not complete: {raw.get('status')}")
            value = legacy.validate_exact(json.loads(text), legacy.VALIDITY_SCHEMA, 'validity')
            record.update(raw_response=raw, parsed=value)
            artifact.update(status='complete', result=value)
        except Exception as error:
            record.update(error_type=type(error).__name__, error=str(error))
            if raw is not None:
                record['raw_response'] = raw
        artifact['attempts'].append(record)
        atomic_json(destination, artifact)
        if artifact['status'] == 'complete':
            break
        if attempt + 1 < max_attempts:
            time.sleep(2 ** attempt)
    return artifact


def merge(rows, mapping, artifacts, model):
    result = []
    for row in rows:
        reference = mapping[row['id']]
        artifact = artifacts.get(reference['api_id'])
        complete = artifact is not None and artifact['status'] == 'complete'
        value = artifact['result'] if complete else {}
        label = value.get('label')
        binary = ('VALID' if label == 'A' else 'INVALID') if complete else 'UNKNOWN'
        result.append(dict(row, api_validity=binary, api_label=label,
            api_status='complete' if complete else ('failed' if artifact else 'missing_question'),
            api_confidence=value.get('confidence'), api_invalid_type=value.get('invalid_type'),
            api_reason=value.get('reasoning_summary'), api_model=model,
            api_judgment=value, api_question_source=reference['question_source'],
            api_judged_question=reference['question'] or None, api_id=reference['api_id']))
    return result


def summaries(rows):
    stats = []
    for r in sorted({row['round'] for row in rows}):
        group = [row for row in rows if row['round'] == r]
        counts = Counter(row['api_validity'] for row in group)
        judged = counts['VALID'] + counts['INVALID']
        stats.append(dict(round=r, total=len(group), valid=counts['VALID'], invalid=counts['INVALID'],
            unknown=counts['UNKNOWN'], api_failed=sum(row['api_status'] == 'failed' for row in group),
            missing_question=sum(row['api_status'] == 'missing_question' for row in group),
            label_f=sum(row['api_label'] == 'F' for row in group),
            valid_rate_among_judged=counts['VALID']/judged if judged else None,
            valid_fraction_all_rows=counts['VALID']/len(group)))
    return stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--model', default='gpt-5.6-sol')
    parser.add_argument('--reasoning-effort', default='high')
    parser.add_argument('--max-output-tokens', type=int, default=16384)
    parser.add_argument('--concurrency', type=int, default=16)
    parser.add_argument('--max-attempts', type=int, default=3)
    parser.add_argument('--rounds', default='1,2,3,4,5')
    parser.add_argument('--per-round', type=int, default=200)
    parser.add_argument('--prepare-only', action='store_true')
    args = parser.parse_args()
    rounds = [int(r) for r in args.rounds.split(',')]
    if min(args.per_round, args.max_attempts, args.max_output_tokens, args.concurrency) < 1 or len(rounds) != len(set(rounds)):
        parser.error('Invalid counts/rounds')
    if args.output_dir.resolve() == args.input.resolve().parent:
        parser.error('Use a separate output directory; never overwrite source files')
    rows, blind, mapping, source_hash = prepare(args.input, rounds, args.per_round)
    config = dict(protocol='raw_audit_api_validity_v1', source_sha256=source_hash,
        model=args.model, reasoning_effort=args.reasoning_effort, max_output_tokens=args.max_output_tokens,
        prompt_version=legacy.VALIDITY_PROMPT_VERSION, prompt=legacy.VALIDITY_SYSTEM_PROMPT,
        schema=legacy.VALIDITY_SCHEMA, label_mapping='A=VALID; B-F=INVALID; API failure=UNKNOWN',
        rounds=rounds, per_round=args.per_round, sampling='all_raw_rows_no_dedup',
        code_sha256=digest(Path(__file__).read_text()),
        legacy_api_code_sha256=digest(Path(legacy.__file__).read_text()))
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    import fcntl
    with (out / '.run.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        manifest = out / 'manifest.json'
        if not manifest.exists() and any(p.name != '.run.lock' for p in out.iterdir()):
            raise ValueError('Nonempty output directory without an API validity manifest')
        if manifest.exists() and json.loads(manifest.read_text()) != config:
            raise ValueError('Input/model/protocol changed; choose a new output directory')
        atomic_json(manifest, config)
        write_rows(out / 'blind_input.jsonl', blind)
        atomic_json(out / 'id_mapping.json', mapping)
        print(f'[validity] input={len(rows)} api_questions={len(blind)} missing_question={len(rows)-len(blind)} model={args.model}', flush=True)
        if args.prepare_only:
            print('[validity] prepared only; no API calls', flush=True)
            return
        if not os.environ.get('OPENAI_API_KEY'):
            raise SystemExit('Set OPENAI_API_KEY (or source env_rzero.sh) before API calls')
        artifacts = {}
        with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
            futures = {pool.submit(judge_one, item, out / 'artifacts' / (item['id'] + '.json'), config, args.max_attempts): item for item in blind}
            for future in as_completed(futures):
                item = futures[future]
                artifacts[item['id']] = future.result()
                if len(artifacts) % 10 == 0 or len(artifacts) == len(blind):
                    failed = sum(a['status'] != 'complete' for a in artifacts.values())
                    print(f'[validity] {len(artifacts)}/{len(blind)} finished; failed={failed}', flush=True)
        if digest(args.input.read_text()) != source_hash:
            raise RuntimeError('Source changed while annotating; do not merge')
        merged = merge(rows, mapping, artifacts, args.model)
        for r in rounds:
            write_rows(out / f'round_{r}.jsonl', [row for row in merged if row['round'] == r])
        write_rows(out / 'all_rounds.jsonl', merged)
        write_rows(out / 'unresolved.jsonl', [row for row in merged if row['api_validity'] == 'UNKNOWN'])
        stats = summaries(merged)
        atomic_json(out / 'summary.json', stats)
        report = ['# API validity by round', '', '| Round | Total | VALID | INVALID | UNKNOWN | Valid / judged |', '|---|---|---|---|---|---|']
        for s in stats:
            rate = f"{s['valid_rate_among_judged']:.2%}" if s['valid_rate_among_judged'] is not None else 'N/A'
            report.append(f"| {s['round']} | {s['total']} | {s['valid']} | {s['invalid']} | {s['unknown']} | {rate} |")
        report += ['', 'Historical strict rule: A=VALID; B-F=INVALID. F means judge uncertainty and is separately counted in summary.json.',
                   'UNKNOWN means failed API request or no extractable question. No rows were dropped.']
        (out / 'report.md').write_text('\n'.join(report) + '\n')
        print(f'[validity] saved {len(merged)} rows: {out}', flush=True)
        if any(row['api_status'] == 'failed' for row in merged):
            raise SystemExit('API failures remain. Repeat the same command to retry only failures; completed judgments are cached.')


if __name__ == '__main__':
    main()
