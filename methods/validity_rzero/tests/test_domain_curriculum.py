"""CPU coverage for allocation, real prompt routing, and resume isolation."""
import ast
from collections import Counter
from pathlib import Path
import types
import pytest
from methods.validity_rzero.domain_curriculum.core import DOMAINS, balanced_domains, messages, phase_b_domains, training_rows
from methods.validity_rzero.tests.test_novelty_invalid_reward import pipeline_init
from methods.validity_rzero.prepare_solver_dataset import build_mixed_rows
ROOT = Path(__file__).resolve().parents[3]


def test_balanced_training_and_rotation():
    rows = training_rows(512, 5, 43, 'round1')
    assert len(rows) == 2560
    assert len({r['domain_prompt_id'] for r in rows}) == 2560
    for step in range(5):
        batch = rows[step*512:(step+1)*512]
        assert set(Counter(r['domain'].split(' → ')[0] for r in batch).values()) == {64}
        for parent, leaves in DOMAINS:
            counts = Counter(r['domain'] for r in batch if r['domain'].startswith(parent + ' → '))
            assert len(counts) == len(leaves)
            assert max(counts.values()) - min(counts.values()) <= 1
    parent, leaves = DOMAINS[0]
    counts = Counter(r['domain'] for r in rows[:1536])
    assert [counts[f'{parent} → {leaf}'] for leaf in leaves] == [64]*3
    assert rows == training_rows(512, 5, 43, 'round1')
    assert rows != training_rows(512, 5, 44, 'round1')


@pytest.mark.parametrize('count', [0, 1, 7, 8, 31, 512, 10000])
def test_arbitrary_budgets(count):
    plan = balanced_domains(count)
    assert len(plan) == count
    counts = Counter(x.split(' → ')[0] for x in plan)
    values = [counts[p] for p, _ in DOMAINS]
    assert max(values) - min(values) <= 1


def test_four_shards_global_plan():
    full = sum([phase_b_domains(2500, 4, i, 43, 'solver_v1') for i in range(4)], [])
    assert full == balanced_domains(10000, 43, context='solver_v1')
    assert set(Counter(x.split(' → ')[0] for x in full).values()) == {1250}
    assert len(set(full)) == 28


def test_actual_dataset_prompt_changes_only_domain_sentence():
    tree = ast.parse((ROOT / 'verl/utils/dataset.py').read_text())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'RLHFDataset')
    method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == '_build_messages')
    mod = ast.Module(body=[ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0), method], type_ignores=[])
    env = {}
    exec(compile(ast.fix_missing_locations(mod), 'dataset_messages', 'exec'), env)
    obj = types.SimpleNamespace(prompt_key='problem', format_prompt='questioner_format', format_prompt_source_key=None)
    legacy = env['_build_messages'](obj, {'problem': 'ignored'})
    obj.format_prompt = 'rzero_domain_balanced_v1\n'
    domain = balanced_domains(512)[0]
    current = env['_build_messages'](obj, {'problem': domain})
    assert current == messages(domain)
    old = 'The problem could come from any field of mathematics, including but not limited to algebra, geometry, number theory, combinatorics, prealgebra, probability, statistics, and calculus. '
    new = f'The problem must belong to the following mathematical domain:\n{domain}\nThe solution must centrally require concepts or reasoning from this domain. '
    assert current[0]['content'] == legacy[0]['content'].replace(old, new)
    assert current[1] == legacy[1]


def test_domain_resume_isolation(tmp_path):
    env = {'VALIDITY_RZERO_DOMAIN_MODE': 'balanced_v1', 'VALIDITY_RZERO_DOMAIN_SEED': '43'}
    result, state = pipeline_init(tmp_path, env)
    assert result.returncode == 0, result.stderr
    assert state['configuration']['domain_curriculum'] == 'balanced_v1'
    result, resumed = pipeline_init(tmp_path, env, resume=True)
    assert result.returncode == 0, result.stderr
    assert resumed == state
    for changed in [{}, dict(env, VALIDITY_RZERO_DOMAIN_SEED='44')]:
        result, _ = pipeline_init(tmp_path, changed, resume=True)
        assert result.returncode != 0
        assert 'run configuration changed' in result.stderr


def test_legacy_cannot_resume_as_domain(tmp_path):
    result, state = pipeline_init(tmp_path, {})
    assert result.returncode == 0
    assert 'domain_curriculum' not in state['configuration']
    result, _ = pipeline_init(tmp_path, {'VALIDITY_RZERO_DOMAIN_MODE': 'balanced_v1'}, resume=True)
    assert result.returncode != 0


def test_domain_metadata_does_not_change_terra_mixture():
    generated = [{'question': str(i), 'answer': '2', 'score': 0.5, 'domain': 'test domain'} for i in range(90)]
    terra = [{'split': 'train', 'terra_validity': 'INVALID', 'question': str(i), 'validity_rl_target': 'INVALID'} for i in range(10)]
    mixed, stats = build_mixed_rows(generated, terra, 0.3, 0.8, 0.1, 1)
    assert stats['actual_replay_ratio'] == 0.1
    assert all(r['domain'] == 'test domain' for r in mixed if r['source'] == 'rzero')
    plain, plain_stats = build_mixed_rows([{k:v for k,v in r.items() if k != 'domain'} for r in generated], terra, 0.3, 0.8, 0.1, 1)
    assert stats == plain_stats
    assert [{k:v for k,v in r.items() if k != 'domain'} for r in mixed] == plain


@pytest.mark.parametrize('enabled', [False, True])
@pytest.mark.parametrize('chat_template', [False, True])
def test_actual_phase_b_generation(tmp_path, monkeypatch, enabled, chat_template):
    # Execute production main with a fake model; inspect every submitted prompt and saved row.
    import json
    import os
    import re
    tree = ast.parse((ROOT / 'question_generate/question_generate.py').read_text())
    funcs = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in {'main', 'extract_boxed'}]
    captured = {}
    class Tokenizer:
        pad_token = 'pad'
        eos_token = 'eos'
        pad_token_id = 0
        eos_token_id = 1
        def apply_chat_template(self, chat, **kwargs):
            return json.dumps(chat)
    tokenizer = Tokenizer()
    tokenizer.chat_template = chat_template
    class Model:
        def __init__(self, **kwargs):
            pass
        def generate(self, prompts, sampling_params):
            captured['prompts'] = prompts
            return [types.SimpleNamespace(outputs=[types.SimpleNamespace(text='<question>q</question>\\boxed{2}')]) for _ in prompts]
    monkeypatch.setenv('VALIDITY_RZERO_ENABLED', '1' if enabled else '0')
    monkeypatch.setenv('VALIDITY_RZERO_DOMAIN_MODE', 'balanced_v1')
    monkeypatch.setenv('QUESTION_NUM_SHARDS', '4')
    monkeypatch.setenv('VALIDITY_RZERO_DOMAIN_SEED', '43')
    (tmp_path / 'generated_question').mkdir()
    env = dict(os=os, json=json, re=re, STORAGE_PATH=str(tmp_path),
               AutoTokenizer=types.SimpleNamespace(from_pretrained=lambda _: tokenizer),
               vllm=types.SimpleNamespace(LLM=Model, SamplingParams=lambda **kw: kw),
               get_dataset_handler=lambda _: types.SimpleNamespace(load_data=lambda: (['q'], ['2'])))
    exec(compile(ast.Module(body=funcs, type_ignores=[]), 'phase_b_main', 'exec'), env)
    env['main'](types.SimpleNamespace(model='test', suffix='0', save_name='solver_v1', num_samples=2500))
    rows = json.loads((tmp_path / 'generated_question/solver_v1_0.json').read_text())
    assert len(rows) == 2500
    if enabled:
        domains = phase_b_domains(2500, 4, 0, 43, 'solver_v1')
        assert [r['domain'] for r in rows] == domains
        for prompt, domain in zip(captured['prompts'], domains):
            expected = messages(domain)
            assert prompt == (json.dumps(expected) if chat_template else 'system: '+expected[0]['content']+'\nuser: '+expected[1]['content'])
    else:
        assert len(set(captured['prompts'])) == 1
        assert all('domain' not in r for r in rows)
        assert 'any field of mathematics' in captured['prompts'][0]


def test_prepare_parquet(tmp_path, monkeypatch):
    import sys
    from datasets import load_dataset
    from methods.validity_rzero.domain_curriculum.prepare import main
    path = tmp_path / 'prompts.parquet'
    monkeypatch.setattr(sys, 'argv', ['prepare', '--output', str(path), '--batch-size', '512', '--steps', '5', '--context', 'round1'])
    main()
    rows = load_dataset('parquet', data_files=str(path), split='train', cache_dir=str(tmp_path / 'cache'))
    assert rows.to_list() == training_rows(512, 5, 43, 'round1')
