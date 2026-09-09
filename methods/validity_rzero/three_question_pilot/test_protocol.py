"""CPU tests: python -m unittest methods.validity_rzero.three_question_pilot.test_protocol -v"""
import contextlib
import io
import json
import os
from pathlib import Path
import runpy
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

from .core import REPO, METHOD, atomic_json, atomic_jsonl, original_messages, parse_three, resolve_model, three_messages
from .run import collect, completed, mark_completed, run_phase


def pair(q, a="1"):
    return f"<question>{q}</question>\\boxed{{{a}}}"


class ProtocolTests(unittest.TestCase):
    def test_prompt_only_four_literal_edits(self):
        before, after = original_messages(), three_messages()
        system = after[0]["content"].replace("design three brand-new, non-trivial problems.", "design a brand-new, non-trivial problem.")
        system = system.replace("Each problem could come", "The problem could come")
        system = system.replace("output **exactly** three pairs of the following two blocks, one pair per problem, in order:", "output **exactly** the following two blocks:")
        self.assertEqual(system, before[0]["content"])
        self.assertEqual(after[1]["content"].replace("Generate three new, challenging reasoning questions now.", "Generate one new, challenging reasoning question now."), before[1]["content"])

    def test_evaluator_is_production_plus_metadata_only(self):
        source = (REPO / "question_evaluate/evaluate.py").read_text()
        snapshot = (METHOD / "evaluate_snapshot.py").read_text()
        self.assertEqual(snapshot.count("# PILOT_PROVENANCE_ONLY"), 2)
        stripped = "".join(line for line in snapshot.splitlines(keepends=True) if "# PILOT_PROVENANCE_ONLY" not in line)
        self.assertEqual("\n".join(line.rstrip() for line in source.splitlines()), stripped.rstrip("\n"))

    def test_three_pairs_nested_answers_and_repeat_preserved(self):
        rows, stats = parse_three(pair("same", r"\frac{1}{2}") * 3)
        self.assertEqual(len(rows), 3)
        self.assertEqual([r["question_position"] for r in rows], [1, 2, 3])
        self.assertEqual(rows[0]["answer"], r"\frac{1}{2}")
        self.assertEqual(stats["parsed_count"], 3)

    def test_missing_middle_answer_never_borrows_third_answer(self):
        rows, _ = parse_three(pair("A", "11") + "<question>B</question>" + pair("C", "33"))
        self.assertEqual([(r["question_position"], r["answer"]) for r in rows], [(1, "11"), (3, "33")])

    def test_truncated_last_box_keeps_first_two(self):
        rows, _ = parse_three(pair("A") + pair("B") + "<question>C</question>\\boxed{\\frac{1}{")
        self.assertEqual([r["question"] for r in rows], ["A", "B"])

    def test_malformed_first_opening_preserves_positions(self):
        rows, _ = parse_three("<question>broken" + pair("B") + pair("C"))
        self.assertEqual([r["question_position"] for r in rows], [2, 3])

    def test_ignore_fourth_and_log_it(self):
        rows, stats = parse_three(pair("A") * 4)
        self.assertEqual(len(rows), 3)
        self.assertEqual(stats["extra_blocks_ignored"], 1)

    def test_empty_or_unstructured_response(self):
        self.assertEqual(parse_three("no tags")[0], [])
        self.assertEqual(parse_three(pair(""))[0], [])
        self.assertEqual(parse_three(pair("A", ""))[0], [])

    def test_box_inside_question_is_not_the_answer(self):
        rows, _ = parse_three("<question>Compute \\boxed{2} plus one.</question>")
        self.assertEqual(rows, [])

    def test_model_resolution_pins_step_not_latest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            hf = root / "global_step_5/actor/huggingface"
            hf.mkdir(parents=True)
            (hf / "config.json").write_text("{}")
            (hf / "model.safetensors").write_bytes(b"dummy")
            self.assertEqual(resolve_model(root, 5)[0], str(hf.resolve()))
            self.assertEqual(resolve_model(hf, 5)[0], str(hf.resolve()))
            with self.assertRaises(FileNotFoundError):
                resolve_model(root, 15)

    def test_resume_detects_modified_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "workspace/generated_question/three_questions_0_results.json"
            atomic_json(path, [])
            mark_completed(root, "evaluate", 0)
            self.assertTrue(completed(root, "evaluate", 0))
            atomic_json(path, [{}])
            self.assertFalse(completed(root, "evaluate", 0))

    def test_orchestrator_isolation_and_shard_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            args = types.SimpleNamespace(output_dir=root, gpus=["0", "1", "2", "3"],
                                         requests_per_gpu=2, resume=False, eval_timeout_seconds=10)
            calls = []
            def launch(cmd, **kw):
                env = kw["env"]
                calls.append((cmd, env))
                self.assertEqual(env["VALIDITY_RZERO_ENABLED"], "1")
                self.assertEqual(env["VALIDITY_RZERO_DOMAIN_MODE"], "none")
                self.assertNotIn("VALIDITY_RZERO_NOVELTY_INVALID_REWARD", env)
                self.assertNotIn("TERRA_REPLAY_RATIO", env)
                self.assertEqual(env["STORAGE_PATH"], str(root / "workspace"))
                if "--shard" in cmd:
                    shard = int(cmd[cmd.index("--shard") + 1])
                    atomic_json(root / "generation" / f"shard_{shard}_candidates.json", [])
                    atomic_json(root / "generation" / f"shard_{shard}_prompt.json", {})
                    atomic_jsonl(root / "generation" / f"shard_{shard}_raw.jsonl", [])
                else:
                    shard = int(cmd[cmd.index("--suffix") + 1])
                    input_path = root / "workspace/generated_question" / f"three_questions_{shard}.json"
                    self.assertTrue(input_path.exists())
                    input_path.unlink()
                    atomic_json(input_path.with_name(f"three_questions_{shard}_results.json"), [])
                self.assertEqual(env["CUDA_VISIBLE_DEVICES"], str(shard))
                return types.SimpleNamespace(poll=lambda: 0)
            env = {"VALIDITY_RZERO_DOMAIN_MODE": "balanced_v1", "VALIDITY_RZERO_NOVELTY_INVALID_REWARD": "zero", "TERRA_REPLAY_RATIO": "0.1"}
            with patch.dict(os.environ, env), patch("subprocess.Popen", side_effect=launch), contextlib.redirect_stdout(io.StringIO()):
                run_phase(args, "generate", {"questioner": "Q4"})
                run_phase(args, "evaluate", {"solver": "S3"})
                self.assertEqual(len(calls), 8)
                args.resume = True
                run_phase(args, "generate", {"questioner": "Q4"})
                run_phase(args, "evaluate", {"solver": "S3"})
                self.assertEqual(len(calls), 8)
                self.assertEqual(os.environ["VALIDITY_RZERO_DOMAIN_MODE"], "balanced_v1")
                # A damaged generation artifact must rerun that shard AND its evaluation.
                (root / "generation/shard_1_raw.jsonl").write_text('{"changed": true}\n')
                run_phase(args, "generate", {"questioner": "Q4"})
                run_phase(args, "evaluate", {"solver": "S3"})
                self.assertEqual(len(calls), 10)

    def test_failed_worker_does_not_create_success_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            args = types.SimpleNamespace(output_dir=root, gpus=["0"], requests_per_gpu=1,
                                         resume=False, eval_timeout_seconds=10)
            with patch("subprocess.Popen", return_value=types.SimpleNamespace(poll=lambda: 1)), \
                 patch("methods.validity_rzero.three_question_pilot.run.stop_workers") as stop, \
                 contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(RuntimeError):
                    run_phase(args, "generate", {"questioner": "Q4"})
                stop.assert_called_once()
            self.assertFalse((root / "receipts/generate_0.json").exists())

    def test_real_evaluator_control_flow_with_fake_gpu(self):
        """Exercise the real snapshot (both gates, majority, skips and duplicate IDs).

        Only external inference/grader dependencies are fake. No GPU claim is made.
        """
        import re
        def extract(text):
            matches = re.findall(r"\\boxed\{([^{}]*)\}", text)
            return matches[-1] if matches else "None"
        grader = types.ModuleType("mathruler.grader")
        grader.extract_boxed_content = extract
        grader.grade_answer = lambda a, b: a == b
        mathruler = types.ModuleType("mathruler")
        mathruler.grader = grader
        stopit = types.ModuleType("stopit")
        stopit.threading_timeoutable = lambda **kw: lambda fn: lambda a, b, **k: fn(a, b)
        jinja = types.ModuleType("jinja2")
        class Template:
            def __init__(self, text):
                self.text = text
            def render(self, **kw):
                return kw["content"]
        jinja.Template = Template
        tokenizer = types.SimpleNamespace(eos_token_id=0, chat_template=None)
        transformers = types.ModuleType("transformers")
        transformers.AutoTokenizer = types.SimpleNamespace(from_pretrained=lambda *a, **kw: tokenizer)
        vllm = types.ModuleType("vllm")
        vllm.SamplingParams = lambda **kw: types.SimpleNamespace(**kw)
        calls = []
        def response(answers):
            return types.SimpleNamespace(outputs=[types.SimpleNamespace(text=a) for a in answers])
        class LLM:
            def __init__(self, **kw):
                pass
            def generate(self, prompts, sampling_params, **kw):
                calls.append((len(prompts), vars(sampling_params)))
                if len(calls) == 1:
                    return [response([r"\boxed{INVALID}"] * 5 + [r"\boxed{1}"] * 4)] + [response([r"\boxed{1}"] * 9) for _ in range(5)]
                panels = [["1"] * 4 + ["2"] * 3 + ["3"] * 2,
                          ["1"] * 8 + ["2"], [], ["1"] * 5 + ["2"] * 4,
                          ["1"] * 6 + ["2"] * 3]
                return [response(["\\boxed{" + a + "}" for a in answers] if answers else ["no answer"] * 9) for answers in panels]
        vllm.LLM = LLM
        modules = {"vllm": vllm, "transformers": transformers, "mathruler": mathruler,
                   "mathruler.grader": grader, "stopit": stopit, "jinja2": jinja}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            questions = ["invalid", "same question", "too easy", "missing math", "a box question", "same question"]
            candidates = [{"question": q, "answer": "1", "score": 0, "sample_id": f"s{i}",
                           "request_id": f"r{i // 3}", "question_position": i % 3 + 1,
                           "request_index": i // 3, "shard": 0} for i, q in enumerate(questions)]
            atomic_json(root / "generated_question/three_questions_0.json", candidates)
            env = {"STORAGE_PATH": str(root), "VALIDITY_RZERO_ENABLED": "1",
                   "VALIDITY_RZERO_PROMPT": str(REPO / "methods/validity_rl/validity_solver.jinja")}
            # Ensure real gating imports the fake external grader for this test only.
            cached = {k: sys.modules.pop(k) for k in ("methods.validity_rzero.gating", "methods.validity_rl.validity_reward") if k in sys.modules}
            try:
                with patch.dict(sys.modules, modules), patch.dict(os.environ, env), patch.object(sys, "argv", ["evaluate", "--save_name", "three_questions"]), contextlib.redirect_stdout(io.StringIO()):
                    runpy.run_path(str(METHOD / "evaluate_snapshot.py"), run_name="__main__")
            finally:
                for name in ("methods.validity_rzero.gating", "methods.validity_rl.validity_reward"):
                    sys.modules.pop(name, None)
                sys.modules.update(cached)
            evaluated = json.loads((root / "generated_question/three_questions_0_results.json").read_text())
            # Production treats mathruler's literal "None" as truthy in its answer list;
            # that row survives evaluation but is rejected by passes_rzero_filter.
            self.assertEqual([r["sample_id"] for r in evaluated], ["s0", "s1", "s2", "s3", "s5"])
            self.assertTrue(evaluated[0]["discarded_by_validity"])
            self.assertAlmostEqual(evaluated[1]["score"], 4 / 9)
            self.assertEqual([c[0] for c in calls], [6, 5])
            for _, params in calls:
                self.assertEqual(params, {"max_tokens": 4096, "temperature": 1.0, "top_p": 1.0,
                                          "top_k": 40, "stop_token_ids": [0], "n": 9})
            # Collation must preserve positions across skipped and duplicate questions.
            atomic_json(root / "generation/shard_0_candidates.json", candidates)
            atomic_jsonl(root / "generation/shard_0_raw.jsonl", [
                {"finish_reason": "stop", "parsed_count": 3, "extra_blocks_ignored": 0} for _ in range(2)])
            atomic_json(root / "workspace/generated_question/three_questions_0_results.json", evaluated)
            summary = collect(root, 1)
            self.assertEqual(summary["retained_count"], 2)
            self.assertEqual(summary["omitted_by_original_evaluator_count"], 1)
            kept = json.loads((root / "datasets/round_4.json").read_text())
            self.assertEqual([(r["sample_id"], r["question_position"]) for r in kept], [("s1", 2), ("s5", 3)])


if __name__ == "__main__":
    unittest.main()
