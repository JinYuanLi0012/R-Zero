from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


METHOD_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(METHOD_DIR))

from answer_consistency_audit import (
    AUDIT_SCHEMA,
    build_results,
    create_record,
    make_batch_row,
    make_statistics,
    prepare_audit_inputs,
    render_report,
    run_batch_audit,
    state_config,
)
from common import atomic_json, write_jsonl


def audit_result(**overrides):
    value = {
        "goal_summary": "Compute the requested value.",
        "question_status": "CLEAR",
        "canonical_status": "CORRECT",
        "derived_status": "CORRECT",
        "derived_canonical_relation": "AGREE",
        "canonical_matches_request": True,
        "preferred_final_answer": "2",
        "needs_deep_review": False,
        "confidence": 0.95,
        "reasoning_summary": "Independently checked.",
    }
    value.update(overrides)
    return value


class FakeObject(SimpleNamespace):
    def model_dump(self, mode="json"):
        del mode
        return dict(self.__dict__)


class FakeFiles:
    def __init__(self):
        self.values = {}
        self.next_id = 1

    def create(self, file, purpose):
        if purpose != "batch":
            raise AssertionError(purpose)
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

    def parsed_for(self, item_id, attempt):
        if item_id == "q_equiv":
            return audit_result(derived_canonical_relation="EQUIVALENT")
        if item_id == "q_conflict":
            return audit_result(
                canonical_status="INCORRECT", derived_canonical_relation="CONFLICT",
                preferred_final_answer="3", needs_deep_review=True,
            )
        if item_id == "q_bad":
            return audit_result(
                canonical_status="INCORRECT", canonical_matches_request=False,
                needs_deep_review=True,
            )
        if item_id == "q_ambig":
            return audit_result(question_status="AMBIGUOUS", needs_deep_review=True)
        if item_id == "q_low":
            return audit_result(confidence=0.79)
        return audit_result()

    def create(self, input_file_id, endpoint, completion_window, metadata):
        self.created += 1
        if endpoint != "/v1/responses" or completion_window != "24h":
            raise AssertionError((endpoint, completion_window))
        if metadata["pass"] != "consistency":
            raise AssertionError(metadata)
        batch_id = f"batch-{self.created}"
        requests = [
            json.loads(line) for line in self.files.values[input_file_id].decode().splitlines()
        ]
        output, errors = [], []
        for request in reversed(requests):
            custom_id = request["custom_id"]
            _, item_id, attempt_text = custom_id.split(":")
            attempt = int(attempt_text[1:])
            if item_id == "q_request" and attempt == 1:
                errors.append(json.dumps({
                    "custom_id": custom_id, "response": None,
                    "error": {"code": "temporary_error", "message": "retry"},
                }))
                continue
            text = (
                "not json" if item_id == "q_parse" and attempt == 1
                else json.dumps(self.parsed_for(item_id, attempt))
            )
            output.append(json.dumps({
                "custom_id": custom_id,
                "response": {"status_code": 200, "body": {
                    "model": "fake", "output": [{"type": "message", "content": [
                        {"type": "output_text", "text": text}
                    ]}],
                }},
                "error": None,
            }))
        output_id = f"file-output-{self.created}"
        self.files.values[output_id] = ("\n".join(output) + "\n").encode()
        error_id = None
        if errors:
            error_id = f"file-error-{self.created}"
            self.files.values[error_id] = ("\n".join(errors) + "\n").encode()
        snapshot = {
            "id": batch_id, "status": "completed", "output_file_id": output_id,
            "error_file_id": error_id,
            "request_counts": {
                "total": len(requests), "completed": len(output), "failed": len(errors),
            },
            "errors": None,
        }
        self.values[batch_id] = snapshot
        return FakeObject(**snapshot)

    def retrieve(self, batch_id):
        return FakeObject(**self.values[batch_id])


def fake_client():
    files = FakeFiles()
    return SimpleNamespace(files=files, batches=FakeBatches(files))


class AnswerConsistencyAuditTests(unittest.TestCase):
    def test_schema_and_batch_request_are_strict_and_blind(self):
        self.assertFalse(AUDIT_SCHEMA["additionalProperties"])
        item = {
            "id": "q_opaque", "question": "What is 1+1?",
            "derived_answer": "1+1", "canonical_final_answer": "2",
        }
        row = make_batch_row(item, 1, "gpt-5.6-luna", "high", 8192)
        self.assertEqual(row["custom_id"], "consistency:q_opaque:a1")
        self.assertEqual(row["url"], "/v1/responses")
        serialized = json.dumps(row)
        for value in item.values():
            self.assertIn(value, serialized)
        for forbidden in ("round", "split", "score", "pseudo-answer", "historical reward"):
            self.assertNotIn(forbidden, serialized)

    def test_prepare_joins_valid_rows_and_isolates_unverified(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, output = root / "source", root / "output"
            source.mkdir()
            sampled = [
                {"id": "q_ok", "question": "1+1?", "round": "v1", "split": "train",
                 "score": 0.4, "pseudo_answer": "private"},
                {"id": "q_missing", "question": "2+2?", "round": "v2", "split": "validation"},
                {"id": "q_invalid", "question": "bad", "round": "v3", "split": "train"},
            ]
            raw = [
                {"id": "q_ok", "validity_pass": {"status": "complete", "result": {
                    "label": "A", "derived_answer": "2"}}, "answer_pass": {
                    "status": "complete", "result": {"canonical_final_answer": "2",
                                                       "answer_verified": True, "confidence": .9}}},
                {"id": "q_missing", "validity_pass": {"status": "complete", "result": {
                    "label": "A", "derived_answer": None}}, "answer_pass": {
                    "status": "uncertain", "result": {"canonical_final_answer": None,
                                                        "answer_verified": False}}},
                {"id": "q_invalid", "validity_pass": {"status": "complete", "result": {
                    "label": "C", "derived_answer": None}}, "answer_pass": None},
            ]
            write_jsonl(source / "sampled_questions.jsonl", sampled)
            write_jsonl(source / "terra_raw_results.jsonl", raw)
            verified, unverified, private = prepare_audit_inputs(
                source, output, 3, 2, 1, 1,
            )
            self.assertEqual([row["id"] for row in verified], ["q_ok"])
            self.assertEqual(unverified[0]["suspect_reasons"], ["PREEXISTING_UNVERIFIED"])
            self.assertEqual(private["q_ok"]["round"], "v1")
            blind = json.loads((output / "audit_input.jsonl").read_text().strip())
            self.assertEqual(set(blind), {
                "id", "question", "derived_answer", "canonical_final_answer",
            })
            serialized = (output / "audit_input.jsonl").read_text()
            for forbidden in ("round", "split", "score", "pseudo_answer"):
                self.assertNotIn(forbidden, serialized)

    def test_batch_classification_retries_and_output_order(self):
        ids = [
            "q_agree", "q_equiv", "q_conflict", "q_bad", "q_ambig", "q_low",
            "q_parse", "q_request",
        ]
        items = [{
            "id": item_id, "question": f"Question {item_id}",
            "derived_answer": "2", "canonical_final_answer": "2",
        } for item_id in ids]
        private = {
            item["id"]: {**item, "round": "v1", "split": "train"} for item in items
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            client = fake_client()
            artifacts, _ = run_batch_audit(
                client, items, root, "gpt-5.6-luna", "high", 8192, 3, 0.8, 5,
            )
            results, passed, suspect = build_results(artifacts, private, [], 0.8)
            disposition = {row["id"]: row["disposition"] for row in results}
            self.assertEqual(disposition["q_agree"], "PASS")
            self.assertEqual(disposition["q_equiv"], "PASS")
            for item_id in ("q_conflict", "q_bad", "q_ambig", "q_low"):
                self.assertEqual(disposition[item_id], "SUSPECT")
            self.assertEqual(disposition["q_parse"], "PASS")
            self.assertEqual(disposition["q_request"], "PASS")
            self.assertEqual(len(passed), 4)
            self.assertEqual(len(suspect), 4)
            by_id = {row["id"]: row for row in artifacts}
            self.assertEqual(len(by_id["q_parse"]["attempts"]), 2)
            self.assertEqual(by_id["q_parse"]["attempts"][0]["error_type"], "JSONDecodeError")
            self.assertEqual(len(by_id["q_request"]["attempts"]), 2)
            self.assertEqual(by_id["q_request"]["attempts"][0]["error_type"], "BatchRequestError")
            # A completed rerun uses cached artifacts and submits no more batches.
            created = client.batches.created
            run_batch_audit(client, items, root, "gpt-5.6-luna", "high", 8192, 3, 0.8, 5)
            self.assertEqual(client.batches.created, created)

    def test_resume_existing_batch_id_without_resubmission(self):
        item = {
            "id": "q_resume", "question": "1+1?", "derived_answer": "2",
            "canonical_final_answer": "2",
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            batch_dir = root / "batch"
            batch_dir.mkdir(parents=True)
            config = state_config([item], "gpt-5.6-luna", "high", 8192, 3, 0.8)
            record = create_record([(item, 1)], config, batch_dir, 1)
            client = fake_client()
            with Path(record["input_path"]).open("rb") as handle:
                uploaded = client.files.create(handle, "batch")
            batch = client.batches.create(
                uploaded.id, "/v1/responses", "24h",
                {"pass": "consistency", "sequence": "1"},
            )
            record["input_file_id"] = uploaded.id
            record["batch_id"] = batch.id
            record["submitted_at_utc"] = "before-interruption"
            record["last_batch_snapshot"] = batch.model_dump()
            atomic_json(batch_dir / "state.json", {"config": config, "batches": [record]})
            created = client.batches.created
            artifacts, _ = run_batch_audit(
                client, [item], root, "gpt-5.6-luna", "high", 8192, 3, 0.8, 5,
            )
            self.assertEqual(client.batches.created, created)
            self.assertEqual(artifacts[0]["status"], "complete")

    def test_accounting_report_includes_preexisting_and_is_self_consistent(self):
        items = [
            {
                "id": "q_pass", "question": "1+1?", "derived_answer": "2",
                "canonical_final_answer": "2", "round": "v1", "split": "train",
                "audit_status": "complete", "audit_result": audit_result(),
                "disposition": "PASS", "suspect_reasons": [], "attempts": [{"parsed": {}}],
            },
            {
                "id": "q_old", "question": "2+2?", "derived_answer": None,
                "canonical_final_answer": None, "round": "v2", "split": "validation",
                "audit_status": "PREEXISTING_UNVERIFIED", "audit_result": None,
                "disposition": "SUSPECT", "suspect_reasons": ["PREEXISTING_UNVERIFIED"],
            },
        ]
        stats = make_statistics(items, 1)
        self.assertEqual(stats["total_valid"], 2)
        self.assertEqual(stats["pass"], 1)
        self.assertEqual(stats["suspect"], 1)
        self.assertEqual(stats["preexisting_unverified"], 1)
        self.assertTrue(all(stats["accounting_check"].values()))
        report = render_report(stats)
        self.assertIn("Deep review is needed for 1 SUSPECT samples", report)
        self.assertIn("| v1 | 1 | 0 |", report)
        self.assertIn("| validation | 0 | 1 |", report)


if __name__ == "__main__":
    unittest.main()
