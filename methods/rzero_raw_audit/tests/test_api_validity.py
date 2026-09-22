import json
import sys

import pytest

from methods.rzero_raw_audit import api_validity as api
from methods.rzero_raw_audit.worker import read_rows, write_rows


def judgment(label='A'):
    return dict(goal_restatement='compute the requested value', conditions_complete=True,
        contradictory=label == 'D', multiple_reasonable_interpretations=False,
        solution_exists=label != 'D', unique_or_explicit_grading=True, label=label,
        confidence=.9, issue_types=[], reasoning_summary='checked conditions', derived_answer=None,
        invalid_type=None if label == 'A' else 'other')


def test_blind_inputs_salvage_tags_without_exposing_answers(tmp_path):
    source = tmp_path / 'input.jsonl'
    rows = [dict(id=f'q_r1_{i}', round=1, question=None,
                 questioner_raw='<question>Compute 1+1</question> secret_answer_and_reasoning',
                 majority_answer='SECRET', score=.99) for i in range(2)]
    write_rows(source, rows)
    original, blind, mapping, _ = api.prepare(source, [1], 2)
    assert original == rows and len(blind) == 2
    assert blind[0]['id'] != blind[1]['id']
    assert all(set(item) == {'id', 'question'} for item in blind)
    assert all(item['question'] == 'Compute 1+1' for item in blind)
    assert 'SECRET' not in json.dumps(blind) and 'q_r1_' not in json.dumps(blind)


def test_partial_generation_is_rejected_before_api(tmp_path):
    source = tmp_path / 'input.jsonl'
    write_rows(source, [dict(id='one', round=1, question='Q')])
    with pytest.raises(ValueError, match='incomplete'):
        api.prepare(source, [1, 2, 3, 4, 5], 200)


def test_retry_preserves_attempts_and_cache_skips_completed(tmp_path, monkeypatch):
    item = {'id': 'opaque', 'question': 'Q'}
    config = {'model': 'test', 'reasoning_effort': 'high', 'max_output_tokens': 100}
    destination = tmp_path / 'artifact.json'
    def broken(*args): raise RuntimeError('temporary outage')
    monkeypatch.setattr(api.legacy, 'api_call', broken)
    first = api.judge_one(item, destination, config, 1)
    assert first['status'] == 'failed'
    calls = []
    def valid(*args):
        calls.append(args)
        return json.dumps(judgment()), {'status': 'completed'}
    monkeypatch.setattr(api.legacy, 'api_call', valid)
    second = api.judge_one(item, destination, config, 1)
    assert second['status'] == 'complete' and len(second['attempts']) == 2
    assert api.judge_one(item, destination, config, 1) == second
    assert len(calls) == 1


def test_incomplete_response_cannot_be_a_valid_label(tmp_path, monkeypatch):
    monkeypatch.setattr(api.legacy, 'api_call', lambda *args: (json.dumps(judgment()), {'status': 'incomplete'}))
    result = api.judge_one({'id':'x', 'question':'q'}, tmp_path/'x.json',
        {'model':'test', 'reasoning_effort':'high', 'max_output_tokens':100}, 1)
    assert result['status'] == 'failed' and result['result'] is None


def test_full_1000_rows_preserve_votes_labels_rounds_and_source(tmp_path, monkeypatch):
    rows = [dict(id=f'q_r{r}_{i}', round=r, question='same question',
                 majority_answer=f'original-{r}-{i}', score=0.5,
                 solver_responses=['secret vote']*9) for r in range(1,6) for i in range(200)]
    rows[-1]['question'] = None
    rows[-1]['questioner_raw'] = 'no question tags'
    source = tmp_path/'source/all_rounds.jsonl'
    write_rows(source, rows)
    source_bytes = source.read_bytes()
    calls = []
    def call(model, prompt, name, schema, item, effort, tokens):
        assert prompt == api.legacy.VALIDITY_SYSTEM_PROMPT
        assert set(item) == {'id', 'question'}
        calls.append(item)
        return json.dumps(judgment('A' if int(item['id'][-1],16)%2 else 'F')), {'status':'completed'}
    monkeypatch.setattr(api.legacy, 'api_call', call)
    monkeypatch.setenv('OPENAI_API_KEY', 'test-placeholder')
    out = tmp_path/'labels'
    argv = ['validity', '--input',str(source),'--output-dir',str(out)]
    monkeypatch.setattr(sys,'argv',argv)
    api.main()
    merged = read_rows(out/'all_rounds.jsonl')
    assert len(merged) == 1000 and len(calls) == 999
    for old,new in zip(rows,merged):
        assert all(new[key] == value for key,value in old.items())
    assert merged[-1]['api_validity'] == 'UNKNOWN' and merged[-1]['api_status'] == 'missing_question'
    assert all(row['api_validity'] == ('VALID' if row['api_label']=='A' else 'INVALID') for row in merged[:-1])
    assert all(len(read_rows(out/f'round_{r}.jsonl')) == 200 for r in range(1,6))
    assert source.read_bytes() == source_bytes
    api.main()
    assert len(calls) == 999
