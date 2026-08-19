from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


METHOD_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(METHOD_DIR))

from common import atomic_json, write_jsonl
from suspect_deep_review import (
    REVIEW_SCHEMA,
    build_results,
    create_record,
    deterministic_action,
    load_inputs,
    make_batch_row,
    make_statistics,
    run_batch_review,
    state_config,
    write_outputs,
)


def review_result(**overrides):
    result = {
        "question_status": "CLEAR",
        "independently_derived_answer": "2",
        "independent_answer_verified": True,
        "independent_answer_matches_request": True,
        "canonical_status": "CORRECT",
        "canonical_matches_request": True,
        "derived_sol_relation": "AGREE",
        "canonical_sol_relation": "AGREE",
        "three_way_relation": "ALL_AGREE",
        "recommended_action": "KEEP_CANONICAL",
        "replacement_answer": None,
        "confidence": 0.97,
        "reasoning_summary": "Solved independently and checked by substitution.",
    }
    result.update(overrides)
    return result


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
        file_id = f"input-{self.next_id}"
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

    @staticmethod
    def result_for(item_id):
        if item_id == "q_replace":
            return review_result(
                independently_derived_answer="3", canonical_status="INCORRECT",
                canonical_matches_request=False, derived_sol_relation="AGREE",
                canonical_sol_relation="CONFLICT", three_way_relation="CANONICAL_ONLY_DIFFERS",
                recommended_action="REPLACE_CANONICAL", replacement_answer="3",
            )
        if item_id == "q_ambiguous":
            return review_result(
                question_status="AMBIGUOUS", independently_derived_answer=None,
                independent_answer_verified=False, independent_answer_matches_request=None,
                canonical_status="UNABLE_TO_VERIFY", canonical_matches_request=None,
                derived_sol_relation="NOT_COMPARABLE", canonical_sol_relation="NOT_COMPARABLE",
                three_way_relation="NOT_COMPARABLE", recommended_action="EXCLUDE",
                confidence=0.92,
            )
        if item_id == "q_human":
            return review_result(
                independently_derived_answer="4", derived_sol_relation="CONFLICT",
                canonical_sol_relation="CONFLICT", three_way_relation="ALL_CONFLICT",
                canonical_status="INCORRECT", canonical_matches_request=False,
                recommended_action="REPLACE_CANONICAL", replacement_answer="4",
            )
        return review_result()

    def create(self, input_file_id, endpoint, completion_window, metadata):
        self.created += 1
        if (endpoint, completion_window, metadata["pass"]) != (
            "/v1/responses", "24h", "deep_review",
        ):
            raise AssertionError((endpoint, completion_window, metadata))
        batch_id = f"batch-{self.created}"
        requests = [
            json.loads(line) for line in self.files.values[input_file_id].decode().splitlines()
        ]
        outputs, errors = [], []
        for request in reversed(requests):
            custom_id = request["custom_id"]
            _, item_id, attempt_text = custom_id.split(":")
            attempt = int(attempt_text[1:])
            if item_id == "q_request" and attempt == 1:
                errors.append(json.dumps({
                    "custom_id": custom_id, "response": None,
                    "error": {"code": "temporary", "message": "retry"},
                }))
                continue
            text = (
                "malformed" if item_id == "q_parse" and attempt == 1
                else json.dumps(self.result_for(item_id))
            )
            outputs.append(json.dumps({
                "custom_id": custom_id,
                "response": {"status_code": 200, "body": {
                    "model": "fake", "output": [{"type": "message", "content": [{
                        "type": "output_text", "text": text,
                    }]}],
                }},
                "error": None,
            }))
        output_id = f"output-{self.created}"
        self.files.values[output_id] = ("\n".join(outputs) + "\n").encode()
        error_id = None
        if errors:
            error_id = f"error-{self.created}"
            self.files.values[error_id] = ("\n".join(errors) + "\n").encode()
        snapshot = {
            "id": batch_id, "status": "completed", "output_file_id": output_id,
            "error_file_id": error_id, "errors": None,
            "request_counts": {
                "total": len(requests), "completed": len(outputs), "failed": len(errors),
            },
        }
        self.values[batch_id] = snapshot
        return FakeObject(**snapshot)

    def retrieve(self, batch_id):
        return FakeObject(**self.values[batch_id])


def fake_client():
    files = FakeFiles()
    return SimpleNamespace(files=files, batches=FakeBatches(files))


def blind_item(item_id):
    return {
        "id": item_id, "question": f"Question {item_id}",
        "derived_answer": "2", "canonical_final_answer": "2",
    }


class SuspectDeepReviewTests(unittest.TestCase):
    def test_schema_and_request_are_strict_and_blind(self):
        self.assertFalse(REVIEW_SCHEMA["additionalProperties"])
        item = blind_item("q_opaque")
        row = make_batch_row(item, 1, "gpt-5.6-sol", "high", 16384)
        self.assertEqual(row["custom_id"], "deep-review:q_opaque:a1")
        serialized = json.dumps(row)
        for key in ("id", "question", "derived_answer", "canonical_final_answer"):
            self.assertIn(key, serialized)
        for forbidden in (
            "suspect_reasons", "audit_result", "round", "split", "known error", "Luna",
        ):
            self.assertNotIn(forbidden, serialized)

    def test_loads_exact_113_suspects_and_writes_blind_input(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            audit, output = root / "audit", root / "output"
            rows = [{
                **blind_item(f"q_{index:03d}"), "disposition": "SUSPECT",
                "round": "v1", "split": "train", "suspect_reasons": ["private"],
                "audit_result": {"private": True},
            } for index in range(113)]
            write_jsonl(audit / "suspect.jsonl", rows)
            blind, source = load_inputs(audit, output)
            self.assertEqual(len(blind), 113)
            self.assertEqual(len(source), 113)
            stored = [json.loads(line) for line in (output / "deep_review_input.jsonl").read_text().splitlines()]
            self.assertTrue(all(set(row) == {
                "id", "question", "derived_answer", "canonical_final_answer",
            } for row in stored))
            serialized = (output / "deep_review_input.jsonl").read_text()
            for forbidden in ("round", "split", "suspect_reasons", "audit_result"):
                self.assertNotIn(forbidden, serialized)

    def test_actions_retries_order_and_cached_resume(self):
        ids = ["q_keep", "q_replace", "q_ambiguous", "q_human", "q_parse", "q_request"]
        items = [blind_item(item_id) for item_id in ids]
        source = {
            row["id"]: {**row, "disposition": "SUSPECT", "round": "v1", "split": "train"}
            for row in items
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            client = fake_client()
            artifacts, _ = run_batch_review(
                client, items, root, "gpt-5.6-sol", "high", 16384, 3, 0.9, 5,
            )
            results, groups = build_results(artifacts, source, 0.9)
            actions = {row["id"]: row["final_action"] for row in results}
            self.assertEqual(actions["q_keep"], "KEEP_CANONICAL")
            self.assertEqual(actions["q_replace"], "REPLACEMENT_CANDIDATE")
            self.assertEqual(actions["q_ambiguous"], "EXCLUDE")
            self.assertEqual(actions["q_human"], "HUMAN_REVIEW")
            self.assertEqual(actions["q_parse"], "KEEP_CANONICAL")
            self.assertEqual(actions["q_request"], "KEEP_CANONICAL")
            self.assertEqual(len(groups["REPLACEMENT_CANDIDATE"]), 1)
            by_id = {row["id"]: row for row in artifacts}
            self.assertEqual(by_id["q_parse"]["attempts"][0]["error_type"], "JSONDecodeError")
            self.assertEqual(by_id["q_request"]["attempts"][0]["error_type"], "BatchRequestError")
            created = client.batches.created
            run_batch_review(client, items, root, "gpt-5.6-sol", "high", 16384, 3, 0.9, 5)
            self.assertEqual(client.batches.created, created)

    def test_existing_batch_id_resumes_without_submission(self):
        item = blind_item("q_resume")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            batch_dir = root / "batch"
            batch_dir.mkdir(parents=True)
            config = state_config([item], "gpt-5.6-sol", "high", 16384, 3, 0.9)
            record = create_record([(item, 1)], config, batch_dir, 1)
            client = fake_client()
            with Path(record["input_path"]).open("rb") as handle:
                uploaded = client.files.create(handle, "batch")
            batch = client.batches.create(
                uploaded.id, "/v1/responses", "24h", {"pass": "deep_review"},
            )
            record.update({
                "input_file_id": uploaded.id, "batch_id": batch.id,
                "submitted_at_utc": "before interruption",
                "last_batch_snapshot": batch.model_dump(),
            })
            atomic_json(batch_dir / "state.json", {"config": config, "batches": [record]})
            created = client.batches.created
            artifacts, _ = run_batch_review(
                client, [item], root, "gpt-5.6-sol", "high", 16384, 3, 0.9, 5,
            )
            self.assertEqual(client.batches.created, created)
            self.assertEqual(artifacts[0]["status"], "complete")

    def test_statistics_accounting(self):
        rows = []
        for index, action in enumerate((
            "KEEP_CANONICAL", "REPLACEMENT_CANDIDATE", "EXCLUDE", "HUMAN_REVIEW",
        )):
            rows.append({
                "id": f"q_{index}", "round": "v1", "split": "train",
                "final_action": action, "decision_reasons": [],
                "deep_review_result": review_result(), "deep_review_attempts": [{"parsed": {}}],
            })
        stats = make_statistics(rows)
        self.assertEqual(stats["total_suspects"], 4)
        self.assertEqual(sum(stats["final_action_counts"].values()), 4)
        self.assertTrue(stats["accounting_check"])

    def test_screening_answer_conflict_blocks_replacement_candidate(self):
        parsed = review_result(
            independently_derived_answer="223844", canonical_status="INCORRECT",
            canonical_matches_request=False, derived_sol_relation="AGREE",
            canonical_sol_relation="CONFLICT", three_way_relation="CANONICAL_ONLY_DIFFERS",
            recommended_action="REPLACE_CANONICAL", replacement_answer="223844",
        )
        artifact = {
            "status": "complete", "result": parsed, "attempts": [{"parsed": parsed}],
        }
        source = {"audit_result": {"preferred_final_answer": "224069"}}
        action, reasons = deterministic_action(artifact, 0.9, source)
        self.assertEqual(action, "HUMAN_REVIEW")
        self.assertIn("SCREENING_PREFERRED_ANSWER_CONFLICTS_WITH_SOL", reasons)

    def test_writes_all_output_groups_and_report(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output, audit = root / "output", root / "audit"
            output.joinpath("batch").mkdir(parents=True)
            atomic_json(output / "batch/state.json", {"config": {}, "batches": []})
            rows = [{
                "id": "q_keep", "round": "v1", "split": "train",
                "final_action": "KEEP_CANONICAL", "decision_reasons": [],
                "deep_review_result": review_result(),
                "deep_review_attempts": [{"parsed": review_result()}],
            }]
            groups = {
                "KEEP_CANONICAL": rows, "REPLACEMENT_CANDIDATE": [],
                "EXCLUDE": [], "HUMAN_REVIEW": [],
            }
            stats = make_statistics(rows)
            write_outputs(output, audit, rows, groups, stats, {"model": "fake"})
            for name in (
                "deep_review_results.jsonl", "keep.jsonl", "replacement_candidates.jsonl",
                "exclude.jsonl", "human_review.jsonl", "manifest.json",
                "analysis/statistics.json", "analysis/report.md",
            ):
                self.assertTrue((output / name).is_file(), name)
            self.assertIn("KEEP_CANONICAL", (output / "analysis/report.md").read_text())


if __name__ == "__main__":
    unittest.main()
