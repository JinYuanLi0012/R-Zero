from __future__ import annotations

import json
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


METHOD_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(METHOD_DIR))


def load_local_module(name: str):
    spec = importlib.util.spec_from_file_location(f"clean_formal_{name}", METHOD_DIR / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


prepare = load_local_module("prepare").prepare
finalize = load_local_module("finalize").finalize
majority_module = load_local_module("majority_judge")
make_batch_row = majority_module.make_batch_row
run_majority_pass = majority_module.run_majority_pass


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def source_row(question: str, answer: str = "2") -> dict:
    return {
        "answer": answer, "discarded_by_validity": False, "invalid_votes": 0,
        "passed_rzero_filter": True, "question": question,
        "results": [answer] * 9, "score": 1.0, "total_votes": 9,
        "validity_decision": "VALID", "validity_format_failures": 0,
        "validity_outputs": [answer] * 9, "validity_penalty": 0.0,
    }


def sampled_row(item_id: str, round_name: str, answer: str) -> dict:
    return {
        "id": item_id, "round": round_name, "source_index": 0,
        "question": f"Question {item_id}", "majority_answer": answer,
        "solver_results": [answer] * 9, "solver_score": 1.0,
        "total_votes": 9, "source_validity_decision": "VALID",
        "source_invalid_votes": 0, "source_validity_format_failures": 0,
        "source_validity_outputs": [answer] * 9, "source_validity_penalty": 0.0,
        "source_discarded_by_validity": False, "source_passed_rzero_filter": True,
    }


def validity_artifact(item_id: str, label: str) -> dict:
    is_valid = label == "A"
    return {
        "id": item_id, "status": "complete", "result": {
            "label": label, "confidence": 0.99,
            "invalid_type": None if is_valid else "no_solution",
            "reasoning_summary": "checked",
        },
    }


def answer_artifact(item_id: str, status: str = "complete") -> dict:
    verified = status == "complete"
    return {
        "id": item_id, "status": status, "result": {
            "answer_verified": verified,
            "canonical_final_answer": "2" if verified else None,
            "confidence": 0.99 if verified else 0.5,
        },
    }


class PipelineTests(unittest.TestCase):
    def test_prepare_deduplicates_before_balanced_sampling(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = root / "data"
            data.mkdir()
            for round_number in range(1, 5):
                rows = [source_row(f"round {round_number} unique {index}") for index in range(5)]
                if round_number == 1:
                    rows[-1] = source_row(rows[0]["question"], "different answer")
                if round_number == 2:
                    rows[-1] = source_row("round 1 unique 1")
                write_jsonl(data / f"round_{round_number}_phase_b.jsonl", rows)
                (data / f"round_{round_number}.json").write_text(
                    json.dumps({"evaluated_candidate_count": len(rows)}), encoding="utf-8"
                )
            first = root / "first"
            second = root / "second"
            sampled = prepare(data, first, per_round=2, seed=42)
            prepare(data, second, per_round=2, seed=42)
            self.assertEqual(len(sampled), 8)
            self.assertEqual(len({row["question"] for row in sampled}), 8)
            self.assertEqual(
                {name: sum(row["round"] == name for row in sampled) for name in ("v1", "v2", "v3", "v4")},
                {"v1": 2, "v2": 2, "v3": 2, "v4": 2},
            )
            blind = [json.loads(line) for line in (first / "terra_blind_input.jsonl").read_text().splitlines()]
            self.assertTrue(all(set(row) == {"id", "question"} for row in blind))
            self.assertEqual(
                (first / "sampled_questions.jsonl").read_text(),
                (second / "sampled_questions.jsonl").read_text(),
            )

    def test_majority_request_exposes_only_comparison_inputs(self):
        row = make_batch_row({
            "id": "q_opaque", "question": "What is 1+1?",
            "canonical_final_answer": "2", "majority_answer": "2.0",
        }, 1, "gpt-5.6-sol", "high", 16384)
        serialized = json.dumps(row)
        self.assertEqual(row["url"], "/v1/responses")
        self.assertEqual(row["body"]["model"], "gpt-5.6-sol")
        self.assertIn("canonical_final_answer", serialized)
        self.assertIn("majority_answer", serialized)
        for private in ("round", "solver_score", "results", "invalid_votes", "passed_rzero"):
            self.assertNotIn(private, serialized)

    def test_majority_batch_retries_uncertain_result(self):
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
                file_id = f"input-{self.next_id}"
                self.next_id += 1
                self.values[file_id] = file.read()
                return FakeObject(id=file_id)

            def content(self, file_id):
                return FakeObject(content=self.values[file_id])

        class FakeBatches:
            def __init__(self, files):
                self.files = files
                self.created = 0
                self.values = {}

            def create(self, input_file_id, endpoint, completion_window, metadata):
                del endpoint, completion_window, metadata
                self.created += 1
                requests = [
                    json.loads(line)
                    for line in self.files.values[input_file_id].decode().splitlines()
                ]
                lines = []
                for request in requests:
                    first = request["custom_id"].endswith(":a1")
                    parsed = {
                        "majority_answer_status": "UNABLE_TO_VERIFY" if first else "CORRECT",
                        "mathematically_equivalent": None if first else True,
                        "confidence": 0.5 if first else 0.99,
                        "reasoning_summary": "retry" if first else "equivalent",
                    }
                    lines.append(json.dumps({
                        "custom_id": request["custom_id"],
                        "response": {"status_code": 200, "body": {
                            "output": [{"type": "message", "content": [{
                                "type": "output_text", "text": json.dumps(parsed),
                            }]}],
                        }}, "error": None,
                    }))
                output_id = f"output-{self.created}"
                self.files.values[output_id] = ("\n".join(lines) + "\n").encode()
                batch_id = f"batch-{self.created}"
                snapshot = {
                    "id": batch_id, "status": "completed", "output_file_id": output_id,
                    "error_file_id": None,
                    "request_counts": {"total": len(requests), "completed": len(requests), "failed": 0},
                    "errors": None,
                }
                self.values[batch_id] = snapshot
                return FakeObject(**snapshot)

            def retrieve(self, batch_id):
                return FakeObject(**self.values[batch_id])

        with tempfile.TemporaryDirectory() as directory:
            files = FakeFiles()
            client = SimpleNamespace(files=files, batches=FakeBatches(files))
            results = run_majority_pass(client, [{
                "id": "q_one", "question": "What is 1+1?",
                "canonical_final_answer": "2", "majority_answer": "2.0",
            }], Path(directory), "gpt-5.6-sol", "high", 16384, 3, 0.8, 5)
            self.assertEqual(results[0]["status"], "complete")
            self.assertEqual(results[0]["result"]["majority_answer_status"], "CORRECT")
            self.assertEqual(len(results[0]["attempts"]), 2)
            self.assertEqual(client.batches.created, 2)

    def test_finalize_defines_strict_and_judged_accuracy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sampled = [
                sampled_row("q1", "v1", "2"),
                sampled_row("q2", "v2", "None"),
                sampled_row("q3", "v3", ""),
                sampled_row("q4", "v4", "7"),
            ]
            raw = [
                {"id": "q1", "validity_pass": validity_artifact("q1", "A"),
                 "answer_pass": answer_artifact("q1"), "majority_pass": {
                     "id": "q1", "status": "complete", "result": {
                         "majority_answer_status": "CORRECT",
                         "mathematically_equivalent": True, "confidence": 0.99,
                         "reasoning_summary": "same answer",
                     }}},
                {"id": "q2", "validity_pass": validity_artifact("q2", "A"),
                 "answer_pass": answer_artifact("q2"), "majority_pass": None},
                {"id": "q3", "validity_pass": validity_artifact("q3", "D"),
                 "answer_pass": None, "majority_pass": None},
                {"id": "q4", "validity_pass": validity_artifact("q4", "A"),
                 "answer_pass": answer_artifact("q4", "uncertain"), "majority_pass": None},
            ]
            write_jsonl(root / "sampled_questions.jsonl", sampled)
            write_jsonl(root / "terra_raw_results.jsonl", raw)
            (root / "prepare_manifest.json").write_text("{}", encoding="utf-8")
            (root / "annotation_manifest.json").write_text("{}", encoding="utf-8")
            stats = finalize(root)
            self.assertEqual(stats["overall"]["terra_valid"], 3)
            self.assertEqual(stats["overall"]["terra_invalid"], 1)
            self.assertEqual(stats["overall"]["verified_reference_count"], 2)
            self.assertEqual(stats["overall"]["majority_correct_count"], 1)
            self.assertEqual(stats["overall"]["majority_strict_accuracy"], 0.5)
            self.assertEqual(stats["overall"]["majority_judged_accuracy"], 1.0)
            self.assertEqual(stats["failed_or_uncertain_count"], 2)


if __name__ == "__main__":
    unittest.main()
