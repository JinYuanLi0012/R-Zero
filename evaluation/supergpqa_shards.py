"""Disjoint SuperGPQA work assignment and count-based two-shard aggregation."""
import hashlib
import json


def partition(rows, categories, shard_index, num_shards):
    if num_shards < 1 or not 0 <= shard_index < num_shards:
        raise ValueError('Invalid SuperGPQA shard index/count')
    ordered = [dict(row) for category in categories for row in rows if row['discipline'] == category]
    digest = hashlib.sha256(json.dumps(ordered, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    selected = []
    for index, row in enumerate(ordered):
        if index % num_shards == shard_index:
            row['_evaluation_index'] = index
            selected.append(row)
    return selected, len(ordered), digest


def merge_shards(folders, model, output_dir):
    records, rows = [], []
    for index, folder in enumerate(folders):
        record = json.loads((folder / 'supergpqa_score.json').read_text())
        part = json.loads((folder / 'supergpqa_outputs.json').read_text())
        if (record.get('model') != model or record.get('dataset') != 'supergpqa'
                or record.get('shard_index') != index or record.get('num_shards') != len(folders)):
            raise ValueError('SuperGPQA shard identity mismatch')
        count, correct = record['total'], record['correct']
        if (type(count) is not int or type(correct) is not int or count != len(part)
                or not 0 <= correct <= count):
            raise ValueError('Invalid SuperGPQA shard counts')
        if any(type(row.get('_evaluation_index')) is not int or
               row['_evaluation_index'] % len(folders) != index for row in part):
            raise ValueError('Wrong SuperGPQA shard assignment')
        records.append(record)
        rows.extend(part)
    total = records[0]['expected_total']
    if (type(total) is not int or total <= 0 or any(
            r['expected_total'] != total or r['dataset_fingerprint'] != records[0]['dataset_fingerprint']
            for r in records)):
        raise ValueError('SuperGPQA shard dataset mismatch')
    ids = [row['_evaluation_index'] for row in rows]
    if len(ids) != total or set(ids) != set(range(total)):
        raise ValueError('SuperGPQA shards contain missing or duplicated questions')
    correct = sum(r['correct'] for r in records)
    score = dict(dataset='supergpqa', model=model, accuracy=round(100 * correct / total, 2),
                 correct=correct, total=total, num_shards=len(folders),
                 dataset_fingerprint=records[0]['dataset_fingerprint'])
    rows.sort(key=lambda row: row['_evaluation_index'])
    (output_dir / 'supergpqa_outputs.json').write_text(json.dumps(rows, ensure_ascii=False))
    (output_dir / 'supergpqa_score.json').write_text(json.dumps(score, indent=2) + '\n')
    return score
