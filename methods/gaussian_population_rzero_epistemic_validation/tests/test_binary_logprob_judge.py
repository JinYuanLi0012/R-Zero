from __future__ import annotations

import math
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

METHOD = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(METHOD))

from binary_logprob_common import (  # noqa: E402
    DIRECT_EXAMPLES, INVALID_CANDIDATE, SOLVER_FIRST_EXAMPLES, VALID_CANDIDATE,
    build_prompt, candidate_logprob, paired_probability,
)
from binary_logprob_analyze import main as analyze_main  # noqa: E402
from binary_logprob_worker import completed, score_candidates  # noqa: E402


class FakeLogprob:
    def __init__(self, value: float):
        self.logprob = value


class FakeOutput:
    def __init__(self, context_ids, candidate_ids, values):
        self.prompt_token_ids = context_ids + candidate_ids
        self.prompt_logprobs = [None] * len(context_ids) + [
            {token_id: FakeLogprob(value)} for token_id, value in zip(candidate_ids, values)
        ]


class PromptTests(unittest.TestCase):
    def test_prompts_are_binary_few_shot_and_blind(self):
        for variant in ("direct", "solver_first"):
            prompt = build_prompt("What is 7 + 8?", variant)
            self.assertIn("What is 7 + 8?", prompt)
            self.assertIn("Verdict: VALID", prompt)
            self.assertIn("Verdict: INVALID", prompt)
            self.assertTrue(prompt.endswith("Analysis:"))
            for leaked in ("terra_label", "difficulty=", "sigma=", "v3:secret"):
                self.assertNotIn(leaked, prompt)

    def test_examples_are_synthetic_and_teach_find_all_as_valid(self):
        self.assertIn("Solve x^2 = 4", DIRECT_EXAMPLES)
        self.assertIn("Verdict: VALID", SOLVER_FIRST_EXAMPLES)
        self.assertNotIn("1729", DIRECT_EXAMPLES + SOLVER_FIRST_EXAMPLES)

    def test_variants_have_different_task_interfaces(self):
        direct = build_prompt("Q", "direct")
        solver = build_prompt("Q", "solver_first")
        self.assertNotEqual(direct, solver)
        self.assertIn("Solve the target problem carefully first", solver)


class LogprobTests(unittest.TestCase):
    def test_candidate_sequence_logprob_sums_all_tokens(self):
        output = FakeOutput([10, 11], [20, 21], [-0.2, -0.3])
        self.assertAlmostEqual(candidate_logprob(output, 2, [20, 21]), -0.5)

    def test_two_candidate_softmax(self):
        probability = paired_probability(math.log(3), math.log(1))
        self.assertAlmostEqual(probability, 0.75)
        self.assertGreater(paired_probability(-0.1, -2.0), 0.5)

    def test_candidates_include_leading_space(self):
        self.assertEqual(VALID_CANDIDATE, " VALID")
        self.assertEqual(INVALID_CANDIDATE, " INVALID")

    def test_scoring_micro_batches_limit_full_vocabulary_work(self):
        class FakeTokenizer:
            def encode(self, text, add_special_tokens=False):
                if text == VALID_CANDIDATE:
                    return [20]
                if text == INVALID_CANDIDATE:
                    return [21]
                return [10, 11]

        class FakeVllm:
            @staticmethod
            def SamplingParams(**kwargs):
                return kwargs

        class FakeLlm:
            def __init__(self):
                self.prompt_counts = []

            def generate(self, prompts, prompt_token_ids, sampling_params, use_tqdm):
                self.prompt_counts.append(len(prompt_token_ids))
                return [
                    FakeOutput(ids[:-1], ids[-1:], [-0.1 if ids[-1] == 20 else -1.0])
                    for ids in prompt_token_ids
                ]

        llm = FakeLlm()
        rows = score_candidates(llm, FakeVllm, FakeTokenizer(), ["a", "b", "c"])
        self.assertEqual(llm.prompt_counts, [1, 1, 1, 1, 1, 1])
        self.assertEqual([row["verdict"] for row in rows], ["VALID"] * 3)


class AnalysisIntegrationTests(unittest.TestCase):
    def test_saved_results_rebuild_metrics_for_both_variants(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            terra_path = root / "terra.jsonl"
            results_path = root / "results.jsonl"
            output_dir = root / "analysis"
            terra_rows = [
                {"question_id": "q1", "round": 1, "label": "A"},
                {"question_id": "q2", "round": 2, "label": "D"},
                {"question_id": "q3", "round": 3, "label": "C"},
            ]
            results = []
            for row in terra_rows:
                for variant in ("direct", "solver_first"):
                    verdict = "VALID" if row["label"] == "A" else "INVALID"
                    results.append(
                        {
                            "question_id": row["question_id"], "round": row["round"],
                            "question": f"Question {row['question_id']}", "variant": variant,
                            "status": "success", "verdict": verdict,
                            "valid_score": 0.9 if verdict == "VALID" else 0.1,
                            "analysis": "Synthetic fixture analysis.",
                            "analysis_truncated": False, "analysis_token_count": 4,
                            "valid_candidate_token_ids": [1],
                            "invalid_candidate_token_ids": [2],
                        }
                    )
            for path, rows in ((terra_path, terra_rows), (results_path, results)):
                path.write_text(
                    "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
                )
            argv = [
                "binary_logprob_analyze.py", "--results", str(results_path),
                "--terra-results", str(terra_path), "--output-dir", str(output_dir),
                "--expected-count", "3",
            ]
            with patch.object(sys, "argv", argv):
                analyze_main()
            metrics = json.loads((output_dir / "metrics.json").read_text(encoding="utf-8"))
            self.assertEqual(metrics["scopes"]["overall"]["direct"]["invalid_recall"], 1.0)
            self.assertEqual(metrics["scopes"]["overall"]["solver_first"]["roc_auc"], 1.0)
            self.assertEqual(metrics["prompt_comparison"]["paired_count"], 3)
            self.assertTrue((output_dir / "report.md").is_file())


class RuntimeConfigurationTests(unittest.TestCase):
    def test_prompt_logprob_scoring_disables_prefix_cache(self):
        source = (METHOD / "binary_logprob_worker.py").read_text(encoding="utf-8")
        self.assertIn("enable_prefix_caching=False", source)
        self.assertNotIn("enable_prefix_caching=True", source)

    def test_logprob_scoring_defaults_to_one_question_micro_batches(self):
        worker = (METHOD / "binary_logprob_worker.py").read_text(encoding="utf-8")
        launcher = (METHOD / "binary_logprob_judge.py").read_text(encoding="utf-8")
        self.assertIn('parser.add_argument("--score-batch-size", type=int, default=1)', worker)
        self.assertIn('parser.add_argument("--score-batch-size", type=int, default=1)', launcher)
        self.assertIn('parser.add_argument("--gpu-memory-utilization", type=float, default=0.7)', worker)
        self.assertIn('parser.add_argument("--gpu-memory-utilization", type=float, default=0.7)', launcher)

    def test_resume_rejects_a_different_generation_length(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "artifact.json"
            path.write_text(
                json.dumps(
                    {
                        "status": "success",
                        "model": "Qwen/Qwen3-4B-Base",
                        "variant": "solver_first",
                        "experiment_version": "binary-fewshot-logprob-v2",
                        "max_analysis_tokens": 1024,
                    }
                ),
                encoding="utf-8",
            )
            self.assertTrue(completed(path, "Qwen/Qwen3-4B-Base", "solver_first", 1024))
            self.assertFalse(completed(path, "Qwen/Qwen3-4B-Base", "solver_first", 2048))


if __name__ == "__main__":
    unittest.main()
