"""CPU checks for the small single-answer pipeline; no GPU quality claims."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

from methods.validity_rzero.scope_tree import prompts, run
from methods.validity_rzero.scope_tree.core import (
    SchemaError, TreeBuilder, decision, description, gap_answer, parse_response,
)
from methods.validity_rzero.scope_tree.run import StructuredClient, ParseRetriesExhausted


def boxed(value):
    return '<analysis>Consider the scope and distinctions.</analysis>\n<box>' + value + '</box>'


class Backend:
    def __init__(self, outputs):
        self.outputs = iter(outputs)
        self.seeds, self.users = [], []

    def generate(self, system, user, seed):
        self.seeds.append(seed)
        self.users.append(user)
        value = next(self.outputs)
        return {'raw_completion': value, 'finish_reason': 'stop'}


class Script:
    def __init__(self, values):
        self.values, self.calls = values, []
        self.last_raw_completion = ''

    def request(self, label, prompt, validator):
        self.calls.append((label, prompt))
        raw = boxed(self.values[label])
        self.last_raw_completion = raw
        return validator(parse_response(raw))


def confirms(parent, count):
    return {f'{parent}/coverage/{count}/{i}': 'NONE' for i in range(2)}


def happy():
    return {'root/principle': 'Primary structures',
            'root/candidate/1/propose': 'Region A', 'root/candidate/1/audit/0': 'YES',
            'root/coverage/1/0': 'Region B has no allocation',
            'root/candidate/2/propose': 'Region B', 'root/candidate/2/audit/0': 'YES', **confirms('root', 2),
            '1/principle': 'Relations among objects', '1/candidate/1/propose': 'Family A1',
            '1/candidate/1/audit/0': 'YES', **confirms('1', 1),
            '2/principle': 'Relations among objects', '2/candidate/1/propose': 'Family B1',
            '2/candidate/1/audit/0': 'YES', **confirms('2', 1), 'global/audit': 'YES'}


class BoxTests(unittest.TestCase):
    def test_only_box_parsed_analysis_is_not_a_schema(self):
        for prefix in ('Plain reasoning. ', '<analysis>Reasoning</analysis>', 'Reasoning</analysis>', ''):
            self.assertEqual(parse_response(prefix + '<box>A scope: with | symbols\nand another line.</box>'),
                             'A scope: with | symbols\nand another line.')
        self.assertEqual(parse_response('Analysis <box>YES<\\box>'), 'YES')
        self.assertTrue(decision(parse_response('<BOX>yes</BOX>')))

    def test_missing_empty_ambiguous_and_old_formats_rejected(self):
        for raw in ('NAME: A', '<box>unfinished', '<box></box>', '<box>A</box><box>B</box>',
                    '</box>A<box>', '<final>NAME: A</final>', '<final_json>{}</final_json>'):
            with self.subTest(raw=raw), self.assertRaises(SchemaError):
                parse_response(raw)

    def test_single_verdict_and_missing_description(self):
        self.assertFalse(decision('NO'))
        self.assertIsNone(gap_answer('NONE'))
        self.assertEqual(gap_answer('Missing continuous structures'), 'Missing continuous structures')
        for answer in ('YES because...', 'TRUE', 'YES\nNO'):
            with self.assertRaises(SchemaError):
                decision(answer)
        for answer in ('YES', 'NO', 'NONE'):
            with self.assertRaises(SchemaError):
                description(answer)

    def test_prompt_has_one_answer_no_field_matrix(self):
        builder = TreeBuilder(None)
        task = prompts.propose(builder.root, 1)
        self.assertIn('just ONE', task)
        for label in ('NAME:', 'SCOPE:', 'DISTINCTION:', 'PRINCIPLE:', 'PAIR:'):
            self.assertNotIn(label, task + prompts.SYSTEM)
        self.assertIn('fewer than 30%', prompts.SYSTEM)


class FlowTests(unittest.TestCase):
    def test_incremental_build_and_double_no_use_same_input(self):
        client = Script(happy()); builder = TreeBuilder(client)
        self.assertTrue(builder.build())
        self.assertEqual(len(builder.root['children']), 2)
        self.assertTrue(all(c['children'] for c in builder.root['children']))
        self.assertEqual(builder.root['children'][0]['scope'], 'Region A')
        self.assertTrue(all(n == 2 for n in builder.status['coverage_no'].values()))
        calls = dict(client.calls)
        self.assertEqual(calls['root/coverage/2/0'], calls['root/coverage/2/1'])
        self.assertNotEqual(calls['root/coverage/1/0'], calls['root/coverage/2/0'])

    def test_no_yes_resets_confirmation_after_addition(self):
        values = happy(); values['root/coverage/1/0'] = 'NONE'
        values['root/coverage/1/1'] = 'Missing B'
        snapshots = []
        builder = TreeBuilder(Script(values), checkpoint=lambda r, s: snapshots.append(deepcopy(s)))
        self.assertTrue(builder.build())
        counts = [s['coverage_no'].get('root') for s in snapshots]
        self.assertIn(0, counts[counts.index(1)+1:])
        self.assertEqual(builder.status['coverage_no']['root'], 2)

    def test_repair_one_candidate_preserves_accepted_and_passes_review(self):
        values = happy(); values['root/candidate/2/audit/0'] = 'NO'
        values.update({'root/candidate/2/repair/0': 'Improved B', 'root/candidate/2/audit/1': 'YES'})
        client = Script(values); builder = TreeBuilder(client)
        self.assertTrue(builder.build())
        self.assertEqual([c['scope'] for c in builder.root['children']], ['Region A', 'Improved B'])
        self.assertIn('<box>NO</box>', dict(client.calls)['root/candidate/2/repair/0'])

    def test_duplicate_candidate_can_be_repaired_without_another_judge(self):
        values = happy(); values['root/candidate/2/propose'] = 'Region A'
        values.update({'root/candidate/2/repair/0': 'Distinct B', 'root/candidate/2/audit/1': 'YES'})
        client = Script(values); builder = TreeBuilder(client)
        self.assertTrue(builder.build())
        self.assertNotIn('root/candidate/2/audit/0', dict(client.calls))

    def test_last_repair_must_receive_a_third_review(self):
        values = happy(); values['root/candidate/1/audit/0'] = 'NO'
        values.update({'root/candidate/1/repair/0': 'Revised A', 'root/candidate/1/audit/1': 'NO',
                       'root/candidate/1/repair/1': 'Final A', 'root/candidate/1/audit/2': 'YES'})
        client = Script(values); builder = TreeBuilder(client)
        self.assertTrue(builder.build())
        self.assertEqual(builder.root['children'][0]['scope'], 'Final A')
        self.assertIn('root/candidate/1/audit/2', dict(client.calls))

    def test_stalled_repair_and_repeated_gap_stop(self):
        values = happy(); values['root/candidate/1/audit/0'] = 'NO'
        values['root/candidate/1/repair/0'] = 'Region A'
        builder = TreeBuilder(Script(values)); self.assertFalse(builder.build())
        self.assertEqual(builder.status['parents']['root'], 'stalled_duplicate_candidate')
        values = happy(); values['root/coverage/2/0'] = values['root/coverage/1/0']
        builder = TreeBuilder(Script(values)); self.assertFalse(builder.build())
        self.assertEqual(builder.status['parents']['root'], 'stalled_repeated_gap')

    def test_candidate_budget_and_actual_width_limit_are_unresolved(self):
        values = happy(); values['root/candidate/1/audit/0'] = 'NO'
        builder = TreeBuilder(Script(values), max_repairs=0); self.assertFalse(builder.build())
        self.assertFalse(builder.root['children'])
        client = Script(happy()); builder = TreeBuilder(client, max_children_per_parent=1)
        self.assertFalse(builder.build())
        self.assertNotIn('root/candidate/2/propose', dict(client.calls))
        self.assertEqual(builder.status['parents']['root'], 'children_limit_exhausted')

    def test_global_no_is_unresolved_not_an_unchecked_repair(self):
        values = happy(); values['global/audit'] = 'NO'
        builder = TreeBuilder(Script(values)); self.assertFalse(builder.build())
        self.assertEqual(builder.status['global'], 'unresolved')

    def test_one_no_before_call_budget_cannot_freeze(self):
        with tempfile.TemporaryDirectory() as d:
            client = StructuredClient(Backend([boxed(s) for s in ('Criterion', 'A', 'YES', 'NONE')]), d, max_calls=4)
            builder = TreeBuilder(client); self.assertFalse(builder.build())
            self.assertEqual(builder.status['coverage_no']['root'], 1)
            self.assertEqual(builder.status['stop_reason'], 'call_budget_exhausted')


class RuntimeTests(unittest.TestCase):
    def test_full_tree_reconstruction_reuses_same_state_requests(self):
        with tempfile.TemporaryDirectory() as d:
            original = TreeBuilder(StructuredClient(Backend([boxed(s) for s in happy().values()]), d))
            self.assertTrue(original.build())
            resumed = TreeBuilder(StructuredClient(Backend([]), d))
            self.assertTrue(resumed.build())
            self.assertEqual(resumed.root, original.root)
            self.assertEqual(resumed.status, original.status)

    def test_parse_retry_raw_persistence_and_resume(self):
        with tempfile.TemporaryDirectory() as d:
            backend = Backend(['unbounded list without box', boxed('A')])
            client = StructuredClient(backend, d)
            self.assertEqual(client.request('x', 'Describe one family', description), 'A')
            self.assertEqual(len(set(backend.seeds)), 2)
            rows = [json.loads(p.read_text()) for p in sorted((Path(d)/'requests').glob('*/attempt_*.json'))]
            self.assertEqual(rows[0]['raw_completion'], 'unbounded list without box')
            self.assertEqual(rows[1]['box_answer'], 'A')
            resumed = StructuredClient(Backend([]), d)
            self.assertEqual(resumed.request('x', 'Describe one family', description), 'A')
            self.assertEqual(resumed.last_raw_completion, boxed('A'))

    def test_retry_budget_persists(self):
        with tempfile.TemporaryDirectory() as d:
            client = StructuredClient(Backend(['bad']*3), d)
            with self.assertRaises(ParseRetriesExhausted): client.request('x', 'Task', description)
            with self.assertRaises(ParseRetriesExhausted): StructuredClient(Backend([]), d).request('x', 'Task', description)

    def test_plain_base_completion_prefills_analysis_and_stops_at_box(self):
        backend = object.__new__(run.VLLMBackend)
        backend.args = types.SimpleNamespace(max_new_tokens=8192,max_model_len=32768,temperature=.6,top_p=.95)
        backend.tokenizer = types.SimpleNamespace(encode=lambda *a, **k: [1])
        captured = {}
        def sampling(**kwargs): captured.update(kwargs); return kwargs
        backend.sampling_class = sampling
        def generate(inputs, **kwargs):
            self.assertTrue(inputs[0].endswith('Response:\n<analysis>\n'))
            self.assertNotIn('<|im_start|>', inputs[0])
            completion = types.SimpleNamespace(text='Reasoning</analysis><box>YES</box>', token_ids=[1], finish_reason='stop')
            return [types.SimpleNamespace(outputs=[completion])]
        backend.model = types.SimpleNamespace(generate=generate)
        output = backend.generate(prompts.SYSTEM, 'One judgment', 1)
        self.assertEqual(captured['stop'], ['</box>', '<\\box>'])
        self.assertTrue(captured['include_stop_str_in_output'])
        self.assertTrue(decision(parse_response(output['raw_completion'])))

    def test_cli_json_artifacts_and_resume_fingerprint(self):
        with tempfile.TemporaryDirectory() as d:
            model = Path(d)/'model'; model.mkdir()
            out = Path(d)/'output'; args = ['--model', str(model), '--output-dir', str(out)]
            backend = Backend([boxed(s) for s in happy().values()])
            modules = {k: types.SimpleNamespace(__version__='test') for k in ('vllm','transformers')}
            with patch.object(run,'VLLMBackend', return_value=backend), patch.dict('sys.modules',modules):
                self.assertEqual(run.main(args),0)
            self.assertTrue((out/'tree.json').exists())
            self.assertTrue((out/'tree.md').exists())
            manifest = json.loads((out/'manifest.json').read_text())
            self.assertEqual(manifest['config']['prompt_version'], 'scope-tree-v4-single-answer')
            with patch.object(run,'VLLMBackend',side_effect=AssertionError('no model needed')):
                self.assertEqual(run.main(args+['--resume']),0)
            with self.assertRaisesRegex(ValueError,'fingerprint'):
                run.main(args+['--resume','--seed','8'])

    def test_cli_global_failure_does_not_publish_tree(self):
        with tempfile.TemporaryDirectory() as d:
            model = Path(d)/'model'; model.mkdir(); out=Path(d)/'output'
            values=happy(); values['global/audit']='NO'
            modules = {k: types.SimpleNamespace(__version__='test') for k in ('vllm','transformers')}
            with patch.object(run,'VLLMBackend',return_value=Backend([boxed(s) for s in values.values()])), patch.dict('sys.modules',modules):
                self.assertEqual(run.main(['--model',str(model),'--output-dir',str(out)]),2)
            self.assertFalse((out/'tree.json').exists())
            self.assertTrue((out/'partial_tree.json').exists())


if __name__ == '__main__':
    unittest.main()
