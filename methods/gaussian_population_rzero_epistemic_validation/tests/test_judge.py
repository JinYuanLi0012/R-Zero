from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

METHOD_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(METHOD_DIR))

from common import question_hash
from judge import JUDGE_SCHEMA, label_consistent


class JudgeTests(unittest.TestCase):
    def test_schema_is_strict_and_valid_a_is_consistent(self):
        self.assertFalse(JUDGE_SCHEMA["additionalProperties"])
        value = {
            "label": "A", "conditions_complete": True, "contradictory": False,
            "multiple_reasonable_interpretations": False, "solution_exists": True,
            "unique_or_explicit_grading": True,
        }
        self.assertTrue(label_consistent(value))

    def test_fixture_pipeline_writes_only_blind_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            question = "What is 1+1?"
            source = root / "input.jsonl"
            source.write_text(json.dumps({
                "question_id": f"v1:0:{question_hash(question)[:16]}", "question_hash": question_hash(question),
                "question": question, "round": 1, "original_difficulty": 0.4,
            }) + "\n", encoding="utf-8")
            subprocess.run(
                [sys.executable, str(METHOD_DIR / "judge.py"), "--input", str(source),
                 "--output-dir", str(root / "judge"), "--fixture", str(Path(__file__).with_name("judge_fixture.json")),
                 "--human-review-size", "1"], check=True,
            )
            blind = json.loads((root / "judge" / "blind_input.jsonl").read_text(encoding="utf-8"))
            self.assertEqual(set(blind), {"opaque_judge_id", "question"})
            self.assertNotIn("round", blind)
            self.assertNotIn("score", blind)
            result = json.loads((root / "judge" / "judge_results.jsonl").read_text(encoding="utf-8"))
            self.assertEqual(result["label"], "A")
            self.assertNotIn("label_pass2", result)
            manifest = json.loads((root / "judge" / "judge_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["api_calls_per_unique_question"], 1)


if __name__ == "__main__":
    unittest.main()
