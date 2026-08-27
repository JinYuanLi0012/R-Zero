import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from qwen35.rzero.diagnostics.analyze_questioner_rollouts import analyze
from qwen35.rzero.diagnostics.questioner_candidate_gate import prepare_candidates, summarize_gate
from qwen35.rzero.diagnostics.questioner_one_step import configure_node_caches


class FakeTokenizer:
    def encode(self, text, add_special_tokens=False):
        del add_special_tokens
        return text.split()


class QuestionerThinkingOffGateTests(unittest.TestCase):
    def test_raw_diagnostic_records_adapt_to_released_candidate_schema(self):
        candidates = prepare_candidates(
            [
                {"parsed_question": "What is 2+3?", "parsed_answer": "5", "raw_response": "raw valid"},
                {"parsed_question": "", "parsed_answer": "", "raw_response": "raw invalid"},
            ]
        )
        self.assertEqual(candidates[0], {"question": "What is 2+3?", "answer": "5", "score": 0})
        self.assertEqual(candidates[1], {"question": "raw invalid", "answer": "", "score": -1})

    def test_candidate_gate_reports_none_votes_and_released_difficulty_filter(self):
        candidates = [
            {"question": "q0", "answer": "a", "score": 0},
            {"question": "q1", "answer": "b", "score": 0},
            {"question": "bad", "answer": "", "score": -1},
        ]
        scored = [
            {"question": "q0", "answer": "42", "score": 1 / 3, "results": ["42"] * 9},
            {"question": "q1", "answer": "None", "score": 7 / 9, "results": ["None"] * 9},
        ]
        summary = summarize_gate(candidates, scored)
        self.assertEqual(summary["parseable_candidates"], 2)
        self.assertEqual(summary["scored_candidates"], 2)
        self.assertEqual(summary["majority_none"], 1)
        self.assertEqual(summary["accepted_0.3_to_0.8"], 1)
        self.assertEqual(summary["accepted_questions"], ["q0"])
        self.assertFalse(summary["semantics"]["deduplication"])
        self.assertFalse(summary["semantics"]["repeat_to_minimum"])

    def test_gate_redirects_compiler_caches_to_job_local_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "job-cache"
            with patch.dict(
                os.environ,
                {"RZERO_NODE_CACHE_ROOT": str(root)},
                clear=False,
            ):
                cache_keys = (
                    "XDG_CACHE_HOME",
                    "TRITON_CACHE_DIR",
                    "TORCHINDUCTOR_CACHE_DIR",
                    "CUDA_CACHE_PATH",
                    "VLLM_CACHE_ROOT",
                    "FLASHINFER_WORKSPACE_BASE",
                    "TMPDIR",
                )
                previous = {key: os.environ.pop(key, None) for key in cache_keys}
                try:
                    self.assertEqual(configure_node_caches(), root)
                    for key in cache_keys:
                        self.assertTrue(Path(os.environ[key]).is_dir())
                        self.assertTrue(Path(os.environ[key]).is_relative_to(root))
                finally:
                    for key in cache_keys:
                        os.environ.pop(key, None)
                        if previous[key] is not None:
                            os.environ[key] = previous[key]

    def test_rollout_summary_preserves_reward_components_and_parse_rate(self):
        rows = [
            {
                "output": "<question>What is 2 plus 3?</question> \\boxed{5}",
                "format": 1.0,
                "solver_difficulty": 0.4,
                "diversity_penalty": 0.25,
                "score": 0.15,
            },
            {
                "output": "unfinished meta loop",
                "format": 0.0,
                "solver_difficulty": -1.0,
                "diversity_penalty": 0.25,
                "score": -1.25,
            },
        ]
        summary = analyze(rows, FakeTokenizer(), max_tokens=3)
        self.assertEqual(summary["total"], 2)
        self.assertEqual(summary["parse_valid"], 1)
        self.assertEqual(summary["reward_format_valid"], 1)
        self.assertEqual(summary["hit_max_tokens_reencoded"], 2)
        self.assertAlmostEqual(summary["solver_difficulty"]["mean"], -0.3)
        self.assertAlmostEqual(summary["solver_difficulty_valid_only"]["mean"], 0.4)
        self.assertAlmostEqual(summary["diversity_penalty"]["mean"], 0.25)
        self.assertAlmostEqual(summary["total_reward"]["mean"], -0.55)


if __name__ == "__main__":
    unittest.main()
