import ast
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

from methods.rzero_raw_audit import protocol, worker, run


def test_prompt_matches_ordinary_generator_exactly():
    source = ast.parse((run.ROOT / 'question_generate/question_generate.py').read_text())
    main = next(n for n in source.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
    chat = next(n for n in main.body if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == 'chat' for t in n.targets))
    assert ast.literal_eval(chat.value) == protocol.QUESTIONER_CHAT


def test_pairing_uses_previous_solver():
    pairs = run.model_pairs('/models-root', 'run', [1, 2, 3, 4, 5])
    assert pairs[0]['solver'] == 'Qwen/Qwen3-4B-Base'
    assert all(f'_questioner_v{p["round"]}/global_step_5/' in p['questioner'] for p in pairs)
    assert all(f'_solver_v{p["round"]-1}/global_step_15/' in p['solver'] for p in pairs[1:])


def test_nonempty_denominator_tie_and_legacy_filter_are_only_annotations():
    vote = protocol.majority_vote(['1', '2', '', None, '1', '2', '', '', ''], lambda *a, **k: False)
    assert vote['majority_answer'] == '1' and vote['score'] == 0.5
    assert vote['majority_fraction_of_all_votes'] == 2/9
    assert vote['tied_largest_clusters'] == 2
    assert 'question_contains_box' in protocol.legacy_filter_reasons('A box contains balls', vote)


def test_timeout_does_not_try_reverse_and_empty_votes_are_retained():
    calls = []
    def grade(a, b, **kwargs):
        calls.append((a, b))
        return 'TIMED_OUT'
    vote = protocol.majority_vote(['a', 'b'], grade)
    assert calls == [('b', 'a')]
    assert vote['answer_counts'] == {'a': 1, 'b': 1}
    empty = protocol.majority_vote(['']*9, grade)
    assert empty['score'] is None and empty['majority_answer'] is None


def test_cluster_matches_existing_evaluator_body():
    source = ast.parse((run.ROOT / 'question_evaluate/evaluate.py').read_text())
    outer = next(n for n in source.body if isinstance(n, ast.For) and isinstance(n.target, ast.Tuple))
    body = outer.body[0].body  # legacy try block
    start = next(i for i,n in enumerate(body) if isinstance(n, ast.Assign)
                 and any(isinstance(t,ast.Name) and t.id == 'answer_counts' for t in n.targets))
    end = next(i for i,n in enumerate(body) if isinstance(n,ast.Assign)
               and any(isinstance(t,ast.Name) and t.id == 'score' for t in n.targets))
    # Keep the enclosing loop so original continue statements remain legal.
    statements = ast.parse('for _ in [0]:\n pass').body[0]
    statements.body = body[start:end+1]
    module = ast.fix_missing_locations(ast.Module(body=[statements], type_ignores=[]))
    for answers in [['1','1','2'], ['2','1'], ['no solution', 'no roots'], ['a','b','a']]:
        def grader(a,b,**kwargs): return a == b
        ns = dict(results=answers, grade_answer_with_timeout=grader, args=SimpleNamespace(suffix=0))
        exec(compile(module, 'legacy_vote', 'exec'), ns)
        new = protocol.majority_vote(answers, grader)
        assert new['answer_counts'] == ns['answer_counts']
        assert new['majority_answer'] == ns['majority_answer']
        assert new['score'] == ns['score']


def fake_runtime(monkeypatch):
    class Tokenizer:
        chat_template = None
        pad_token = None
        eos_token = '<eos>'
        eos_token_id = 1
    class LLM:
        def __init__(self, **kwargs): pass
        def generate(self, prompts, sampling_params, **kwargs):
            n = sampling_params.n
            return [SimpleNamespace(outputs=[SimpleNamespace(
                text=('<question>A box contains balls</question> \\boxed{1}' if i else 'malformed') if n == 1 else '\\boxed{1}',
                finish_reason='stop') for _ in range(n)]) for i in range(len(prompts))]
    monkeypatch.setitem(sys.modules, 'vllm', SimpleNamespace(LLM=LLM, SamplingParams=lambda **kw: SimpleNamespace(**kw)))
    monkeypatch.setitem(sys.modules, 'transformers', SimpleNamespace(AutoTokenizer=SimpleNamespace(from_pretrained=lambda _: Tokenizer())))
    monkeypatch.setitem(sys.modules, 'stopit', SimpleNamespace(threading_timeoutable=lambda **kw: lambda f: lambda a,b,**opts: f(a,b)))
    monkeypatch.setitem(sys.modules, 'mathruler', SimpleNamespace())
    monkeypatch.setitem(sys.modules, 'mathruler.grader', SimpleNamespace(extract_boxed_content=lambda _: '1', grade_answer=lambda a,b: a==b))


def test_end_to_end_preserves_200_raw_rows_duplicates_failures_and_resume(tmp_path, monkeypatch):
    fake_runtime(monkeypatch)
    storage = tmp_path / 'storage'
    model = storage / 'models/qwen3_4b_rzero_8k_5round_questioner_v1/global_step_5/actor/huggingface'
    model.mkdir(parents=True)
    (model / 'config.json').write_text('{}')
    (model / 'model.safetensors').write_bytes(b'test')
    calls = []
    def local_workers(commands, devices, timeout):
        for command in commands:
            calls.append(command)
            monkeypatch.setattr(sys, 'argv', ['worker'] + command[3:])
            worker.main()
        return 0
    monkeypatch.setattr(run, 'run_workers', local_workers)
    output = tmp_path / 'output'
    argv = ['run', '--storage', str(storage), '--output-dir', str(output), '--rounds', '1']
    monkeypatch.setattr(sys, 'argv', argv)
    run.main()
    rows = worker.read_rows(output / 'round_1.jsonl')
    assert len(rows) == len({r['id'] for r in rows}) == 200
    assert sum(r['questioner_parse_ok'] for r in rows) == 196
    assert all(r['score'] == 1 for r in rows if r['questioner_parse_ok'])
    assert not any(r['would_pass_original_filter'] for r in rows)
    assert all(len(r['solver_responses']) == 9 for r in rows if r['questioner_parse_ok'])
    assert all(r['questioner_raw'] for r in rows)
    assert sum(len(worker.read_rows(p)) for p in output.glob('round_1/generate_*.jsonl')) == 200
    assert len(calls) == 8
    monkeypatch.setattr(sys, 'argv', argv + ['--resume'])
    run.main()
    assert len(calls) == 8
    monkeypatch.setattr(sys, 'argv', argv + ['--resume', '--per-round', '201'])
    with pytest.raises(SystemExit, match='configuration changed'):
        run.main()
