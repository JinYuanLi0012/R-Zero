from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

METHOD = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(METHOD))

from base_judge_common import (  # noqa: E402
    BASE_JUDGE_SCHEMA, SYSTEM_PROMPT, binary_metrics, build_prompt, parse_judgment, roc_auc,
)
from judge import JUDGE_SCHEMA, SYSTEM_PROMPT as TERRA_SYSTEM_PROMPT  # noqa: E402


def judgment() -> dict:
    return {
        "goal_restatement": "Find the integer.",
        "conditions_complete": True,
        "contradictory": False,
        "multiple_reasonable_interpretations": False,
        "solution_exists": True,
        "unique_or_explicit_grading": True,
        "label": "A",
        "confidence": 0.8,
        "probability_label_A": 0.75,
        "issue_types": [],
        "reasoning_summary": "The conditions determine one value.",
        "derived_answer": "2",
    }


class PromptTests(unittest.TestCase):
    def test_prompt_contains_only_question_not_metadata(self):
        prompt = build_prompt("What is 1+1?")
        self.assertIn("What is 1+1?", prompt)
        for leaked in ("v2:99:secret", "terra-secret-C", "difficulty=0.444", "sigma=0.003"):
            self.assertNotIn(leaked, prompt)

    def test_blind_schema_is_explicit(self):
        self.assertIn("probability_label_A", BASE_JUDGE_SCHEMA["required"])
        self.assertFalse(BASE_JUDGE_SCHEMA["additionalProperties"])

    def test_taxonomy_and_fields_match_terra_with_one_added_probability(self):
        self.assertEqual(SYSTEM_PROMPT, TERRA_SYSTEM_PROMPT)
        self.assertEqual(
            set(BASE_JUDGE_SCHEMA["required"]) - {"probability_label_A"},
            set(JUDGE_SCHEMA["required"]),
        )


class ParserTests(unittest.TestCase):
    def test_parses_direct_and_fenced_json(self):
        payload = json.dumps(judgment())
        self.assertEqual(parse_judgment(payload)["label"], "A")
        self.assertEqual(parse_judgment(f"```json\n{payload}\n```")["probability_label_A"], 0.75)

    def test_rejects_missing_field_and_bad_probability(self):
        value = judgment()
        value.pop("derived_answer")
        with self.assertRaises(ValueError):
            parse_judgment(json.dumps(value))
        value = judgment()
        value["probability_label_A"] = 1.1
        with self.assertRaises(ValueError):
            parse_judgment(json.dumps(value))


class MetricTests(unittest.TestCase):
    def test_binary_metrics_and_always_valid_baseline(self):
        values = binary_metrics([True, True, False, False], [True, False, False, True])
        self.assertEqual((values["tp"], values["tn"], values["fp"], values["fn"]), (1, 1, 1, 1))
        self.assertAlmostEqual(values["balanced_accuracy"], 0.5)
        baseline = binary_metrics([True, True, False, False], [True, True, True, True])
        self.assertEqual(baseline["invalid_recall"], 0.0)
        self.assertEqual(baseline["balanced_accuracy"], 0.5)

    def test_auc_handles_ties(self):
        self.assertAlmostEqual(roc_auc([False, True, False, True], [0.1, 0.9, 0.2, 0.8]), 1.0)
        self.assertAlmostEqual(roc_auc([False, True], [0.5, 0.5]), 0.5)


if __name__ == "__main__":
    unittest.main()
