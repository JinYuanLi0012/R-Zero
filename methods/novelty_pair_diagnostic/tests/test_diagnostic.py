import ast
import copy
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch

from methods.novelty_pair_diagnostic import core as c, backends as b, pipeline as p


def source(n=80):
    return [dict(id=f'{rnd}-{i:03}', question=f'round {rnd} exercise {i}', round=f'v{rnd}', split='train')
            for rnd in range(1, 6) for i in range(n)]


class Tests(unittest.TestCase):
    def test_uniform_pairs_no_leakage_and_duplicates_retained(self):
        rows = source()
        rows[0]['question'] = rows[-1]['question']
        qs, ps, stats = c.prepare_rows(rows, {}, per_round=50, expected=400)
        self.assertEqual(len(ps), 250)
        self.assertEqual(len(qs), 400)
        self.assertEqual(stats['duplicate_text_records_retained'], 1)
        self.assertEqual((qs, ps, stats), c.prepare_rows(rows, {}, per_round=50, expected=400))
        self.assertEqual(ps, c.prepare_rows(list(reversed(rows)), {}, per_round=50, expected=400)[1])
        qm = {q['id']: q for q in qs}
        seen = set()
        groups = {'test': set(), 'calibration': set()}
        identities = {'test': set(), 'calibration': set()}
        for pair in ps:
            self.assertNotEqual(pair['a'], pair['b'])
            self.assertEqual(qm[pair['a']]['round'], qm[pair['b']]['round'])
            edge = tuple(sorted([pair['a'], pair['b']]))
            self.assertNotIn(edge, seen)
            seen.add(edge)
            for key in edge:
                groups[pair['split']].add(qm[key]['text_group'])
                identities[pair['split']].add(key)
        self.assertFalse(groups['test'] & groups['calibration'])
        self.assertFalse(identities['test'] & identities['calibration'])
        for rnd in range(1, 6):
            self.assertEqual(sum(x['round'] == f'v{rnd}' for x in ps), 50)

    def test_run_manifest_rejects_config_and_source_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            src = folder / 'source.jsonl'
            c.write_rows(src, source())
            config_path = folder / 'config.json'
            c.atomic(config_path, dict(input=str(src), output=str(folder/'out'),
                                       expected_questions=400, pairs_per_round=50))
            config = p.configuration(config_path)
            out = Path(config['output'])
            p.prepare(config, out)
            p.load_run(config, out)
            changed = copy.deepcopy(config)
            changed['seed'] += 1
            with self.assertRaises(ValueError):
                p.load_run(changed, out)
            rows = source(); rows[0]['question'] += ' changed'
            c.write_rows(src, rows)
            with self.assertRaises(ValueError):
                p.load_run(config, out)

    def test_invalid_input(self):
        with self.assertRaises(ValueError):
            c.prepare_rows(source(2), {}, expected=10)
        rows = source()
        rows[1]['id'] = rows[0]['id']
        with self.assertRaises(ValueError):
            c.prepare_rows(rows, {}, expected=400)

    def test_masked_pooling_real_torch(self):
        import torch
        hidden = torch.tensor([[[1., 0.], [0., 1.], [999., 999.]],
                               [[999., 999.], [2., 0.], [2., 0.]]])
        mask = torch.tensor([[1, 1, 0], [0, 1, 1]])
        vector = b.masked_mean(hidden, mask)
        self.assertTrue(torch.allclose(vector, torch.tensor([[2**-.5, 2**-.5], [1., 0.]])))
        with self.assertRaises(ValueError):
            b.masked_mean(hidden, torch.zeros_like(mask))

    def test_bleu_matches_original_ast(self):
        import numpy as np
        from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
        # Execute the actual source function without importing its GPU/Ray reward module.
        code = ast.parse((p.ROOT / p.SOURCES[0]).read_text())
        function = next(n for n in code.body if isinstance(n, ast.FunctionDef) and n.name == '_bleu_distance_matrix')
        scope = dict(np=np, sentence_bleu=sentence_bleu, SmoothingFunction=SmoothingFunction)
        exec(compile(ast.Module(body=[function], type_ignores=[]), '<original BLEU>', 'exec'), scope)
        texts = ['a b c d e f', 'a b c d', 'x', 'x', 'alpha beta gamma delta']
        matrix = scope['_bleu_distance_matrix'](texts)
        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                self.assertAlmostEqual(b.bleu(texts[i], texts[j]), 1 - matrix[i, j])
        self.assertNotEqual(b.bleu(texts[0], texts[1]), b.bleu(texts[1], texts[0]))

    def test_metrics_and_failures(self):
        m = c.metrics(['SAME_TYPE'] * 3 + ['DIFFERENT'] * 3,
                      ['SAME_TYPE', 'DIFFERENT', 'DIFFERENT', 'SAME_TYPE', 'DIFFERENT', 'DIFFERENT'])
        self.assertEqual(m['confusion'], dict(TP=1, FN=2, FP=1, TN=2))
        self.assertAlmostEqual(m['false_negative_rate'], 2/3)
        self.assertAlmostEqual(m['false_positive_rate'], 1/3)
        self.assertAlmostEqual(m['f1'], .4)
        self.assertIsNone(c.metrics([], [])['recall'])
        with self.assertRaises(ValueError):
            c.metrics(['SAME_TYPE'], ['FORMAT_ERROR'])
        self.assertFalse(p.complete_label(dict(status='uncertain', label='DIFFERENT')))
        self.assertFalse(p.complete_score(dict(status='complete', score=float('nan'))))

    def test_calibration_guards(self):
        rows = [dict(split='calibration', label=label, score=score) for label, score in
                [('SAME_TYPE', .8), ('DIFFERENT', .2), ('SAME_TYPE', .9)]]
        self.assertEqual(c.calibrate(rows)['threshold'], .8)
        rows[0]['split'] = 'test'
        with self.assertRaises(ValueError):
            c.calibrate(rows)
        with self.assertRaises(ValueError):
            c.calibrate([dict(split='calibration', label='DIFFERENT', score=.1)])

    def test_cache_identity_history_and_tamper(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            cache = p.Cache(path, {'model': 'a'}, {'x': {'question': 'old'}})
            cache.put('x', dict(status='request_error'))
            cache.put('x', dict(status='complete', label='SAME_TYPE'))
            self.assertEqual(len(cache.get('x')['history']), 1)
            with self.assertRaises(ValueError):
                p.Cache(path, {'model': 'b'}, cache.inputs)
            changed = p.Cache(path, {'model': 'a'}, {'x': {'question': 'new'}})
            with self.assertRaises(ValueError):
                changed.get('x')
            a = json.loads(cache.path('x').read_text()); a['label'] = 'DIFFERENT'
            c.atomic(cache.path('x'), a)
            with self.assertRaises(ValueError):
                cache.get('x')

    def test_reference_blindness_and_failure_status(self):
        pair = dict(question_a='A', question_b='B', score=.9, terra_validity='INVALID', label='DIFFERENT')
        body = b.api_body(pair, p.DEFAULT['api'])
        self.assertEqual(json.loads(body['input'][1]['content']), dict(question_a='A', question_b='B'))
        value = dict(label='UNCERTAIN', shared_setup='unclear', task_comparison='unclear', reason='ambiguous')
        response = NS(output_text=json.dumps(value), model_dump=lambda **kw: {'status': 'completed'})
        client = NS(responses=NS(create=lambda **kw: response))
        self.assertEqual(b.reference_call(client, pair, p.DEFAULT['api'])['status'], 'uncertain')
        response.output_text = 'bad'
        result = b.reference_call(client, pair, p.DEFAULT['api'])
        self.assertEqual(result['status'], 'parse_error')
        self.assertIn('raw_response', result)
        response.output_text = json.dumps(value)
        response.model_dump = lambda **kw: {'status': 'incomplete'}
        self.assertEqual(b.reference_call(client, pair, p.DEFAULT['api'])['status'], 'parse_error')

    def test_base_parser_reused(self):
        self.assertIsNone(b.parse_response_v3('DIFFERENT')['parsed_label'])
        self.assertEqual(b.parse_response_v3(r'\boxed{SAME_TYPE}')['parsed_label'], 'SAME_TYPE')
        self.assertIsNone(b.parse_response_v3(r'\boxed{SAME_TYPE} \boxed{DIFFERENT}')['parsed_label'])
        self.assertEqual(b.sampling_options(1024, 42)['temperature'], .6)

    def test_mock_pipeline_calibration_never_opens_test_labels(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            rows = source()
            qs, pairs, stats = c.prepare_rows(rows, {}, per_round=50, expected=400)
            manifest = {'mock': True, 'stats': stats}
            inputs = {x['pair_id']: x for x in pairs}
            caches = {stage: p.stage_cache(out, stage, manifest, inputs) for stage in ('reference', 'bleu', 'embedding', 'judge')}
            for i, pair in enumerate(pairs):
                key = pair['pair_id']; label = c.LABELS[i % 2]
                caches['reference'].put(key, dict(status='complete', label=label))
                caches['judge'].put(key, dict(status='complete', label=label))
                for name in ('bleu', 'embedding'):
                    caches[name].put(key, dict(status='complete', score=.8 if label == 'SAME_TYPE' else .2))
            original = p.Cache.get
            def guarded(cache, key):
                self.assertEqual(inputs[key]['split'], 'calibration')
                return original(cache, key)
            with patch.object(p.Cache, 'get', guarded):
                p.fit(out, manifest, pairs, p.DEFAULT)
            thresholds = (out / 'thresholds.json').read_bytes()
            test_key = next(x['pair_id'] for x in pairs if x['split'] == 'test')
            caches['reference'].put(test_key, dict(status='uncertain', label='UNCERTAIN'))
            with patch.object(p.Cache, 'get', guarded):
                p.fit(out, manifest, pairs, p.DEFAULT)
            self.assertEqual((out / 'thresholds.json').read_bytes(), thresholds)
            p.report(out, manifest, pairs)
            result = json.loads((out / 'report.json').read_text())
            self.assertEqual(result['status'], 'INCOMPLETE')
            for method in ('bleu', 'embedding', 'judge'):
                m = result['results']['overall'][method]
                self.assertEqual(m['n'], m['planned_n'] - 1)
                self.assertEqual(m['f1'], 1.)
            p.export_review(out, manifest, pairs)
            self.assertNotIn('score', c.read_rows(out / 'review.jsonl')[0])
            cal_key = next(x['pair_id'] for x in pairs if x['split'] == 'calibration')
            caches['reference'].put(cal_key, dict(status='complete', label='DIFFERENT'))
            # A changed calibration label invalidates the already frozen thresholds.
            caches['bleu'].put(cal_key, dict(status='complete', score=.123))
            with self.assertRaises(ValueError):
                p.report(out, manifest, pairs)


class BackendTests(unittest.TestCase):
    def test_mock_embedding_batches_resume_and_overflow(self):
        import torch
        import sys
        calls = []
        class Encoded(dict):
            def to(self, device):
                return self
        class Tokenizer:
            pad_token_id = 0
            name_or_path = 'mock'
            init_kwargs = {'_commit_hash': 'fake'}
            def __call__(self, texts, **kw):
                self.assert_flags = kw
                return {'input_ids': [[int(t) for t in text.split()] for text in texts]}
            def pad(self, data, **kw):
                ids = data['input_ids']; width = max(map(len, ids))
                return Encoded(input_ids=torch.tensor([r + [0]*(width-len(r)) for r in ids]),
                               attention_mask=torch.tensor([[1]*len(r)+[0]*(width-len(r)) for r in ids]))
        class Model:
            config = NS(max_position_embeddings=8)
            def to(self, device): return self
            def eval(self): return self
            def requires_grad_(self, value): self.frozen = not value
            def __call__(self, input_ids, attention_mask, return_dict):
                calls.append(input_ids.shape)
                x = input_ids.float()
                return NS(last_hidden_state=torch.stack([x, torch.ones_like(x)], dim=-1))
        modules = {'transformers': NS(AutoTokenizer=NS(from_pretrained=lambda *a, **kw: Tokenizer()),
                                       AutoModel=NS(from_pretrained=lambda *a, **kw: Model()))}
        qs = [dict(id='a', question='1 3'), dict(id='b', question='2')]
        pairs = [dict(pair_id='p', a='a', b='b')]
        with tempfile.TemporaryDirectory() as tmp, patch.dict(sys.modules, modules):
            cache = p.Cache(Path(tmp), {'mock': True}, {q['id']: q for q in qs})
            settings = dict(batch_size=2, device='cpu', dtype='float32', max_length=8)
            result = b.embedding_run(qs, pairs, cache, dict(model='mock', revision='fake'), settings)
            self.assertAlmostEqual(result['p']['score'], 1., places=6)
            self.assertEqual(cache.get('a')['tokens'], 2)
            self.assertEqual(cache.get('b')['tokens'], 1)
            self.assertEqual(len(calls), 1)
            b.embedding_run(qs, pairs, cache, dict(model='mock', revision='fake'), settings)
            self.assertEqual(len(calls), 1)
            other = p.Cache(Path(tmp)/'overflow', {'mock': True}, {q['id']: q for q in qs})
            with self.assertRaises(ValueError):
                b.embedding_run(qs, pairs, other, dict(model='mock', revision='fake'), dict(settings, max_length=1))
            self.assertEqual(len(calls), 1)

    def test_mock_judge_batch_resume_retry(self):
        import sys
        calls = []
        class Model:
            def __init__(self, **kw): calls.append(('init', kw))
            def get_tokenizer(self): return NS(encode=lambda s: list(range(20)))
            def generate(self, prompts, sampling_params, use_tqdm):
                calls.append(('generate', sampling_params))
                return [NS(outputs=[NS(text=(r'\boxed{SAME_TYPE}' if i == 0 else 'missing label'),
                                         finish_reason='stop')]) for i in range(len(prompts))]
        modules = {'vllm': NS(LLM=Model, SamplingParams=lambda **kw: kw)}
        pairs = [dict(pair_id=str(i), question_a='A', question_b='B') for i in range(2)]
        with tempfile.TemporaryDirectory() as tmp, patch.dict(sys.modules, modules):
            cache = p.Cache(Path(tmp), {'mock': True}, {x['pair_id']: x for x in pairs})
            b.judge_run(pairs, cache, dict(model='mock', revision='fake'), p.DEFAULT['judge'])
            self.assertEqual(cache.get('0')['label'], 'SAME_TYPE')
            self.assertEqual(cache.get('1')['status'], 'parse_error')
            self.assertEqual(cache.get('1')['raw_output'], 'missing label')
            b.judge_run(pairs, cache, dict(model='mock', revision='fake'), p.DEFAULT['judge'])
            self.assertEqual(len(calls), 2)
            b.judge_run(pairs, cache, dict(model='mock', revision='fake'), p.DEFAULT['judge'], retry=True)
            self.assertEqual(cache.get('1')['status'], 'complete')
            self.assertEqual(len(cache.get('1')['history']), 1)
            self.assertEqual(calls[0][1]['revision'], 'fake')


if __name__ == '__main__':
    unittest.main()
