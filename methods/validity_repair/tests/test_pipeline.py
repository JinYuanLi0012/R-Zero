import copy
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pipeline as p
from protocol import accepted, apply_edits


def proposal(old='3', new='4'):
    return {'decision': 'proposed', 'defect': 'bad parameter',
            'edits': [{'old': old, 'new': new, 'reason': 'local correction'}], 'check_summary': 'checked'}


def review(**updates):
    value = {'original_label': 'D', 'repaired_label': 'A', 'same_objects': True, 'same_target': True,
             'same_task_type': True, 'local_edit': True, 'no_answer_or_hint_added': True,
             'no_core_constraint_removed': True, 'confidence': 0.9, 'check_summary': 'independent check'}
    return {**value, **updates}


def complete(result):
    return {'status': 'complete', 'result': result}


def response(key, result, status='completed'):
    return {'custom_id': key, 'response': {'status_code': 200, 'body': {
        'status': status, 'output': [{'type': 'message', 'content': [
            {'type': 'output_text', 'text': json.dumps(result)}]}]}}}


class FakeClient:
    def __init__(self, results, interrupt=False):
        self.results, self.interrupt = results, interrupt
        self.files = SimpleNamespace(create=self.upload, content=self.content)
        self.batches = SimpleNamespace(create=self.create, retrieve=self.retrieve)
        self.uploads = self.creates = 0
        self.rows = []

    def upload(self, file, purpose):
        self.uploads += 1
        self.rows = [json.loads(line) for line in file]
        return SimpleNamespace(id='file-input')

    def create(self, **kwargs):
        self.creates += 1
        return SimpleNamespace(id='batch-test', model_dump=lambda **kw: {'id': 'batch-test'})

    def retrieve(self, key):
        if self.interrupt:
            self.interrupt = False
            raise ConnectionError('simulate interruption after submission')
        return {'id': key, 'status': 'completed', 'request_counts': {'completed': len(self.rows), 'total': len(self.rows)},
                'output_file_id': 'file-output', 'error_file_id': None}

    def content(self, key):
        # Deliberately reverse output order. Omitted results simulate missing requests.
        lines = [response(r['custom_id'], self.results[r['custom_id'].split(':')[1]])
                 for r in reversed(self.rows) if r['custom_id'].split(':')[1] in self.results]
        return SimpleNamespace(text='\n'.join(json.dumps(x) for x in lines))


class Tests(unittest.TestCase):
    def test_exact_edits_and_disjoint_original_spans(self):
        r = proposal('x=3', 'x=4')
        r['edits'].append({'old': 'y=4', 'new': 'y=5', 'reason': 'second'})
        self.assertEqual(apply_edits('x=3; y=4.', r), 'x=4; y=5.')
        for q, bad in [('3+3', proposal()), ('x', proposal()), ('3', proposal('3', '3'))]:
            with self.assertRaises(ValueError):
                apply_edits(q, bad)
        r['edits'][1]['old'] = '=3'
        with self.assertRaises(ValueError):
            apply_edits('x=3; y=4.', r)

    def test_abstention_and_schema(self):
        r = proposal()
        r['decision'] = 'uncertain'
        with self.assertRaises(ValueError):
            apply_edits('3', r)
        r['edits'] = []
        self.assertEqual(apply_edits('3', r), '3')
        with self.assertRaises(ValueError):
            accepted(review(same_objects='true'))
        with self.assertRaises(ValueError):
            accepted(review(confidence=float('nan')))

    def test_review_gates(self):
        self.assertTrue(accepted(review()))
        for update in ({'original_label': 'A'}, {'original_label': 'F'}, {'repaired_label': 'C'},
                       {'confidence': 0.79}, {'same_target': False}, {'local_edit': False},
                       {'no_answer_or_hint_added': False}, {'no_core_constraint_removed': False}):
            self.assertFalse(accepted(review(**update)))

    def test_batch_parse_rejects_incomplete_and_invalid_patch(self):
        item = {'id': 'q1', 'question': 'x=3'}
        with self.assertRaises(ValueError):
            p.parse_line(response('repair:q1:a1', proposal(), 'incomplete'), item, 'repair')
        with self.assertRaises(ValueError):
            p.parse_line(response('repair:q1:a1', proposal('missing')), item, 'repair')

    def test_blind_review_has_no_repair_rationale_or_source_labels(self):
        items = [{'id': 'q1', 'question': '3'}]
        reviews = p.proposals(items, {'q1': complete(proposal())})
        self.assertEqual(set(reviews[0]), {'id', 'original_question', 'repaired_question'})
        body = p.request(reviews[0], 'review', 'gpt-5.6-sol', 'high', 16384)['body']
        sent = json.loads(body['input'][1]['content'])
        self.assertNotIn('defect', sent)
        self.assertNotIn('terra_validity', sent)
        self.assertEqual(body['reasoning'], {'effort': 'high'})

    def test_batch_resume_out_of_order_and_one_attempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            items = [{'id': 'q1', 'question': '3'}, {'id': 'q2', 'question': '5'}, {'id': 'q3', 'question': '7'}]
            abstain = {'decision': 'unrepairable', 'defect': 'large change', 'edits': [], 'check_summary': 'checked'}
            client = FakeClient({'q1': proposal(), 'q2': abstain}, interrupt=True)
            args = (client, items, 'repair', out, 'gpt-5.6-sol', 'high', 16384, 5)
            with self.assertRaises(ConnectionError):
                p.run_stage(*args)
            results = p.run_stage(*args)
            self.assertEqual(results['q1']['result']['decision'], 'proposed')
            self.assertEqual(results['q2']['result']['decision'], 'unrepairable')
            self.assertEqual(results['q3']['status'], 'failed')
            again = p.run_stage(*args)
            self.assertEqual(results, again)
            self.assertEqual((client.uploads, client.creates), (1, 1))
            with self.assertRaises(RuntimeError):
                p.run_stage(client, items, 'repair', out, 'other-model', 'high', 16384, 5)

    def test_prepare_and_paired_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            rows = [{'id': f'q{i}', 'question': f'Question {i}: x=3', 'round': 'v1', 'split': 'train',
                     'terra_validity': 'VALID' if i == 0 else 'INVALID',
                     'canonical_final_answer': 'SECRET ANSWER', 'validity_rl_target': 'INVALID'} for i in range(5)]
            src = out / 'source.jsonl'
            p.write_jsonl(src, rows)
            clean, items, config = p.prepare(src, out, 0, 42, 5)
            self.assertNotIn('canonical_final_answer', clean[0])
            repairs = {'q1': complete(proposal('x=3', 'x=4')),
                       'q2': complete(proposal('x=3', 'x=4')),
                       'q3': {'status': 'failed', 'result': None},
                       'q4': complete({'decision': 'already_valid', 'defect': '', 'edits': [], 'check_summary': 'ok'})}
            reviews = {'q1': complete(review()), 'q2': complete(review(same_target=False))}
            stats = p.finalize(clean, items, repairs, reviews, out, 0.8)
            a, b = [p.read_jsonl(out / name) for name in ('original_questions.jsonl', 'repaired_questions.jsonl')]
            self.assertEqual(len(a), 5)
            self.assertEqual([r['id'] for r in a], [r['id'] for r in b])
            self.assertEqual(stats['accepted_repairs'], 1)
            self.assertEqual(stats['nominal_repaired_valid_rate'], 0.4)
            for i in (0, 2, 3, 4):
                self.assertEqual(a[i], b[i])
            self.assertEqual(b[1]['question'], 'Question 1: x=4')
            self.assertTrue(all(set(r) == {'id', 'question', 'round', 'split'} for r in a+b))
            with self.assertRaises(ValueError):
                p.prepare(src, out, 1, 42, 5)
            rows[0]['split'] = 'validation'
            p.write_jsonl(src, rows)
            with self.assertRaises(ValueError):
                p.prepare(src, out / 'bad', 0, 42, 5)

    def test_cli_end_to_end_and_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            source = directory / 'input.jsonl'
            p.write_jsonl(source, [
                {'id': 'q1', 'question': 'x=3', 'round': 'v1', 'split': 'train', 'terra_validity': 'INVALID'},
                {'id': 'q2', 'question': 'Compute 2+2', 'round': 'v2', 'split': 'train', 'terra_validity': 'VALID'}])
            class Router(FakeClient):
                def content(self, key):
                    stage = self.rows[0]['custom_id'].split(':')[0]
                    self.results = {'q1': proposal() if stage == 'repair' else review()}
                    return super().content(key)
            client = Router({})
            argv = ['pipeline.py', '--input', str(source), '--output-dir', str(directory / 'run'), '--expected-count', '2']
            with patch.object(sys, 'argv', argv), patch.dict(p.os.environ, {'OPENAI_API_KEY': 'fake'}), patch.dict(sys.modules, {'openai': SimpleNamespace(OpenAI=lambda: client)}):
                p.main()
                p.main()
            self.assertEqual(client.creates, 2)
            stats = json.loads((directory / 'run/analysis/statistics.json').read_text())
            self.assertEqual(stats['accepted_repairs'], 1)
            self.assertFalse(stats['training_labels_generated'])

    def test_smoke_is_deterministic_and_retains_unselected(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            rows = [{'id': f'q{i}', 'question': f'Question {i}', 'round': 'v1', 'split': 'train',
                     'terra_validity': 'INVALID'} for i in range(10)]
            src = out / 'input.jsonl'
            p.write_jsonl(src, rows)
            clean, items, _ = p.prepare(src, out / 'a', 2, 42, 10)
            _, other, _ = p.prepare(src, out / 'b', 2, 42, 10)
            self.assertEqual(items, other)
            repairs = {i['id']: {'status': 'failed', 'result': None} for i in items}
            stats = p.finalize(clean, items, repairs, {}, out / 'a', 0.8)
            self.assertEqual(stats['status_counts']['not_selected'], 8)
            self.assertEqual(p.read_jsonl(out / 'a/original_questions.jsonl'), p.read_jsonl(out / 'a/repaired_questions.jsonl'))


if __name__ == '__main__':
    unittest.main()
