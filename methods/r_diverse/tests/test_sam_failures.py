import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

from methods.r_diverse.core import read_json, write_json
from methods.r_diverse.inference import sam
from methods.r_diverse.reward import compute_score
from methods.r_diverse.run import prepare_dataset
from methods.r_diverse.gpu_worker import generate


class SamFailureTests(unittest.TestCase):
    def test_retry_only_failed_cache_success_and_count_duplicate_failures(self):
        calls = []
        def worker(mode, rows, model, gpus, cfg, work):
            attempt = cfg.get('sam_retry_attempt', 0)
            calls.append((mode, attempt, [r['question'] for r in rows]))
            if mode == 'code':
                return [dict(r, sam_ok=(r['question'] == 'good' or (r['question'] == 'retry' and attempt > 0)),
                             retry_attempt=attempt, code='def solver(): return 1') for r in rows]
            self.assertTrue(all(r['sam_ok'] for r in rows))
            return [dict(r, embedding=[1., float(r['question'] == 'retry')]) for r in rows]
        with tempfile.TemporaryDirectory() as tmp:
            cfg = dict(run_root=tmp, coder_model='coder', embedding_model='encoder', code_tokens=2048, embedding_tokens=4096)
            with patch('methods.r_diverse.inference.run_workers', worker):
                vectors, records = sam(['good', 'fail', 'retry', 'good'], cfg, ['0'], tmp)
                self.assertEqual(calls[1], ('code', 1, ['fail', 'retry']))
                self.assertEqual(vectors.shape, (3, 2))
                self.assertEqual([r['sam_ok'] for r in records], [True, False, True, True])
                np.testing.assert_array_equal(vectors, [[1, 0], [1, 1], [1, 0]])
                self.assertEqual(read_json(Path(tmp) / 'sam_summary.json')['failed_rows'], 1)
                self.assertEqual(len(list((Path(tmp) / 'sam_cache').glob('*.json'))), 2)
                calls.clear()
                sam(['good', 'retry'], cfg, ['0'], tmp)
                self.assertEqual(calls, [])
                vectors, records = sam(['fail', 'fail', 'good'], cfg, ['0'], tmp)
                self.assertEqual(vectors.shape, (1, 2))
                self.assertEqual([r['sam_ok'] for r in records], [False, False, True])
                summary = read_json(Path(tmp) / 'sam_summary.json')
                self.assertTrue(summary['failure_threshold_exceeded'])
                self.assertFalse(summary['strict_failures'])
                with self.assertRaisesRegex(RuntimeError, '2/3'):
                    sam(['fail', 'fail', 'good'], dict(cfg, sam_strict_failures=True), ['0'], tmp)
                with self.assertRaisesRegex(RuntimeError, '1/1'):
                    sam(['fail'], cfg, ['0'], tmp)

    def test_mixed_reward_preserves_order_and_uses_conservative_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp); cfg = p/'config.json'; memory = p/'memory.npy'
            write_json(cfg, {'feedback_gpus': ['2'], 'seed': 1})
            np.save(memory, [[1., 0.]])
            records = [{'key': 'a', 'sam_ok': True}, {'key': 'b', 'sam_ok': False}, {'key': 'c', 'sam_ok': True}]
            evaluated = [{'score': .5}, {'score': .3}, {'score': .2}]
            with patch('methods.r_diverse.reward.run_workers', return_value=evaluated), patch(
                'methods.r_diverse.reward.sam', return_value=(np.array([[1.,0.],[0.,1.]]), records)):
                scores = compute_score(['bad'] + [f'<question>{q}</question>\\boxed{{1}}' for q in 'abc'],
                                       [], cfg, 'solver', memory, p)
            self.assertEqual([r['format'] for r in scores], [0,1,1,1])
            self.assertEqual([r['sam_failed'] for r in scores], [0,0,1,0])
            np.testing.assert_allclose([r['overall'] for r in scores], [-2., -.625, -1.325, -.3])
            rows = read_json(next(p.glob('reward_*'))/'questions.json')
            self.assertEqual([r['original_index'] for r in rows], [1,2,3])

    def test_dataset_memory_vectors_and_rows_remain_aligned(self):
        class FakeDataset:
            @staticmethod
            def from_list(rows):
                return SimpleNamespace(to_parquet=lambda path: write_json(path, rows))
        current = [dict(question=q, answer='1', score=.5, source_id=q) for q in 'abc']
        records = [dict(key=q, sam_ok=q!='b', code_tags_ok=True, code_syntax_ok=True, code_truncated=False) for q in 'abc']
        history = [dict(question='old', answer='2', score=.4, sam_key='old')]
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'round_2';p.mkdir()
            with patch.dict('sys.modules', datasets=SimpleNamespace(Dataset=FakeDataset)), patch(
                'methods.r_diverse.run.sam', return_value=(np.array([[1.,0.],[0.,1.]]), records)):
                prepare_dataset(p, {'all_gpus':['0'], 'seed':1, 'rollout_batch':1}, current, history, np.array([[.5,.5]]))
            self.assertEqual([r['question'] for r in read_json(p/'memory_rows.json')], ['old','a','c'])
            np.testing.assert_array_equal(np.load(p/'memory.npy'), [[.5,.5],[1,0],[0,1]])
            self.assertEqual(read_json(p/'dataset_summary.json')['sam_failed_rows'], 1)
            self.assertEqual({r['problem'] for r in read_json(p/'solver.parquet')}, {'a','c'})

    def test_retry_prefill_is_reconstructed_and_budget_grows(self):
        seen = {}
        class LLM:
            def __init__(self, **kwargs): pass
            def generate(self, prompts, params, **kwargs):
                seen.update(prompts=prompts, params=params)
                return [SimpleNamespace(outputs=[SimpleNamespace(text='n1=17):\n    return n1**2\n</CODE>', finish_reason='stop')])]
        tokenizer=SimpleNamespace(chat_template=None, encode=lambda *a, **k: [1]*100)
        with patch.dict('sys.modules', vllm=SimpleNamespace(LLM=LLM, SamplingParams=lambda **k:k),
                        transformers=SimpleNamespace(AutoTokenizer=SimpleNamespace(from_pretrained=lambda *a:tokenizer))):
            rows=generate(dict(mode='code', model='coder', seed=1, rows=[{'id':0,'question':'square 17'}],
                               config=dict(inference_memory=.8, inference_context=8192, inference_batch=1,
                                           code_tokens=2048, sam_retry_attempt=1)))
        self.assertEqual(seen['params']['max_tokens'],4096)
        self.assertTrue(seen['prompts'][0].endswith('<CODE>\ndef solver('))
        self.assertEqual(rows[0]['code'], 'def solver(n1=17):\n    return n1**2')
        self.assertTrue(rows[0]['sam_ok'])


if __name__ == '__main__': unittest.main()
