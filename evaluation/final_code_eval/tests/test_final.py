import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from evaluation.final_code_eval.protocol import configure, render
from evaluation.final_code_eval import run
from evaluation.code_batch import run as batch


class Tokenizer:
    chat_template = "training template must never be used"
    def __init__(self, family):
        self.bos_token_id = 128000 if family == "octo" else None
        self.bos_token = "<|begin_of_text|>" if family == "octo" else None
        self.eos_token_id = 128001 if family == "octo" else 151643
        self.eos_token = "<|end_of_text|>" if family == "octo" else "<|endoftext|>"
    def encode(self, text, add_special_tokens):
        return ([self.bos_token_id] if self.bos_token_id is not None and add_special_tokens else []) + [10, 20]
    def apply_chat_template(self, *args, **kwargs):
        raise AssertionError("Final must not apply a chat template")


class FinalTests(unittest.TestCase):
    def test_all_models_preserved_and_paper_rows_launch_first(self):
        folder = batch.ROOT / "evaluation/code_batch/manifests"
        old = json.loads((folder / "qwen_octo_42.json").read_text())
        new = json.loads((folder / "qwen_octo_42_final.json").read_text())
        self.assertCountEqual(old, new)
        self.assertEqual(len(new), 42)
        self.assertEqual(sum(r["family"] == "qwen" for r in new), 31)
        self.assertTrue(all("重新评" in r["label"] for r in new[:11]))
        self.assertEqual([r["label"] for r in new[:3]], ["qwen_base（重新评）", "qwen_rzero_v2（重新评）", "qwen_semantic_novelty_v2（重新评）"])
        args = SimpleNamespace(tools=Path("/tools"), workers=4, max_new_tokens=4096,
                               max_model_len=16384, batch_size=32, gpu_memory_utilization=.85, seed=42, timeout=6)
        final = batch.plan(new, Path("/out"), "base", False, "final")
        legacy = batch.plan(new, Path("/out"), "base", False, "legacy")
        matched = batch.plan(new, Path("/out"), "base", False, "matched")
        for j, l, m in zip(final, legacy, matched):
            cmd = batch.command_for(args, j)
            self.assertEqual(Path(cmd[2]), batch.ROOT / "evaluation/final_code_eval/run.py")
            self.assertEqual(cmd[cmd.index("--family") + 1], j["family"])
            self.assertNotIn("--base-model", cmd)
            self.assertNotEqual(j["output"], l["output"])
            self.assertNotEqual(j["output"], m["output"])

    def test_direct_prompt_and_single_bos(self):
        task = {"task_id": "HumanEval/0", "prompt": "def f():\n", "stop": ["\ndef "]}
        for family in ("qwen", "octo"):
            tok = Tokenizer(family)
            configure(tok, family)
            rendered = render(task, tok, family, 4096, 16384)
            self.assertEqual(rendered["rendered_prompt"], task["prompt"])
            self.assertEqual(rendered["prompt_token_ids"], tok.encode(task["prompt"], True))
            with self.assertRaises(ValueError):
                render(task, tok, family, 4096, 4096)
            tok.eos_token = "wrong"
            with self.assertRaises(ValueError):
                configure(tok, family)

    def test_generation_uses_native_tokens_shared_stops_and_no_checkpoint_defaults(self):
        for family in ("qwen", "octo"):
            with tempfile.TemporaryDirectory() as temp:
                output = Path(temp)
                folder = output / "humaneval"
                task = {"task_id": "HumanEval/0", "prompt": "def f():\n", "stop": ["\ndef "]}
                run.write(folder / "tasks.json", [task])
                tok = Tokenizer(family)
                captured = {}
                class Engine:
                    def __init__(self, **kwargs): captured["engine"] = kwargs
                    def generate(self, prompts, sampling_params, **kwargs):
                        captured["inputs"] = prompts
                        captured["params"] = sampling_params
                        return [SimpleNamespace(outputs=[SimpleNamespace(text="    return 1", token_ids=[5], finish_reason="stop")])]
                args = SimpleNamespace(model="model", revision="revision", family=family,
                    datasets=["humaneval"], output=output, max_new_tokens=4096,
                    max_model_len=16384, tp=1, dtype="bfloat16", gpu_memory_utilization=.85, seed=42, batch_size=32)
                modules = {"transformers": SimpleNamespace(AutoTokenizer=SimpleNamespace(from_pretrained=lambda *a, **k: tok)),
                           "vllm": SimpleNamespace(LLM=Engine, SamplingParams=lambda **k: k)}
                with patch.dict("sys.modules", modules), patch.object(run.importlib.metadata, "version", return_value="test"):
                    run.generate(args)
                    run.generate(args)  # Completed generation safely resumes without a new engine call.
                self.assertEqual(captured["engine"]["generation_config"], "vllm")
                self.assertEqual(captured["inputs"], [{"prompt_token_ids": tok.encode(task["prompt"], True)}])
                params = captured["params"][0]
                self.assertEqual(params["stop"], task["stop"])
                self.assertEqual(params["stop_token_ids"], [tok.eos_token_id])
                self.assertEqual(params["temperature"], 0)
                self.assertEqual(len(run.read(folder / "raw.json")), 1)


if __name__ == "__main__":
    unittest.main()
