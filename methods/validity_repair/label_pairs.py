#!/usr/bin/env python3
"""Prepare matched arms and label with frozen base Solver, never API/Terra answers."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'methods/validity_rl_terra_dataset'))
from common import atomic_json, read_jsonl, write_jsonl
from question_evaluate.majority import majority_vote, render_prompt

VERSION = 'paired-base-majority-v1'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def prepare(repair_dir, out, limit=0):
    audit = read_jsonl(repair_dir / 'repair_audit.jsonl')
    originals = read_jsonl(repair_dir / 'original_questions.jsonl')
    repaired = read_jsonl(repair_dir / 'repaired_questions.jsonl')
    if not len(audit) == len(originals) == len(repaired) or not audit:
        raise ValueError('source lengths differ or empty source')
    seen, pairs, excluded = set(), [], []
    for a, o, r in zip(audit, originals, repaired):
        key = a['id']
        if key in seen or not key == o['id'] == r['id']:
            raise ValueError('duplicate or misaligned IDs')
        seen.add(key)
        if (a['original_question'] != o['question'] or a['final_question'] != r['question']
                or o['round'] != r['round'] or o['split'] != 'train' or r['split'] != 'train'):
            raise ValueError(f'source mismatch: {key}')
        changed = a['status'] == 'accepted'
        if (o['question'] != r['question']) != changed:
            raise ValueError(f'change/status mismatch: {key}')
        if a['status'] not in ('accepted', 'unchanged_valid'):
            excluded.append({'id': key, 'reason': a['status']})
            continue
        if a['source_validity'] != ('INVALID' if changed else 'VALID'):
            raise ValueError('source validity/status mismatch')
        pairs.append({'id': key, 'round': o['round'], 'changed': changed,
                      'original_question': o['question'], 'repaired_question': r['question']})
    full_count = len(pairs)
    if limit:
        pairs = pairs[:limit]
    if not pairs:
        raise ValueError('no eligible pairs')
    jobs = []
    for pair in pairs:
        for variant in (('original', 'repaired') if pair['changed'] else ('shared',)):
            question = pair['repaired_question'] if variant == 'repaired' else pair['original_question']
            job_id = hashlib.sha256((pair['id'] + ':' + variant).encode()).hexdigest()[:24]
            jobs.append({'job_id': job_id, 'pair_id': pair['id'], 'variant': variant, 'question': question})
            pair[variant + '_job'] = job_id
    config = {'version': VERSION, 'source_hash': digest([audit, originals, repaired]),
              'pair_limit': limit, 'full_eligible_pairs': full_count, 'selected_pairs': len(pairs),
              'jobs_hash': digest(jobs), 'jobs_count': len(jobs)}
    path = out / 'pair_manifest.json'
    if path.exists() and json.loads(path.read_text()) != config:
        raise ValueError('source or selection changed: use a new LABEL_OUTPUT_DIR')
    atomic_json(path, config)
    write_jsonl(out / 'pairs.jsonl', pairs)
    write_jsonl(out / 'label_jobs.jsonl', jobs)
    write_jsonl(out / 'excluded_repair_ids.jsonl', excluded)
    for arm in ('original', 'repaired'):
        write_jsonl(out / f'{arm}_questions.jsonl', [
            {'id': p['id'], 'round': p['round'], 'question': p[arm + '_question']} for p in pairs])
    return pairs, jobs, config


def usable(answer):
    # None is mathruler's possible parse sentinel; INVALID is not a math label.
    return isinstance(answer, str) and bool(answer.strip()) and answer.strip().upper() not in ('NONE', 'INVALID')


def finalize(pairs, artifacts, out):
    arms = {'original': [], 'repaired': []}
    drops = []
    for pair in pairs:
        keys = [pair['original_job'], pair['repaired_job']] if pair['changed'] else [pair['shared_job']] * 2
        records = [artifacts[k] for k in keys]
        if any(a['status'] != 'complete' or not usable(a.get('answer')) for a in records):
            drops.append({'id': pair['id'], 'reasons': [a['status'] for a in records], 'jobs': keys})
            continue
        for arm, a in zip(arms, records):
            arms[arm].append({'id': pair['id'], 'round': pair['round'], 'problem': pair[arm + '_question'],
                              'answer': a['answer'], 'score': a['score'], 'label_job_id': a['job_id']})
    for arm, rows in arms.items():
        write_jsonl(out / f'{arm}_train.jsonl', rows)
    write_jsonl(out / 'excluded_label_ids.jsonl', drops)
    write_jsonl(out / 'label_results.jsonl', artifacts.values())
    kept = {r['id'] for r in arms['original']}
    shared = sum(not p['changed'] and p['id'] in kept for p in pairs)
    stats = {'selected_pairs': len(pairs), 'kept_pairs': len(kept), 'paired_drops': len(drops),
             'shared_valid_kept': shared, 'changed_pairs_kept': len(kept)-shared,
             'artifact_status_counts': dict(Counter(a['status'] for a in artifacts.values())),
             'score_filter_applied': False, 'validity_gate_applied': False, 'training_started': False}
    atomic_json(out / 'analysis/statistics.json', stats)
    report = ['# Paired Solver pseudo-labels', '', f'- Selected pairs: {len(pairs)}',
              f'- Training rows per arm: {len(kept)}', f'- Shared originally VALID: {shared}',
              f'- Changed pairs: {len(kept)-shared}', f'- Paired exclusions for unusable labels: {len(drops)}',
              '- No score thresholds, validity gate, or question-type filtering.',
              '- Scores measure vote agreement, not correctness.', '', '| Arm | Mean score | Score=1 |', '|---|---:|---:|']
    for arm, rows in arms.items():
        mean = sum(r['score'] for r in rows)/len(rows) if rows else 0
        report.append(f'| {arm} | {mean:.4f} | {sum(r["score"]==1 for r in rows)} |')
    (out / 'analysis/report.md').write_text('\n'.join(report)+'\n')
    return stats


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repair-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--model', default='Qwen/Qwen3-4B-Base')
    parser.add_argument('--revision', default=None)
    parser.add_argument('--pair-limit', type=int, default=0)
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--num-samples', type=int, default=9)
    parser.add_argument('--batch-size', type=int, default=16)
    parser.add_argument('--tensor-parallel-size', type=int, default=1)
    parser.add_argument('--gpu-memory-utilization', type=float, default=0.85)
    parser.add_argument('--max-model-len', type=int, default=8192)
    parser.add_argument('--max-tokens', type=int, default=4096)
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()
    if args.pair_limit < 0 or min(args.num_samples,args.batch_size,args.tensor_parallel_size,args.max_tokens) < 1 or args.max_model_len <= args.max_tokens or not 0 < args.gpu_memory_utilization < 1:
        parser.error('invalid numeric configuration')
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    import fcntl
    with (out / '.label.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        pairs, jobs, prep = prepare(args.repair_dir, out, args.pair_limit)
        print(f'[prepare] pairs={len(pairs)} shared={sum(not p["changed"] for p in pairs)} jobs={len(jobs)}', flush=True)
        config = {**prep, 'model': args.model, 'revision': args.revision, 'samples': args.num_samples,
                  'max_tokens': args.max_tokens, 'temperature': 1.0, 'top_p': 1.0, 'top_k': 40,
                  'seed': args.seed, 'tensor_parallel_size': args.tensor_parallel_size,
                  'max_model_len': args.max_model_len, 'batch_size': args.batch_size,
                  'majority_code_sha256': hashlib.sha256((ROOT/'question_evaluate/majority.py').read_bytes()).hexdigest()}
        path = out / 'label_manifest.json'
        if path.exists() and json.loads(path.read_text()) != config:
            raise ValueError('generation configuration changed: use a new output directory')
        atomic_json(path, config)
        if args.prepare_only:
            return
        artifacts, pending = {}, []
        config_hash = digest(config)
        for job in jobs:
            path = out / 'artifacts' / (job['job_id']+'.json')
            if path.exists():
                a = json.loads(path.read_text())
                if a['config_hash'] != config_hash or a['job_hash'] != digest(job):
                    raise ValueError('cached label artifact mismatch')
                artifacts[job['job_id']] = a
            else:
                pending.append(job)
        if pending:
            import vllm
            import stopit
            from transformers import AutoTokenizer
            from mathruler.grader import extract_boxed_content, grade_answer
            tokenizer = AutoTokenizer.from_pretrained(args.model, revision=args.revision)
            model = vllm.LLM(model=args.model, tokenizer=args.model, revision=args.revision,
                             tokenizer_revision=args.revision, tensor_parallel_size=args.tensor_parallel_size,
                             gpu_memory_utilization=args.gpu_memory_utilization, seed=args.seed,
                             max_model_len=args.max_model_len)
            timed_grade = stopit.threading_timeoutable(default='TIMED_OUT')(grade_answer)
            for start in range(0, len(pending), args.batch_size):
                chunk = pending[start:start+args.batch_size]
                prompts = [render_prompt(tokenizer, j['question']) for j in chunk]
                for prompt in prompts:
                    if len(tokenizer.encode(prompt)) + args.max_tokens > args.max_model_len:
                        raise ValueError('prompt exceeds configured context budget; do not truncate paired questions')
                seeds = [(args.seed + int(j['job_id'][:8],16)) % (2**31) for j in chunk]
                params = [vllm.SamplingParams(n=args.num_samples,max_tokens=args.max_tokens,
                          temperature=1.0,top_p=1.0,top_k=40,stop_token_ids=[tokenizer.eos_token_id],seed=seed) for seed in seeds]
                responses = model.generate(prompts, sampling_params=params, use_tqdm=True)
                if len(responses) != len(chunk):
                    raise RuntimeError('generation output count mismatch')
                for job, res, seed in zip(chunk,responses,seeds):
                    if len(res.outputs) != args.num_samples:
                        raise RuntimeError('sample count mismatch')
                    texts = [o.text for o in res.outputs]
                    extracted = [extract_boxed_content(t) for t in texts]
                    vote = majority_vote(extracted, lambda a,b: timed_grade(a,b,timeout=10))
                    artifact = {**job, **vote, 'status': 'complete' if usable(vote['answer']) else 'no_usable_answer',
                                'config_hash': config_hash, 'job_hash': digest(job), 'seed': seed,
                                'raw_responses': texts, 'extracted_answers': extracted,
                                'finish_reasons': [o.finish_reason for o in res.outputs]}
                    atomic_json(out/'artifacts'/(job['job_id']+'.json'), artifact)
                    artifacts[job['job_id']] = artifact
                print(f'[label] {len(artifacts)}/{len(jobs)} saved',flush=True)
        # Restore deterministic source-job order even after a partially completed run.
        stats = finalize(pairs,{j['job_id']:artifacts[j['job_id']] for j in jobs},out)
        print(f'[complete] {stats["kept_pairs"]} rows per arm; report={out / "analysis/report.md"}',flush=True)


if __name__ == '__main__':
    main()
