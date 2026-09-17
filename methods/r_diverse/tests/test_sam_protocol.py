import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from methods.r_diverse.gpu_worker import generate
from methods.r_diverse.inference import sam
from methods.r_diverse.sam_protocol import code_prompt, extract_code


class SamProtocolTests(unittest.TestCase):
    def test_base_prefill_ignores_even_present_chat_template(self):
        tokenizer = SimpleNamespace(chat_template='must not be used')
        prompt = code_prompt('Compute 17 squared.', tokenizer)
        self.assertTrue(prompt.endswith('Input Question: Compute 17 squared.\nOutput:\n<CODE>\n'))

    def test_prefilled_and_full_block(self):
        body = 'def solver(n1=17):\n    return n1 ** 2'
        self.assertEqual(extract_code(body + '\n</CODE>'), body)
        self.assertEqual(extract_code('<CODE>\n' + body + '\n</CODE>'), body)
        self.assertEqual(extract_code('<CODE>\n' + body + '\n</CODE>', 'chat'), body)

    def test_real_echo_shape_is_rejected_not_salvaged(self):
        # Regression: the observed response repeats this prefix of the paper prompt.
        template = Path(__file__).parents[1].joinpath('code_prompt.txt').read_text()
        echo = template[:template.index('</CODE>') + len('</CODE>')]
        for mode in ['completion', 'chat']:
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                extract_code(echo, mode)

    def test_no_raw_output_fallback_or_nested_block(self):
        for raw in ['Some prose', '<CODE></CODE>',
                    '<CODE>instructions <CODE>def solver(): return 8</CODE>',
                    '<CODE>def solver(): return 1</CODE>\nextra prose']:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                extract_code(raw)

    def test_missing_closer_recovers_only_complete_solver_and_never_truncation(self):
        body = 'import math\ndef solver(n1=2):\n    return math.sqrt(n1)'
        self.assertEqual(extract_code(body), body)
        self.assertEqual(extract_code('<CODE>\n' + body), body)
        for raw in ['def solver():', 'print(8)', 'def other(): return 8']:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                extract_code(raw)
        with self.assertRaises(ValueError):
            extract_code(body, truncated=True)

    def test_syntax_is_not_a_math_validity_gate(self):
        # Framed but syntactically incorrect code is still represented, as documented.
        self.assertEqual(extract_code('def solver(:\n    return 1\n</CODE>'),
                         'def solver(:\n    return 1')

    def test_chat_requires_template(self):
        with self.assertRaises(ValueError):
            code_prompt('question', SimpleNamespace(chat_template=None), 'chat')

    def test_worker_preserves_failed_row_and_continues(self):
        prompts = []
        template = Path(__file__).parents[1].joinpath('code_prompt.txt').read_text()
        echo = template[:template.index('</CODE>') + len('</CODE>')]
        class FakeLLM:
            def __init__(self, **kwargs):
                pass
            def generate(self, batch, params, **kwargs):
                prompts.extend(batch)
                text = 'def solver(): return 17\n</CODE>' if len(prompts) == 1 else echo
                return [SimpleNamespace(outputs=[SimpleNamespace(text=text, finish_reason='stop')])]
        fake_vllm = SimpleNamespace(LLM=FakeLLM, SamplingParams=lambda **kw: kw)
        tokenizer = SimpleNamespace(chat_template='present but unused in Base mode')
        fake_transformers = SimpleNamespace(AutoTokenizer=SimpleNamespace(from_pretrained=lambda *a: tokenizer))
        with tempfile.TemporaryDirectory() as tmp:
            job = dict(mode='code', model='coder', seed=1,
                       rows=[dict(id=0, question='first'), dict(id=1, question='second')],
                       config=dict(inference_memory=.8, inference_context=8192,
                                   code_tokens=2048, inference_batch=1))
            with patch.dict('sys.modules', vllm=fake_vllm, transformers=fake_transformers):
                result = generate(job)
            self.assertEqual(len(result), 2)
            self.assertTrue(result[0]['sam_ok'])
            saved = result[1]
            self.assertFalse(saved['sam_ok'])
            self.assertEqual(saved['question'], 'second')
            self.assertEqual(saved['raw_code_output'], echo)
            self.assertTrue(saved['rendered_prompt'].endswith('second\nOutput:\n<CODE>\n'))
            self.assertTrue(prompts[0].endswith('first\nOutput:\n<CODE>\n'))

    def test_old_cache_cannot_be_reused_and_duplicate_rows_survive(self):
        calls = []
        def worker(mode, rows, model, gpus, cfg, work):
            calls.append(mode)
            if mode == 'code':
                return [dict(r, code='def solver(): return 17') for r in rows]
            return [dict(r, embedding=[1., 0.]) for r in rows]
        with tempfile.TemporaryDirectory() as tmp:
            config = dict(run_root=tmp, coder_model='coder', embedding_model='encoder',
                          code_tokens=2048, embedding_tokens=4096)
            with patch('methods.r_diverse.inference.run_workers', worker), \
                 patch('methods.r_diverse.inference.CODE_PROTOCOL', 'old-protocol'):
                sam(['question'], config, ['0'], tmp)
            calls.clear()
            with patch('methods.r_diverse.inference.run_workers', worker):
                vectors, records = sam(['question', 'question'], config, ['0'], tmp)
                self.assertEqual(calls, ['code', 'embed'])
                self.assertEqual(vectors.shape, (2, 2))
                self.assertEqual(records[0]['key'], records[1]['key'])
                calls.clear()
                sam(['question'], config, ['0'], tmp)
                self.assertEqual(calls, [])


if __name__ == '__main__':
    unittest.main()
