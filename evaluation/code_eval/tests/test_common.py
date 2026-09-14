import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import align, bind, codegen, read


class EvaluationIntegrity(unittest.TestCase):
    def test_alignment_requires_all_tasks_once(self):
        tasks = [{"task_id": "a"}, {"task_id": "b"}]
        self.assertEqual([r["task_id"] for r in align(tasks, list(reversed(tasks)))], ["a", "b"])
        for bad in [tasks[:1], [tasks[0], tasks[0]], [tasks[0], {"task_id": "c"}]]:
            with self.assertRaises(ValueError):
                align(tasks, bad)

    def test_changed_experiment_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "config.json"
            bind(path, {"model": "base", "tokens": 4096})
            bind(path, {"model": "base", "tokens": 4096})
            with self.assertRaises(ValueError):
                bind(path, {"model": "solver1", "tokens": 4096})
            self.assertEqual(read(path)["model"], "base")

    def test_interrupted_generation_resumes_only_missing_questions(self):
        tasks = [{"task_id": str(i), "rendered_prompt": f"prompt{i}"} for i in range(5)]
        saved = []

        class Engine:
            def __init__(self, fail=False):
                self.calls = []
                self.fail = fail

            def generate(self, prompts, **kwargs):
                self.calls.append(prompts)
                if self.fail and len(self.calls) == 2:
                    raise RuntimeError("interruption")
                return [SimpleNamespace(outputs=[SimpleNamespace(
                    text="answer:" + p, finish_reason="stop", token_ids=[1, 2])]) for p in prompts]

        def checkpoint(rows):
            saved[:] = rows

        with self.assertRaises(RuntimeError):
            codegen(Engine(fail=True), tasks, [], lambda _: None, 2, checkpoint)
        self.assertEqual(len(saved), 2)
        resumed = Engine()
        result = codegen(resumed, tasks, saved, lambda _: None, 2, checkpoint)
        self.assertEqual(resumed.calls, [["prompt2", "prompt3"], ["prompt4"]])
        self.assertEqual(len(result), 5)
        self.assertEqual(len(saved), 5)
        finished = Engine()
        codegen(finished, tasks, saved, lambda _: None, 2, checkpoint)
        self.assertEqual(finished.calls, [])


if __name__ == "__main__":
    unittest.main()
