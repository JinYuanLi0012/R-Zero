from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


METHOD_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(METHOD_DIR))

from build_clean_dataset import build_clean_rows, main
from common import write_jsonl


def base_row(item_id: str, split: str, validity: str) -> dict:
    answer = "42" if validity == "VALID" else None
    return {
        "id": item_id, "round": "v1", "question": f"Question {item_id}",
        "terra_validity": validity, "canonical_final_answer": answer,
        "answer_verified": True if validity == "VALID" else None,
        "invalid_type": None if validity == "VALID" else "BROKEN_PROBLEM",
        "split": split, "terra_label": "A" if validity == "VALID" else "B",
        "validity_rl_target": answer if validity == "VALID" else "INVALID",
    }


def audit_row(item_id: str, disposition: str, split: str = "train") -> dict:
    return {
        "id": item_id, "round": "v1", "split": split,
        "question": f"Question {item_id}", "canonical_final_answer": "42",
        "disposition": disposition,
    }


class BuildCleanDatasetTests(unittest.TestCase):
    def fixture(self):
        train = [
            base_row("q_invalid_train", "train", "INVALID"),
            base_row("q_pass", "train", "VALID"),
            base_row("q_keep", "train", "VALID"),
            base_row("q_replace", "train", "VALID"),
        ]
        validation = [
            base_row("q_invalid_val", "validation", "INVALID"),
            base_row("q_human", "validation", "VALID"),
        ]
        passed = [audit_row("q_pass", "PASS")]
        suspects = [
            audit_row("q_keep", "SUSPECT"), audit_row("q_replace", "SUSPECT"),
            audit_row("q_human", "SUSPECT", "validation"),
            audit_row("q_preexisting", "SUSPECT"),
        ]
        deep = [
            {**row, "final_action": action, "decision_reasons": []}
            for row, action in zip(suspects, (
                "KEEP_CANONICAL", "REPLACEMENT_CANDIDATE", "HUMAN_REVIEW", "EXCLUDE",
            ))
        ]
        return train, validation, passed, suspects, deep

    def test_keeps_only_pass_and_keep_valid_while_retaining_all_invalid(self):
        clean_train, clean_validation, excluded, stats = build_clean_rows(
            *self.fixture(), expected=None,
        )
        self.assertEqual(
            [row["id"] for row in clean_train], ["q_invalid_train", "q_keep", "q_pass"],
        )
        self.assertEqual([row["id"] for row in clean_validation], ["q_invalid_val"])
        self.assertEqual(
            [row["id"] for row in excluded], ["q_human", "q_preexisting", "q_replace"],
        )
        self.assertEqual(stats["clean_total"], 4)
        self.assertEqual(stats["clean_valid"], 2)
        self.assertEqual(stats["clean_invalid"], 2)
        self.assertFalse(stats["policy"]["replacement_candidates_applied"])
        self.assertTrue(stats["accounting_check"])

    def test_rejects_incomplete_deep_review_accounting(self):
        train, validation, passed, suspects, deep = self.fixture()
        with self.assertRaisesRegex(ValueError, "deep-review/suspect ID mismatch"):
            build_clean_rows(train, validation, passed, suspects, deep[:-1], expected=None)

    def test_rejects_production_count_mismatch_by_default(self):
        with self.assertRaisesRegex(ValueError, "production accounting mismatch"):
            build_clean_rows(*self.fixture())

    def test_does_not_mutate_training_rows(self):
        train, validation, passed, suspects, deep = self.fixture()
        original = [dict(row) for row in train]
        clean_train, _, _, _ = build_clean_rows(
            train, validation, passed, suspects, deep, expected=None,
        )
        self.assertEqual(train, original)
        self.assertEqual(clean_train[0], train[0])

    def test_rejects_keep_row_missing_from_base_dataset(self):
        train, validation, passed, suspects, deep = self.fixture()
        deep[-1]["final_action"] = "KEEP_CANONICAL"
        with self.assertRaisesRegex(ValueError, "deep-review KEEP row"):
            build_clean_rows(train, validation, passed, suspects, deep, expected=None)

    def test_cli_writes_clean_dataset_report_and_hash_manifest(self):
        train, validation, passed, suspects, deep = self.fixture()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, audit, review, output = (
                root / "source", root / "audit", root / "review", root / "clean",
            )
            write_jsonl(source / "train.jsonl", train)
            write_jsonl(source / "validation.jsonl", validation)
            write_jsonl(audit / "passed.jsonl", passed)
            write_jsonl(audit / "suspect.jsonl", suspects)
            write_jsonl(review / "deep_review_results.jsonl", deep)
            argv = [
                "build_clean_dataset.py", str(source), str(audit), str(review),
                "--output-dir", str(output), "--allow-nonstandard-counts",
            ]
            with patch.object(sys, "argv", argv):
                main()
            for relative in (
                "train.jsonl", "validation.jsonl", "excluded_valid.jsonl",
                "manifest.json", "analysis/statistics.json", "analysis/report.md",
            ):
                self.assertTrue((output / relative).is_file(), relative)
            manifest = json.loads((output / "manifest.json").read_text())
            self.assertEqual(set(manifest["input_sha256"]), {
                "source_train", "source_validation", "audit_passed", "audit_suspect",
                "deep_review_results",
            })
            self.assertEqual(set(manifest["output_sha256"]), {
                "clean_train", "clean_validation", "excluded_valid", "statistics", "report",
            })


if __name__ == "__main__":
    unittest.main()
