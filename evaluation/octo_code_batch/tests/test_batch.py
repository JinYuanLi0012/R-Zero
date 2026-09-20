import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import threading
import sys
import time
from types import SimpleNamespace
import unittest

ENTRY = Path(__file__).resolve().parents[1] / "run.py"
spec = importlib.util.spec_from_file_location("octo_batch", ENTRY)
batch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(batch)


class BatchTests(unittest.TestCase):
    def test_child_timeout_is_stopped_and_logged(self):
        with tempfile.TemporaryDirectory() as temp:
            log = Path(temp) / "child.log"
            status = batch.run_child(
                [sys.executable, "-u", "-c", "import time; print('started'); time.sleep(60)"],
                dict(os.environ), log, threading.Event(), 0.1,
            )
            self.assertEqual(status, 124)
            self.assertIn("started", log.read_text())

    def test_four_gpu_queue_failure_continuation_and_summary(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            args = SimpleNamespace(output=root, gpus=["0", "1", "2", "3"], tools=root,
                                   workers=4, max_new_tokens=4096, max_model_len=16384, batch_size=32,
                                   gpu_memory_utilization=0.85, seed=42, timeout=6, job_timeout_hours=0)
            jobs = [dict(model=f"model-{i}", base_model=False, status="QUEUED", error=None,
                         output=str(root / str(i)), log=str(root / f"{i}.log")) for i in range(12)]
            lock = threading.Lock()
            active = set()
            maximum = [0]
            visited = []
            first_wave = threading.Barrier(4)

            def launch(command, env, log, cancelled, timeout):
                gpu = env["CUDA_VISIBLE_DEVICES"]
                model = command[command.index("--model") + 1]
                index = int(model.split("-")[1])
                self.assertEqual(command[command.index("--tp") + 1], "1")
                self.assertEqual(command[command.index("--datasets") + 1:command.index("--tp")], ["humaneval", "mbpp"])
                self.assertTrue(env["XDG_CACHE_HOME"].endswith(gpu))
                with lock:
                    self.assertNotIn(gpu, active)
                    active.add(gpu)
                    visited.append(index)
                    maximum[0] = max(maximum[0], len(active))
                if index < 4:
                    first_wave.wait(timeout=5)
                time.sleep(0.01)
                path = Path(command[command.index("--output") + 1])
                batch.atomic_json(path / "summary.json", {"benchmarks": [
                    {"dataset": "humaneval", "count": 164, "samples_per_task": 1, "pass@1_percent": 20 + index},
                    {"dataset": "mbpp", "count": 378, "samples_per_task": 1, "pass@1_percent": 30 + index}]})
                with lock:
                    active.remove(gpu)
                return 1 if index == 2 else 0  # Existing summary must not hide failure.

            with contextlib.redirect_stdout(io.StringIO()):
                status = batch.execute(args, jobs, launch=launch)
            self.assertEqual(status, 1)
            self.assertEqual(maximum[0], 4)
            self.assertEqual(sorted(visited), list(range(12)))
            self.assertEqual(jobs[2]["status"], "FAILED")
            self.assertNotIn("humaneval_plus", jobs[2])
            self.assertEqual(sum(j["status"] == "DONE" for j in jobs), 11)
            self.assertEqual(len(json.loads((root / "summary.json").read_text())["models"]), 12)
            self.assertIn("FAILED", (root / "summary.txt").read_text())
            self.assertTrue((root / "summary.csv").exists())

    def test_resolve_latest_never_falls_back_to_old_step(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            old = root / "global_step_5/actor/huggingface"
            old.mkdir(parents=True)
            (old / "config.json").write_text("{}")
            (old / "model.safetensors").write_bytes(b"fixture")
            self.assertEqual(batch.resolve_model(str(root)), str(old.resolve()))
            (root / "global_step_15").mkdir()
            with self.assertRaises(ValueError):
                batch.resolve_model(str(root))

    def test_same_basename_different_model_outputs_and_invalid_scores(self):
        self.assertNotEqual(batch.job_key("/a/huggingface", False), batch.job_key("/b/huggingface", False))
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "summary.json"
            batch.atomic_json(path, {"benchmarks": []})
            with self.assertRaises(ValueError):
                batch.parse_scores(path)


if __name__ == "__main__":
    unittest.main()
