import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

HERE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("mixed_batch", HERE / "run.py")
batch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(batch)


class MixedTests(unittest.TestCase):
    def test_manifest_counts_filter_and_paths(self):
        args = SimpleNamespace(manifest=HERE / "manifests/qwen_octo_31.json", family=None,
                               models=[], models_file=None, base_model=[])
        records = batch.read_records(args)
        self.assertEqual(len(records), 31)
        self.assertEqual(sum(r.get("base_model", False) for r in records), 1)
        self.assertFalse(any("\\_" in r["model"] or r["model"].endswith(".safetensors") for r in records))
        args.family = "qwen"
        self.assertEqual(len(batch.read_records(args)), 20)
        args.family = "octo"
        self.assertEqual(len(batch.read_records(args)), 11)

    def test_routing_and_shared_queue(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            records = [{"model": f"/model/{i}", "family": "qwen" if i < 4 else "octo", "base_model": i == 4}
                       for i in range(8)]
            args = SimpleNamespace(output=root, gpus=["0", "1", "2", "3"], tools=root,
                                   qwen_prompt_style="base", workers=4, max_new_tokens=4096,
                                   max_model_len=16384, batch_size=32, gpu_memory_utilization=0.85,
                                   seed=42, timeout=6, job_timeout_hours=0)
            (root / "logs").mkdir()
            jobs = batch.plan(records, root, "base", validate=False)
            commands = []
            def launch(command, env, log, cancelled, timeout):
                commands.append(command)
                model = command[command.index("--model") + 1]
                index = int(Path(model).name)
                self.assertEqual(command[command.index("--tp") + 1], "1")
                if index < 4:
                    self.assertEqual(Path(command[2]), batch.ENTRIES["qwen"])
                    self.assertEqual(command[command.index("--prompt-style") + 1], "base")
                    self.assertNotIn("--base-model", command)
                else:
                    self.assertEqual(Path(command[2]), batch.ENTRIES["octo"])
                    self.assertNotIn("--prompt-style", command)
                    self.assertEqual("--base-model" in command, index == 4)
                output = Path(command[command.index("--output") + 1])
                batch.atomic_json(output / "summary.json", {"benchmarks": [
                    {"dataset": d, "count": n, "samples_per_task": 1, "pass@1_percent": 25}
                    for d, n in [("humaneval", 164), ("mbpp", 378)]]})
                return 1 if index == 1 else 0
            with contextlib.redirect_stdout(io.StringIO()):
                result = batch.execute(args, jobs, launch=launch)
            self.assertEqual(result, 1)
            self.assertEqual(len(commands), 8)
            self.assertEqual(sum(j["status"] == "DONE" for j in jobs), 7)
            self.assertEqual(jobs[1]["status"], "FAILED")
            text = (root / "summary.txt").read_text()
            self.assertIn("qwen-base", text)
            self.assertIn("octo-training-chat", text)
            self.assertNotEqual(batch.plan(records[:1], root, "chat", False)[0]["output"], jobs[0]["output"])

    def test_shard_and_markdown_normalization(self):
        jobs = batch.plan([{"family": "qwen", "model": "/qwen\\_run/huggingface/model-00001-of-00002.safetensors"}],
                          Path("/tmp/result"), "base", validate=False)
        self.assertEqual(jobs[0]["model"], "/qwen_run/huggingface")


if __name__ == "__main__":
    unittest.main()
