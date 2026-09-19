import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from evaluation.octo_code_eval.protocol import TEMPLATE, configure, render, TokenInputModel


class Tokenizer:
    bos_token = "<|begin_of_text|>"
    bos_token_id = 128000
    eos_token = "<|end_of_text|>"
    eos_token_id = 128001
    pad_token_id = None
    chat_template = None

    def apply_chat_template(self, messages, tokenize, add_generation_prompt):
        assert not tokenize and add_generation_prompt
        return self.bos_token + "".join(m["role"] + ": " + m["content"] + "\n" for m in messages) + "assistant:\n"

    def encode(self, prompt, add_special_tokens):
        ids = [self.bos_token_id] * prompt.count(self.bos_token) + [1, 2, 3]
        return ([self.bos_token_id] if add_special_tokens else []) + ids


class ProtocolTests(unittest.TestCase):
    def test_base_and_solver_use_identical_inputs(self):
        template = TEMPLATE.read_text()
        base = configure(Tokenizer(), template, base_model=True)
        solver = Tokenizer()
        solver.chat_template = template
        configure(solver, template)
        task = {"task_id": "example", "messages": [{"role": "user", "content": "Write Python code"}]}
        b = render(task, base, 4096, 16384)
        s = render(task, solver, 4096, 16384)
        self.assertEqual(b, s)
        self.assertEqual(b["prompt_token_ids"].count(base.bos_token_id), 1)
        self.assertEqual(b["prompt_tokens"], len(b["prompt_token_ids"]))
        calls = []

        class Model:
            def generate(self, prompts, **kwargs):
                calls.append((prompts, kwargs))
                return "output"

        adapter = TokenInputModel(Model(), [b])
        self.assertEqual(adapter.generate([b["rendered_prompt"]], sampling_params="settings"), "output")
        self.assertEqual(calls, [([{"prompt_token_ids": b["prompt_token_ids"]}], {"sampling_params": "settings"})])

    def test_no_silent_template_substitution(self):
        with self.assertRaisesRegex(ValueError, "missing"):
            configure(Tokenizer(), TEMPLATE.read_text())
        for is_base in [False, True]:
            tokenizer = Tokenizer()
            tokenizer.chat_template = "different template"
            with self.assertRaisesRegex(ValueError, "differs"):
                configure(tokenizer, TEMPLATE.read_text(), base_model=is_base)

    def test_reject_duplicate_bos_and_overflow(self):
        tokenizer = configure(Tokenizer(), TEMPLATE.read_text(), base_model=True)
        task = {"task_id": "test", "messages": [{"role": "user", "content": tokenizer.bos_token}]}
        with self.assertRaisesRegex(ValueError, "one leading BOS"):
            render(task, tokenizer, 4, 20)
        task["messages"][0]["content"] = "normal"
        with self.assertRaisesRegex(ValueError, "do not fit"):
            render(task, tokenizer, 4, 7)


if __name__ == "__main__":
    unittest.main()
