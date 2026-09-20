import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

from evaluation.matched_code_eval.protocol import configure, messages_for, render, template_for
from evaluation.code_batch.run import plan, command_for


class ProtocolTests(unittest.TestCase):
    def test_shared_messages_and_routing(self):
        task = {'task_id': 'test', 'task_prompt': 'def add(a, b):\n    """Return the sum."""\n'}
        self.assertEqual([m['role'] for m in messages_for(task)], ['system', 'user'])
        self.assertNotIn('boxed', str(messages_for(task)))
        with tempfile.TemporaryDirectory() as directory:
            records = [{'family': f, 'model': '/model/' + f, 'base_model': b}
                       for f in ['qwen', 'octo'] for b in [False, True]]
            jobs = plan(records, Path(directory), 'base', validate=False, protocol_mode='matched')
            args = SimpleNamespace(tools=directory, workers=4, max_new_tokens=4096,
                                   max_model_len=16384, batch_size=32,
                                   gpu_memory_utilization=.85, seed=42, timeout=6)
            for job in jobs:
                command = command_for(args, job)
                self.assertIn('matched_code_eval', command[2])
                self.assertNotIn('--prompt-style', command)
                self.assertEqual(command[command.index('--family') + 1], job['family'])
            legacy = plan(records, Path(directory), 'base', validate=False)
            self.assertTrue(set(j['output'] for j in jobs).isdisjoint(j['output'] for j in legacy))

    @unittest.skipUnless(os.getenv('MATCHED_QWEN_TOKENIZER') and os.getenv('MATCHED_OCTO_TOKENIZER'),
                         'Set local tokenizer paths to run real-tokenizer checks')
    def test_real_base_and_saved_solver_inputs(self):
        from transformers import AutoTokenizer
        task = {'task_id': 'test', 'task_prompt': 'def add(a, b):\n    """Return the sum."""\n'}
        for family in ['qwen', 'octo']:
            tok = AutoTokenizer.from_pretrained(os.environ['MATCHED_' + family.upper() + '_TOKENIZER'])
            tok = configure(tok, template_for(family), family)
            base = render(task, tok, 4096, 16384, family)
            # The same API sequence used by RLHFDataset, independently recomputed.
            training_text = tok.apply_chat_template(messages_for(task), tokenize=False, add_generation_prompt=True)
            self.assertEqual(base['prompt_token_ids'], tok.encode(training_text, add_special_tokens=False))
            expected_end = '<|im_start|>assistant\n' if family == 'qwen' else 'assistant:\n'
            self.assertTrue(base['rendered_prompt'].endswith(expected_end))
            self.assertNotIn('<think>\n\n</think>', base['rendered_prompt'])
            if family == 'qwen':
                self.assertIsNone(tok.bos_token_id)
            else:
                self.assertEqual(base['prompt_token_ids'].count(tok.bos_token_id), 1)
            with tempfile.TemporaryDirectory() as directory:
                tok.save_pretrained(directory)
                solver_tok = configure(AutoTokenizer.from_pretrained(directory), template_for(family), family)
                self.assertEqual(base, render(task, solver_tok, 4096, 16384, family))
            tok.chat_template = 'different training protocol'
            with self.assertRaisesRegex(ValueError, 'template differs'):
                configure(tok, template_for(family), family)


if __name__ == '__main__':
    unittest.main()
