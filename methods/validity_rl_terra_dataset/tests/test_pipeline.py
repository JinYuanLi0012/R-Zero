from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


METHOD_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(METHOD_DIR))

from annotate import ANSWER_SCHEMA, VALIDITY_SCHEMA, label_consistent, run_one, validate_exact
from batch_annotate import make_batch_row, run_batch_pass
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
                "gpt-5.6-sol", 3, 0.8, "high", 1024, fixture,
            )
            self.assertEqual(artifact["status"], "complete")
            self.assertEqual(len(artifact["attempts"]), 2)
            self.assertEqual(artifact["result"]["canonical_final_answer"], "2")

    def test_batch_request_is_blind_and_uses_responses_schema(self):
        row = make_batch_row(
            {"id": "q_opaque", "question": "What is 1+1?"},
            "validity", 1, "gpt-5.6-sol", "high", 16384,
        )
        self.assertEqual(row["custom_id"], "validity:q_opaque:a1")
        self.assertEqual(row["url"], "/v1/responses")
        self.assertEqual(row["body"]["model"], "gpt-5.6-sol")
        serialized = json.dumps(row)
        self.assertIn("q_opaque", serialized)
        self.assertIn("What is 1+1?", serialized)
        self.assertNotIn("round", serialized)
        self.assertNotIn("split", serialized)
        self.assertNotIn("score", serialized)

    def test_batch_pass_downloads_by_custom_id_and_retries_uncertain_answer(self):
        class FakeObject(SimpleNamespace):
            def model_dump(self, mode="json"):
                del mode
                return dict(self.__dict__)

        class FakeFiles:
            def __init__(self):
                self.values = {}
                self.next_id = 1

            def create(self, file, purpose):
                self.assert_purpose = purpose
                file_id = f"file-input-{self.next_id}"
                self.next_id += 1
                self.values[file_id] = file.read()
                return FakeObject(id=file_id)

            def content(self, file_id):
                return FakeObject(content=self.values[file_id])

        class FakeBatches:
            def __init__(self, files):
                self.files = files
                self.values = {}
                self.created = 0

            def create(self, input_file_id, endpoint, completion_window, metadata):
                self.assert_endpoint = endpoint
                self.assert_window = completion_window
                self.assert_metadata = metadata
                self.created += 1
                batch_id = f"batch-{self.created}"
                requests = [
                    json.loads(line) for line in self.files.values[input_file_id].decode().splitlines()
                ]
                output = []
                errors = []
                for request in reversed(requests):  # Batch output order is intentionally different.
                    custom_id = request["custom_id"]
                    if custom_id == "validity:q_two:a1":
                        errors.append(json.dumps({
                            "custom_id": custom_id,
                            "response": None,
                            "error": {"code": "temporary_error", "message": "retry me"},
                        }))
                        continue
                    if custom_id.startswith("validity:"):
                        parsed = valid_judgment("D" if ":q_two:" in custom_id else "A")
                    elif custom_id.endswith(":a1"):
                        parsed = {
                            "solution_summary": "Not fully checked.", "verification_checks": [],
                            "canonical_final_answer": None, "answer_verified": False,
                            "confidence": 0.5, "uncertainty_reason": "Need another attempt.",
                        }
                    else:
                        parsed = {
                            "solution_summary": "Solved and checked.",
                            "verification_checks": ["Substitution checked."],
                            "canonical_final_answer": "2", "answer_verified": True,
                            "confidence": 0.99, "uncertainty_reason": None,
                        }
                    output.append(json.dumps({
                        "custom_id": custom_id,
                        "response": {"status_code": 200, "body": {
                            "model": "gpt-5.6-sol",
                            "output": [{"type": "message", "content": [{
                                "type": "output_text", "text": json.dumps(parsed),
                            }]}],
                        }},
                        "error": None,
                    }))
                output_file_id = f"file-output-{self.created}"
                self.files.values[output_file_id] = ("\n".join(output) + "\n").encode()
                error_file_id = None
                if errors:
                    error_file_id = f"file-error-{self.created}"
                    self.files.values[error_file_id] = ("\n".join(errors) + "\n").encode()
                snapshot = {
                    "id": batch_id, "status": "completed", "output_file_id": output_file_id,
                    "error_file_id": error_file_id,
                    "request_counts": {
                        "total": len(requests), "completed": len(output), "failed": len(errors),
                    },
                    "errors": None,
                }
                self.values[batch_id] = snapshot
                return FakeObject(**snapshot)

            def retrieve(self, batch_id):
                return FakeObject(**self.values[batch_id])

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            files = FakeFiles()
            client = SimpleNamespace(files=files, batches=FakeBatches(files))
            items = [
                {"id": "q_one", "question": "What is 1+1?"},
                {"id": "q_two", "question": "What is 2+2?"},
            ]
            validity = run_batch_pass(
                client, items, "validity", root, "gpt-5.6-sol", "high", 16384, 3, 0.8, 5,
            )
            self.assertTrue(all(row["status"] == "complete" for row in validity))
            self.assertEqual(
                {row["id"]: row["result"]["label"] for row in validity},
                {"q_one": "A", "q_two": "D"},
            )
            self.assertEqual(len(validity[1]["attempts"]), 2)
            self.assertEqual(validity[1]["attempts"][0]["error_type"], "BatchRequestError")
            created_after_validity = client.batches.created
            resumed = run_batch_pass(
                client, items, "validity", root, "gpt-5.6-sol", "high", 16384, 3, 0.8, 5,
            )
            self.assertEqual(client.batches.created, created_after_validity)
            self.assertEqual([row["result"]["label"] for row in resumed], ["A", "D"])
            answers = run_batch_pass(
                client, items[:1], "answer", root, "gpt-5.6-sol", "high", 16384, 3, 0.8, 5,
            )
            self.assertEqual(answers[0]["status"], "complete")
            self.assertEqual(answers[0]["result"]["canonical_final_answer"], "2")
            self.assertEqual(len(answers[0]["attempts"]), 2)
            answer_state = json.loads((root / "batch/answer/state.json").read_text())
            self.assertEqual(len(answer_state["batches"]), 2)

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
