import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from qwen35.rzero.diagnostics.evaluate_solver_thinking_off import (
    _existing_complete,
    build_summary,
    score_responses,
    validate_comparison_baseline,
)


def output(text, finish_reason="stop", stop_reason=248044, token_count=3):
    return SimpleNamespace(
        text=text,
        finish_reason=finish_reason,
        stop_reason=stop_reason,
        token_ids=list(range(token_count)),
    )


class SolverThinkingOffGateTests(unittest.TestCase):
    def test_preserves_every_raw_rollout_before_released_filtering(self):
        candidates = [
            {"question": "Compute 1+1.", "answer": "2", "score": 0},
            {"question": "Put the answer in a box.", "answer": "3", "score": 0},
        ]
        responses = [
            SimpleNamespace(
                outputs=[
                    output("work \\boxed{2}"),
                    output("no final box", finish_reason="length", stop_reason=None, token_count=4096),
                    output("empty \\boxed{}"),
                ]
            ),
            SimpleNamespace(
                outputs=[output("\\boxed{3}"), output("\\boxed{3}"), output("\\boxed{4}")]
            ),
        ]

        def extract(text):
            if "\\boxed{2}" in text:
                return "2"
            if "\\boxed{3}" in text:
                return "3"
            if "\\boxed{4}" in text:
                return "4"
            if "\\boxed{}" in text:
                return ""
            return "None"

        evidence, scored = score_responses(
            candidates,
            responses,
            extract,
            lambda left, right: left == right,
            max_tokens=4096,
        )

        self.assertEqual(len(evidence), 2)
        self.assertEqual(sum(len(item["rollouts"]) for item in evidence), 6)
        self.assertEqual(evidence[0]["rollouts"][1]["raw_response"], "no final box")
        self.assertTrue(evidence[0]["rollouts"][1]["hit_max_tokens"])
        self.assertEqual(evidence[0]["rollouts"][1]["extracted_answer"], "None")
        self.assertEqual(evidence[0]["rollouts"][2]["extracted_answer"], "")
        self.assertEqual(evidence[0]["results"], ["2", "None"])
        self.assertEqual(evidence[0]["disposition"], "scored")
        self.assertEqual(evidence[1]["disposition"], "dropped_released_filter")
        self.assertEqual(scored, [{"question": "Compute 1+1.", "answer": "2", "score": 0.5, "results": ["2", "None"]}])

    def test_summary_reports_rollout_and_viability_counts_without_curation(self):
        evidence = [
            {
                "disposition": "scored",
                "rollouts": [
                    {"finish_reason": "stop", "stop_reason": 248044, "hit_max_tokens": False, "extracted_answer": "2"},
                    {"finish_reason": "length", "stop_reason": None, "hit_max_tokens": True, "extracted_answer": "None"},
                    {"finish_reason": "stop", "stop_reason": 248044, "hit_max_tokens": False, "extracted_answer": ""},
                ],
            }
        ]
        scored = [{"question": "Q", "answer": "2", "score": 0.5, "results": ["2", "None"]}]
        summary = build_summary(
            [{"score": 0}, {"score": -1}],
            evidence,
            scored,
            {"enable_thinking": False},
            0.3,
            0.8,
            16384,
        )
        self.assertEqual(summary["total_candidates"], 2)
        self.assertEqual(summary["parseable_candidates"], 1)
        self.assertEqual(summary["total_solver_rollouts"], 3)
        self.assertEqual(summary["finish_reasons"], {"length": 1, "stop": 2})
        self.assertEqual(summary["max_tokens"], 16384)
        self.assertEqual(summary["hit_max_tokens"], 1)
        self.assertNotIn("hit_4096", summary)
        self.assertEqual(summary["valid_boxed_answers"], 1)
        self.assertEqual(summary["missing_box_none_answers"], 1)
        self.assertEqual(summary["explicit_empty_box_answers"], 1)
        self.assertEqual(summary["accepted_0.3_to_0.8"], 1)
        self.assertEqual(summary["result_lengths"], {"2": 1})
        self.assertFalse(summary["semantics"]["parquet_created"])

    def test_resume_requires_matching_provenance_and_complete_outputs(self):
        import json

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            summary = root / "summary.json"
            evidence = root / "raw.json"
            scored = root / "scored.json"
            summary.write_text(
                json.dumps(
                    {
                        "provenance": {"input_sha256": "same"},
                        "parseable_candidates": 1,
                        "total_solver_rollouts": 2,
                        "scored_candidates": 1,
                    }
                ),
                encoding="utf-8",
            )
            evidence.write_text(json.dumps([{"rollouts": [{}, {}]}]), encoding="utf-8")
            scored.write_text(json.dumps([{}]), encoding="utf-8")
            self.assertTrue(
                _existing_complete(
                    summary, evidence, scored, {"input_sha256": "same"}
                )
            )
            with self.assertRaisesRegex(RuntimeError, "different inputs"):
                _existing_complete(summary, evidence, scored, {"input_sha256": "other"})

    def test_16k_comparison_requires_every_4k_invariant_to_match(self):
        import json

        invariant = {
            "input_sha256": "candidate-hash",
            "solver_config_sha256": "config-hash",
            "solver_revision": "1001bb4",
            "enable_thinking": False,
            "samples": 9,
            "seed": 0,
            "temperature": 1.0,
            "top_p": 1.0,
            "top_k": 40,
            "stop_semantics": "tokenizer.eos_token_id_only",
            "minimum_score": 0.3,
            "maximum_score": 0.8,
            "expected_total_candidates": 64,
            "expected_parseable_candidates": 60,
        }
        with tempfile.TemporaryDirectory() as temporary:
            baseline_path = Path(temporary) / "summary.json"
            baseline_path.write_text(
                json.dumps(
                    {
                        "provenance": {**invariant, "max_tokens": 4096},
                        "total_candidates": 64,
                        "parseable_candidates": 60,
                        "total_solver_rollouts": 540,
                    }
                ),
                encoding="utf-8",
            )
            comparison = validate_comparison_baseline(baseline_path, invariant, 4096)
            self.assertEqual(comparison["max_tokens"], 4096)
            self.assertEqual(len(comparison["summary_sha256"]), 64)

            changed = {**invariant, "input_sha256": "different-candidates"}
            with self.assertRaisesRegex(RuntimeError, "single-variable match"):
                validate_comparison_baseline(baseline_path, changed, 4096)


if __name__ == "__main__":
    unittest.main()
