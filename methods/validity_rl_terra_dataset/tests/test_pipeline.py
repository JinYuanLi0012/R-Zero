from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


METHOD_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(METHOD_DIR))

from annotate import ANSWER_SCHEMA, VALIDITY_SCHEMA, label_consistent, run_one, validate_exact
from common import normalize_question


def valid_judgment(label: str = "A") -> dict:
    is_a = label == "A"
    return {
        "goal_restatement": "Compute the requested value.",
        "conditions_complete": is_a,
        "contradictory": label == "D",
        "multiple_reasonable_interpretations": label == "C",
        "solution_exists": label != "D",
        "unique_or_explicit_grading": is_a,
        "label": label,
        "confidence": 0.95,
        "issue_types": [] if is_a else ["no solution"],
        "reasoning_summary": "Checked the conditions.",
        "derived_answer": "2" if is_a else None,
        "invalid_type": None if is_a else "no_solution",
    }


class PipelineTests(unittest.TestCase):
    def test_strict_schemas_and_consistency(self):
        self.assertFalse(VALIDITY_SCHEMA["additionalProperties"])
        self.assertFalse(ANSWER_SCHEMA["additionalProperties"])
        self.assertTrue(label_consistent(valid_judgment()))
        invalid = valid_judgment("D")
        self.assertTrue(label_consistent(invalid))
        validate_exact(invalid, VALIDITY_SCHEMA, "validity")

    def test_normalization_deduplicates_line_endings_and_trailing_space(self):
        self.assertEqual(normalize_question(" x  \r\n y\n"), "x\n y")

    def test_uncertain_answer_is_retried(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            uncertain = {
                "solution_summary": "Could not finish.", "verification_checks": [],
                "canonical_final_answer": None, "answer_verified": False,
                "confidence": 0.4, "uncertainty_reason": "Verification incomplete.",
            }
            verified = {
                "solution_summary": "Solved and checked.", "verification_checks": ["Checked."],
                "canonical_final_answer": "2", "answer_verified": True,
                "confidence": 0.95, "uncertainty_reason": None,
            }
            fixture = root / "fixture.json"
            fixture.write_text(json.dumps({"default": [uncertain, verified]}), encoding="utf-8")
            artifact = run_one(
                {"id": "q_test", "question": "What is 1+1?"}, "answer", root / "result.json",
                "gpt-5.6", 3, 0.8, "high", 1024, fixture,
            )
            self.assertEqual(artifact["status"], "complete")
            self.assertEqual(len(artifact["attempts"]), 2)
            self.assertEqual(artifact["result"]["canonical_final_answer"], "2")

    def test_end_to_end_fixture_is_blind_and_balanced(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "output"
            source_args = []
            for round_index in range(1, 6):
                source = root / f"v{round_index}.jsonl"
                with source.open("w", encoding="utf-8") as handle:
                    for item_index in range(4):
                        question = (
                            "A duplicate across every round: what is 1+1?" if item_index == 0 else
                            f"Round {round_index} unique problem {item_index}: what is 1+1?"
                        )
                        handle.write(json.dumps({
                            "problem": question,
                            "answer": "historical answer must stay private", "score": 0.5,
                        }) + "\n")
                source_args.extend(["--source", f"v{round_index}={source}"])

            subprocess.run([
                sys.executable, str(METHOD_DIR / "prepare.py"), "--output-dir", str(output),
                "--per-round", "2", "--train-per-round", "1", *source_args,
            ], check=True)
            blind = [json.loads(line) for line in (output / "terra_blind_input.jsonl").read_text().splitlines()]
            self.assertEqual(len(blind), 10)
            self.assertTrue(all(set(row) == {"id", "question"} for row in blind))
            self.assertEqual(len({row["question"] for row in blind}), 10)
            prepare_manifest = json.loads((output / "prepare_manifest.json").read_text())
            self.assertEqual(
                prepare_manifest["sampling_statistics"]["duplicate_occurrences_removed"], 4
            )

            validity_fixture = root / "validity.json"
            payload = {"default": valid_judgment("D")}
            payload[blind[0]["id"]] = valid_judgment("A")
            validity_fixture.write_text(json.dumps(payload), encoding="utf-8")
            answer_fixture = root / "answer.json"
            answer_fixture.write_text(json.dumps({"default": {
                "solution_summary": "One plus one is two.",
                "verification_checks": ["Substitution checked."],
                "canonical_final_answer": "2", "answer_verified": True,
                "confidence": 0.99, "uncertainty_reason": None,
            }}), encoding="utf-8")
            subprocess.run([
                sys.executable, str(METHOD_DIR / "annotate.py"),
                "--input", str(output / "terra_blind_input.jsonl"),
                "--output-dir", str(output), "--validity-fixture", str(validity_fixture),
                "--answer-fixture", str(answer_fixture),
            ], check=True)
            subprocess.run([
                sys.executable, str(METHOD_DIR / "finalize.py"), "--output-dir", str(output),
            ], check=True)

            stats = json.loads((output / "analysis/dataset_statistics.json").read_text())
            self.assertEqual(stats["total_terra_annotation_questions"], 10)
            self.assertEqual(stats["sampled_round_counts"], {f"v{i}": 2 for i in range(1, 6)})
            self.assertEqual(stats["terra_validity_counts"], {"INVALID": 9, "VALID": 1})
            rows = [
                json.loads(line) for path in (output / "train.jsonl", output / "validation.jsonl")
                for line in path.read_text().splitlines()
            ]
            self.assertEqual(len(rows), 10)
            self.assertNotIn("score", rows[0])
            self.assertNotIn("historical_answer", rows[0])
            self.assertTrue(all(row["validity_rl_target"] for row in rows))


if __name__ == "__main__":
    unittest.main()
