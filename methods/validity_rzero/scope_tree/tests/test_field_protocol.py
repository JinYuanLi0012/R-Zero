"""Field transport, real malformed outputs, and semantic gate regressions (CPU only)."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import types
import unittest

from methods.validity_rzero.scope_tree import prompts
from methods.validity_rzero.scope_tree.core import (
    SchemaError, TreeBuilder, apply_repair, parse_response, response_diagnostics,
    validate_audit, validate_global,
    validate_global_addition, validate_proposal,
)
from methods.validity_rzero.scope_tree.run import StructuredClient, VLLMBackend
from methods.validity_rzero.scope_tree.tests.test_scope_tree import (
    FakeBackend, audit, child, clean_script, coverage, node, proposal, repair,
)


def line(key, value):
    return key + ': ' + str(value).replace('\n', '\n  ')


def family_lines(value):
    return [line(k, value[v]) for k, v in (('NAME', 'name'), ('SCOPE', 'scope'), ('DISTINCTION', 'distinguishing_feature'))]


def field_wrapped(value):
    """Fixture encoder only. Production has no model-response rewriting or field deletion."""
    if 'partition_principle' in value:
        lines = [line('PRINCIPLE', value['partition_principle'])]
        if 'children' in value:
            for c in value['children']:
                lines += family_lines(c)
        else:
            for r in value['replacements']:
                lines += [line('REPLACE', r['id']), line('ACTION', 'DELETE' if r['child'] is None else 'REPLACE')]
                if r['child'] is not None:
                    lines += family_lines(r['child'])
    elif 'principle_ok' in value:
        lines = [line('PRINCIPLE_OK', 'YES' if value['principle_ok'] else 'NO'), line('PRINCIPLE_REASON', value['principle_feedback'])]
        for r in value['children']:
            lines += [line('CHILD', r['id'])]
            for label, key in [('FIT', 'fits_parent'), ('AXIS', 'follows_principle'), ('BREADTH', 'comparable_breadth'), ('READY', 'generation_ready')]:
                if key in r:
                    lines += [line(label, 'YES' if r[key] else 'NO')]
            lines += [line('ACTION', r['action']), line('REASON', r['reason'])]
        for r in value['pairs']:
            lines += [line('PAIR', r['a'] + ' ' + r['b']), line('RELATION', r['relation']), line('REASON', r['reason'])]
    elif 'has_major_gap' in value:
        lines = [line('HAS_MAJOR_GAP', 'YES' if value['has_major_gap'] else 'NO'),
                 line('GAP', value['gap_description'] if value['has_major_gap'] else 'NONE'), line('REASON', value['reason'])]
    elif 'issues' in value:
        lines = [] if value['issues'] else ['ISSUES: NONE']
        for r in value['issues']:
            lines += [line('PAIR', r['a'] + ' ' + r['b']), line('RELATION', r['relation']), line('REVISE', r['revise_id']), line('REASON', r['reason'])]
    else:
        lines = [line('PARENT', value['parent_id'])] if 'parent_id' in value else []
        lines += family_lines(value['child'])
    return 'Compare the mathematical ranges and their boundaries.\n<final>\n' + '\n'.join(lines) + '\n</final>'


class FieldBackend(FakeBackend):
    def generate(self, system, user, seed):
        self.seeds.append(seed)
        value = self.outputs.pop(0)
        return {'raw_completion': value if isinstance(value, str) else field_wrapped(value), 'finish_reason': 'stop'}


class FieldProtocolTests(unittest.TestCase):
    def test_every_action_decodes_to_unchanged_internal_schema(self):
        issue = {'a': '1.1', 'b': '2.1', 'relation': 'NESTED', 'revise_id': '2.1', 'reason': 'Same structures'}
        values = [proposal(['A', 'B']), audit(['1', '2']), audit(['1.1', '1.2']),
                  coverage(), coverage('A substantial missing region'), repair({'2': child('B'), '3': None}),
                  {'child': child('C')}, {'parent_id': 'root', 'child': child('D')},
                  {'issues': []}, {'issues': [issue]}]
        for value in values:
            with self.subTest(keys=list(value)):
                self.assertEqual(parse_response(field_wrapped(value)), value)

    def test_literal_colons_quotes_bars_and_indented_multiline_values(self):
        raw = '''Analysis.
<final>
PRINCIPLE: Primary relation: equality | inequality
NAME: "Family: A | B"
SCOPE: Constraints: x:y = 2:3; |x| > 1.
  The next line includes a literal field-looking string:
  NAME: this is scope text, not another record
DISTINCTION: Coupled conditions: not just constants.
</final>'''
        result = validate_proposal(parse_response(raw))
        self.assertEqual(len(result['children']), 1)
        self.assertIn('\nNAME: this is scope text', result['children'][0]['scope'])
        self.assertEqual(result['children'][0]['name'], '"Family: A | B"')

    def test_missing_duplicate_unknown_out_of_order_and_ambiguous_blocks_fail(self):
        valid = field_wrapped({'child': child('A')})
        bad = [valid.replace('SCOPE: Scope of A\n', ''),
               valid.replace('SCOPE: Scope of A', 'SCOPE: Scope of A\nSCOPE: Duplicate'),
               valid.replace('NAME: A', 'NAME: A\nPARENT_ID: root'),
               valid.replace('NAME: A', 'SCOPE: Wrong order'),
               valid.replace('SCOPE: Scope of A', 'unindented continuation'),
               valid.replace('NAME: A', 'NAME: '),
               valid.replace('</final>', ''), valid + valid,
               valid + '<final_json>{}</final_json>',
               '<final>ISSUES: NONE</final>',
               'Reason. <final>{"child": {}}</final>']
        for raw in bad:
            with self.subTest(raw=raw), self.assertRaises(SchemaError):
                parse_response(raw)

    def test_boolean_and_none_contradictions_fail(self):
        for body in ('HAS_MAJOR_GAP: false\nGAP: NONE\nREASON: X',
                     'HAS_MAJOR_GAP: NO\nGAP: A gap\nREASON: X',
                     'HAS_MAJOR_GAP: YES\nGAP: NONE\nREASON: X',
                     'HAS_MAJOR_GAP: YES\nREASON: X', 'ISSUES: YES'):
            with self.subTest(body=body), self.assertRaises(SchemaError):
                parse_response('Reason. <final>\n' + body + '\n</final>')

    def test_id_pair_breadth_readiness_and_decision_checks_survive_text_decode(self):
        children = [node('1.1', 'A'), node('1.2', 'B')]
        good = audit(['1.1', '1.2'])
        bad = []
        missing = deepcopy(good); missing['pairs'] = []; bad.append(missing)
        duplicate = deepcopy(good); duplicate['pairs'] *= 2; bad.append(duplicate)
        duplicate_child = deepcopy(good); duplicate_child['children'].append(deepcopy(good['children'][0])); bad.append(duplicate_child)
        unknown = deepcopy(good); unknown['children'][0]['id'] = '9.9'; bad.append(unknown)
        for key in ('generation_ready', 'comparable_breadth', 'follows_principle', 'fits_parent'):
            failed = deepcopy(good); failed['children'][0][key] = False; bad.append(failed)
        overlapping = deepcopy(good); overlapping['pairs'][0]['relation'] = 'OVERLAP'; bad.append(overlapping)
        missing_ready = deepcopy(good); del missing_ready['children'][0]['generation_ready']; bad.append(missing_ready)
        for value in bad:
            with self.subTest(value=value), self.assertRaises(SchemaError):
                validate_audit(parse_response(field_wrapped(value)), children, 2)
        validate_audit(parse_response(field_wrapped(good)), children, 2)

    def test_repair_conflicts_extra_additions_and_duplicate_names_fail(self):
        children = [node('1', 'A'), node('2', 'B')]
        parent = {'id': 'root', 'partition_principle': 'Shared structural axis'}
        feedback = audit(['1', '2'], revise=['2'])
        for value in (repair({'1': child('Changed accepted')}), repair({'2': child('A')})):
            with self.assertRaises(SchemaError):
                apply_repair(parse_response(field_wrapped(value)), parent, children, feedback, 1)
        raw = field_wrapped(repair({'2': child('Fixed')}))
        with self.assertRaises(SchemaError):
            parse_response(raw.replace('</final>', 'NAME: Extra\nSCOPE: X\nDISTINCTION: Y\n</final>'))
        with self.assertRaises(SchemaError):
            apply_repair(parse_response(raw.replace('REPLACE: 2', 'REPLACE: 9')), parent, children, feedback, 1)
        valid = apply_repair(parse_response(raw), parent, children, feedback, 1)
        self.assertEqual(valid['children'][0], children[0])

    def test_global_pair_and_parent_conflicts_fail(self):
        root = TreeBuilder(None).root
        root['children'] = [node('1', 'A')]
        with self.assertRaises(SchemaError):
            validate_global_addition(parse_response(field_wrapped({'parent_id': 'wrong', 'child': child('B')})), root)
        leaves = [node('1.1', 'A'), node('2.1', 'B')]
        bad = {'issues': [{'a': '1.1', 'b': '2.1', 'relation': 'NESTED', 'revise_id': '3.1', 'reason': 'X'}]}
        with self.assertRaises(SchemaError):
            validate_global(parse_response(field_wrapped(bad)), leaves)
        with self.assertRaisesRegex(SchemaError, 'exactly two'):
            parse_response('Reason. <final>PAIR: 1.1 2.1 3.1\nRELATION: NESTED\nREVISE: 2.1\nREASON: X</final>')

    def test_text_transport_full_build_persists_canonical_json_and_resumes(self):
        with tempfile.TemporaryDirectory() as directory:
            backend = FieldBackend(list(clean_script().values()))
            builder = TreeBuilder(StructuredClient(backend, directory))
            self.assertTrue(builder.build())
            self.assertEqual(len(backend.seeds), 15)
            attempts = [json.loads(p.read_text()) for p in (Path(directory) / 'requests').glob('*/attempt_*.json')]
            self.assertTrue(all(a['diagnostics']['final_box_format'] == 'fields' for a in attempts))
            self.assertTrue(all(isinstance(a['parsed_json'], dict) for a in attempts))
            self.assertTrue(TreeBuilder(StructuredClient(FieldBackend([]), directory)).build())

    def test_retry_error_identifies_field_and_stays_in_text_protocol(self):
        good = field_wrapped(proposal(['A']))
        broken = good.replace('DISTINCTION: Feature of A', 'PARENT_ID: root')
        with tempfile.TemporaryDirectory() as directory:
            client = StructuredClient(FieldBackend([broken, good]), directory)
            self.assertEqual(client.request('root/propose', 'Task', validate_proposal), proposal(['A']))
            attempts = [json.loads(p.read_text()) for p in sorted((Path(directory) / 'requests').glob('*/attempt_*.json'))]
            self.assertIn('expected DISTINCTION, found PARENT_ID', attempts[0]['error'])
            self.assertIn('Do not output JSON', attempts[1]['user'])
            self.assertNotIn('complete JSON result', attempts[1]['user'])
            self.assertEqual(attempts[0]['raw_completion'], broken)

    def test_prompt_context_is_semantic_and_new_outputs_have_no_json_template(self):
        root = TreeBuilder(None).root
        children = [node('1', 'A'), node('2', 'B')]
        root['children'] = children
        root['partition_principle'] = 'Shared structural axis'
        generated = [prompts.propose(root, 1), prompts.audit(root, children, 1),
                     prompts.repair(root, children, audit(['1', '2'], revise=['2']), 1),
                     prompts.coverage_check(root, children, 1), prompts.gap_addition(root, children, 1, 'Gap'),
                     prompts.global_audit([]), prompts.global_coverage(root, []), prompts.global_addition(root, [], 'Gap')]
        for text in generated:
            self.assertNotIn('Final JSON', text)
            self.assertNotIn('"children":', text)
            self.assertNotIn('"parent_id":', text)
            self.assertNotIn(prompts.ROOT_SCOPE, text)
        self.assertIn(prompts.ROOT_SCOPE, prompts.SYSTEM)
        self.assertIn('scope', root)  # storage still retains the full definition
        self.assertIn('PRINCIPLE:', generated[0])
        self.assertIn('actual SCOPE and DISTINCTION', generated[1])
        self.assertIn('READY:', prompts.audit(children[0], [node('1.1', 'A')], 2))

    def test_backend_stop_includes_text_and_legacy_close_and_retains_it(self):
        backend = object.__new__(VLLMBackend)
        backend.args = types.SimpleNamespace(max_new_tokens=8192, max_model_len=32768, temperature=0.6, top_p=0.95)
        backend.tokenizer = types.SimpleNamespace(chat_template=None, encode=lambda *a, **k: [1])
        captured = {}
        def sampling(**kwargs):
            captured.update(kwargs)
            return kwargs
        backend.sampling_class = sampling
        completion = types.SimpleNamespace(text='Reason. <final>ISSUES: NONE</final>', token_ids=[1], finish_reason='stop')
        backend.model = types.SimpleNamespace(generate=lambda *a, **k: [types.SimpleNamespace(outputs=[completion])])
        raw = backend.generate(prompts.SYSTEM, 'Audit', 7)
        self.assertEqual(captured['stop'], ['</final>', '</final_json>'])
        self.assertTrue(captured['include_stop_str_in_output'])
        self.assertEqual(parse_response(raw['raw_completion']), {'issues': []})


class RecordedV3Tests(unittest.TestCase):
    def setUp(self):
        self.rows = json.loads((Path(__file__).parent / 'fixtures/root_propose_v3.json').read_text())

    def test_real_failures_do_not_become_success_by_discarding_fields(self):
        self.assertTrue(all(r['finish_reason'] == 'stop' and r['completion_tokens'] < 8192 for r in self.rows))
        with self.assertRaises(SchemaError):
            parse_response(self.rows[0]['raw_completion'])
        missing = parse_response(self.rows[1]['raw_completion'])
        with self.assertRaisesRegex(SchemaError, r"\$: missing=\['partition_principle'\]; extra=\['parent'\]"):
            validate_proposal(missing)
        extra = parse_response(self.rows[2]['raw_completion'])
        for parent_id in ('root', 'wrong'):
            # Neither matching nor conflicting storage metadata is silently stripped.
            value = deepcopy(extra); value['children'][0]['parent_id'] = parent_id
            with self.assertRaisesRegex(SchemaError, r"\$\.children\[0\]: missing=\[\]; extra=\['parent_id'\]"):
                validate_proposal(value)
        info = response_diagnostics(self.rows[2]['raw_completion'])
        self.assertTrue(info['has_nonempty_prefix'])  # draft JSON, not proof of reasoning
        self.assertNotIn('has_analysis_before_final', info)

    def test_synthetic_field_encoding_of_copied_content_still_goes_to_semantic_audit(self):
        recorded = parse_response(self.rows[2]['raw_completion'])
        # Test-only field encoding: real shared content remains unchanged, while
        # storage metadata is deliberately absent in this synthetic model response.
        text = field_wrapped(recorded)
        parsed = parse_response(text)
        self.assertEqual(len({c['distinguishing_feature'] for c in parsed['children']}), 1)
        ids = [str(i + 1) for i in range(len(parsed['children']))]
        review = audit(ids, revise=ids)
        with tempfile.TemporaryDirectory() as directory:
            client = StructuredClient(FieldBackend([text, review]), directory)
            builder = TreeBuilder(client, max_repairs=0)
            self.assertFalse(builder.build())
            self.assertEqual(client.calls, 2)
            self.assertEqual(builder.status['state'], 'unresolved')


if __name__ == '__main__':
    unittest.main()
