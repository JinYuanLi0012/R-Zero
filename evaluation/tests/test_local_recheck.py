"""CPU-only contract tests; no model weights or GPU runtime required."""

import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import requests

from evaluation.local_judge import LocalJudge, judge_metadata, local_backend, parse_verdict
from evaluation.recheck_common import recheck_rows
from evaluation import recheck_resume, run_local_recheck


ROOT = Path(__file__).resolve().parents[2]


def completion(text="Yes", finish="stop", status=200):
    response = MagicMock(status_code=status)
    response.json.return_value = {"choices": [{"message": {"content": text}, "finish_reason": finish}]}
    return response


class LocalRecheckTest(unittest.TestCase):
    def setUp(self):
        self.env_patch = patch.dict(os.environ, {"RECHECK_BACKEND": "local"}, clear=True)
        self.env_patch.start()
        self.addCleanup(self.env_patch.stop)

    def fixture(self):
        # Retain test artifacts for inspection; never remove user files.
        root = Path(tempfile.mkdtemp(prefix="rzero-local-recheck-"))
        result = root / "evaluation/solver/results_math.json"
        result.parent.mkdir(parents=True)
        result.write_text(json.dumps([
            {"answer": "1", "response": "1", "score": 1},
            {"answer": "2", "response": "2", "score": 0},
            {"average_score": 0.5},
        ]))
        models = root / "models.txt"
        models.write_text("solver\n")
        os.environ["STORAGE_PATH"] = str(root)
        os.environ["EVAL_LOG_DIR"] = str(root / "logs")
        return root, result, models, root / "out.jsonl"

    def test_payload_and_auth_are_independent_of_openai_settings(self):
        os.environ.update(OPENAI_API_KEY="old-test-credential", OPENAI_BASE_URL="https://invalid.example/v1",
                          RECHECK_JUDGE_MODEL="gpt-old", RECHECK_REASONING_EFFORT="none",
                          RECHECK_MAX_COMPLETION_TOKENS="8")
        with patch("evaluation.local_judge.requests.Session") as factory:
            session = factory.return_value.__enter__.return_value
            session.post.return_value = completion()
            self.assertEqual(LocalJudge()("2", "2"), "Yes")
            args, kwargs = session.post.call_args
            self.assertEqual(args[0], "http://127.0.0.1:8000/v1/chat/completions")
            self.assertNotIn("Authorization", kwargs["headers"])
            self.assertFalse(session.trust_env)
            self.assertFalse(kwargs["allow_redirects"])
            self.assertEqual(kwargs["json"]["model"], "Qwen/Qwen3-32B")
            self.assertEqual(kwargs["json"]["max_tokens"], 8)
            self.assertEqual(kwargs["json"]["temperature"], 0)
            self.assertEqual(kwargs["json"]["chat_template_kwargs"], {"enable_thinking": False})
            self.assertNotIn("reasoning_effort", kwargs["json"])
            self.assertNotIn("max_completion_tokens", kwargs["json"])

    def test_only_explicit_local_key_is_used(self):
        os.environ.update(OPENAI_API_KEY="old-test-credential", RECHECK_LOCAL_API_KEY="local-test")
        self.assertEqual(LocalJudge().headers["Authorization"], "Bearer local-test")

    def test_strict_verdict_parser(self):
        for text, expected in [("Yes", "Yes"), (" no. \n", "No"), ("<think>\n</think>\nYes", "Yes")]:
            self.assertEqual(parse_verdict(text), expected)
        for text in [None, "", "Yes or No", "Yesterday", "No, yes is wrong", "<think>yes</think>No", "**Yes**"]:
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_verdict(text)

    def test_no_remote_endpoint_or_bad_configuration(self):
        for base in ["https://api.openai.com/v1", "http://remote/v1", "http://localhost/v1?key=x", "http://user:pass@localhost/v1"]:
            with patch.dict(os.environ, {"RECHECK_LOCAL_BASE_URL": base}), self.assertRaises(ValueError):
                LocalJudge()
        for timeout in ["0", "nan", "inf"]:
            with patch.dict(os.environ, {"RECHECK_LOCAL_TIMEOUT": timeout}), self.assertRaises(ValueError):
                LocalJudge()
        with patch.dict(os.environ, {"RECHECK_BACKEND": "locla"}), self.assertRaises(ValueError):
            local_backend()

    def test_truncation_malformed_and_http_errors_never_become_no(self):
        for response in [completion(finish="length"), completion(status=401), completion(status=302), completion(text=None)]:
            with patch("evaluation.local_judge.requests.Session") as factory:
                factory.return_value.__enter__.return_value.post.return_value = response
                with self.assertRaises((ValueError, RuntimeError)):
                    LocalJudge()("2", "2")
        with patch("evaluation.local_judge.requests.Session") as factory:
            factory.return_value.__enter__.return_value.post.side_effect = requests.Timeout("private data")
            with self.assertRaisesRegex(RuntimeError, "connection failed") as caught:
                LocalJudge()("2", "2")
            self.assertNotIn("private data", str(caught.exception))

    def test_strict_batch_is_atomic_and_only_checks_local_errors(self):
        rows = [{"score": 1}, {"score": 0, "answer": "a", "response": "ok"},
                {"score": 0, "answer": "b", "response": "bad"}]
        def judge(answer, response):
            if response == "bad":
                raise ValueError("invalid verdict")
            return "Yes"
        with self.assertRaises(RuntimeError):
            recheck_rows(rows, judge, 1, "fixture", strict=True, show_progress=False)
        self.assertEqual([r["score"] for r in rows], [1, 0, 0])
        recheck_rows(rows, lambda a, r: "Yes", 2, "fixture", strict=True, show_progress=False)
        self.assertEqual([r["score"] for r in rows], [1, 1, 1])

    def test_results_cli_local_never_reads_token_file_and_records_metadata(self):
        root, source, _, output = self.fixture()
        before = source.read_bytes()
        os.environ["FINAL_RESULTS_FILE"] = str(output)
        real_open = open
        def guarded_open(file, *args, **kwargs):
            if str(file).endswith("tokens.json"):
                self.fail("Local mode tried to read tokens.json")
            return real_open(file, *args, **kwargs)
        with patch("builtins.open", side_effect=guarded_open), patch("evaluation.local_judge.requests.Session") as factory:
            factory.return_value.__enter__.return_value.post.return_value = completion()
            with patch.object(sys, "argv", ["results_recheck.py", "--model_name", "solver", "--datasets", "math"]):
                runpy.run_path(str(ROOT / "evaluation/results_recheck.py"), run_name="__main__")
        record = json.loads(output.read_text())
        self.assertEqual(record["score"], 100)
        self.assertEqual(record["recheck"], judge_metadata())
        self.assertEqual(source.read_bytes(), before)

    def test_failed_results_cli_writes_no_success(self):
        _, _, _, output = self.fixture()
        os.environ["FINAL_RESULTS_FILE"] = str(output)
        with patch("evaluation.local_judge.requests.Session") as factory:
            factory.return_value.__enter__.return_value.post.return_value = completion(status=500)
            with patch.object(sys, "argv", ["results_recheck.py", "--model_name", "solver", "--datasets", "math"]):
                with self.assertRaises(RuntimeError):
                    runpy.run_path(str(ROOT / "evaluation/results_recheck.py"), run_name="__main__")
        self.assertFalse(output.exists())

    def test_resume_rechecks_legacy_scores_then_skips_matching_local_scores(self):
        _, _, models, output = self.fixture()
        output.write_text(json.dumps({"model": "solver", "dataset": "math", "score": 50}) + "\n")
        argv = ["recheck_resume.py", "--models_file", str(models), "--output_file", str(output), "--datasets", "math"]
        with patch.object(sys, "argv", argv), patch.object(recheck_resume, "load_openai_key") as key_loader:
            with patch("evaluation.local_judge.requests.Session") as factory:
                session = factory.return_value.__enter__.return_value
                session.post.return_value = completion()
                recheck_resume.main()
                self.assertEqual(session.post.call_count, 1)
                recheck_resume.main()
                self.assertEqual(session.post.call_count, 1)
                key_loader.assert_not_called()
        self.assertEqual(len(output.read_text().splitlines()), 2)
        changed = dict(judge_metadata(), max_tokens=64)
        self.assertEqual(recheck_resume.load_completed(output, changed), set())

    def test_runner_dry_run_never_starts_server_or_touches_output(self):
        _, _, _, output = self.fixture()
        with patch.object(sys, "argv", ["runner", "--model_name", "solver", "--datasets", "math", "--output_file", str(output), "--dry_run"]):
            with patch.object(subprocess, "Popen") as popen, patch.object(run_local_recheck.socket, "socket") as sock:
                run_local_recheck.main()
                popen.assert_not_called()
                sock.assert_not_called()
        self.assertFalse(output.exists())

    def test_runner_owns_server_and_cleans_up_on_client_failure(self):
        _, _, _, output = self.fixture()
        os.environ.update(OPENAI_API_KEY="old-test-credential", RECHECK_LOCAL_BASE_URL="https://wrong.example/v1")
        server, worker = MagicMock(), MagicMock()
        worker.wait.return_value = 1
        with patch.object(sys, "argv", ["runner", "--model_name", "solver", "--datasets", "math", "--output_file", str(output)]), \
             patch.object(subprocess, "Popen", side_effect=[server, worker]) as popen, \
             patch.object(run_local_recheck.socket, "socket") as sock, \
             patch.object(run_local_recheck, "wait_ready") as ready, \
             patch.object(run_local_recheck, "stop_owned_process") as stop:
            sock.return_value.__enter__.return_value.getsockname.return_value = ("127.0.0.1", 12345)
            with self.assertRaises(subprocess.CalledProcessError):
                run_local_recheck.main()
            command = popen.call_args_list[0].args[0]
            self.assertEqual(command[command.index("--tensor-parallel-size") + 1], "4")
            self.assertEqual(command[command.index("--dtype") + 1], "bfloat16")
            env = popen.call_args_list[1].kwargs["env"]
            self.assertEqual(env["RECHECK_LOCAL_BASE_URL"], "http://127.0.0.1:12345/v1")
            self.assertNotIn("OPENAI_API_KEY", env)
            self.assertTrue(popen.call_args_list[0].kwargs["start_new_session"])
            ready.assert_called_once()
            self.assertEqual([call.args[0] for call in stop.call_args_list], [worker, server])

    def test_readiness_rejects_exited_process(self):
        process = MagicMock()
        process.poll.return_value = 1
        with self.assertRaisesRegex(RuntimeError, "exited during startup"):
            run_local_recheck.wait_ready(process, "http://127.0.0.1:12345/v1", "test", "alias", 10)

    def test_real_http_lifecycle_success_and_failure(self):
        for failure in (False, True):
            with self.subTest(failure=failure):
                root, source, _, output = self.fixture()
                output = root / "nested" / "results.jsonl"
                before = source.read_bytes()
                package = root / "vllm/entrypoints/openai"
                package.mkdir(parents=True)
                for directory in [package, package.parent, package.parent.parent]:
                    (directory / "__init__.py").write_text("")
                (package / "api_server.py").write_text((ROOT / "evaluation/tests/fake_vllm_server.py").read_text())
                pid_file = root / "server.pid"
                env = dict(os.environ, PYTHONPATH=str(root), TEST_SERVER_PID=str(pid_file),
                           RECHECK_STARTUP_TIMEOUT="15", RECHECK_LOCAL_TIMEOUT="5",
                           HTTP_PROXY="http://127.0.0.1:1")
                if failure:
                    env["TEST_SERVER_FAILURE"] = "1"
                result = subprocess.run([
                    sys.executable, str(ROOT / "evaluation/run_local_recheck.py"),
                    "--model_name", "solver", "--datasets", "math", "--output_file", str(output),
                ], env=env, capture_output=True, text=True, timeout=30)
                self.assertTrue(pid_file.exists(), result.stdout + result.stderr)
                pid = int(pid_file.read_text())
                with self.assertRaises(ProcessLookupError):
                    os.kill(pid, 0)
                self.assertEqual(source.read_bytes(), before)
                if failure:
                    self.assertNotEqual(result.returncode, 0)
                    self.assertFalse(output.exists())
                    self.assertIn("HTTP status 500", result.stderr)
                else:
                    self.assertEqual(result.returncode, 0, result.stderr)
                    record = json.loads(output.read_text())
                    self.assertEqual(record["score"], 100)
                    self.assertEqual(record["recheck"]["model"], "Qwen/Qwen3-32B")


if __name__ == "__main__":
    unittest.main()
