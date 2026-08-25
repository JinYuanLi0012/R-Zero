#!/usr/bin/env python3
"""Deterministically sample unique questions from clean-formal Phase-B audits."""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


METHOD_DIR = Path(__file__).resolve().parent
TERRA_DIR = METHOD_DIR.parent / "validity_rl_terra_dataset"
sys.path.insert(0, str(TERRA_DIR))

from common import atomic_json, normalize_question, question_hash, stable_int, write_jsonl


ROUNDS = (1, 2, 3, 4)
REQUIRED_FIELDS = {
    "answer", "discarded_by_validity", "invalid_votes", "passed_rzero_filter",
    "question", "results", "score", "total_votes", "validity_decision",
    "validity_format_failures", "validity_outputs", "validity_penalty",
}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            missing = REQUIRED_FIELDS.difference(row)
            if missing:
                raise ValueError(f"{path}:{line_number} missing fields: {sorted(missing)}")
            if not isinstance(row["question"], str):
                raise ValueError(f"{path}:{line_number} question is not a string")
            if not isinstance(row["answer"], str):
                raise ValueError(f"{path}:{line_number} answer is not a string")
            if row["validity_decision"] not in {"VALID", "INVALID"}:
                raise ValueError(f"{path}:{line_number} has invalid validity_decision")
            if not isinstance(row["results"], list) or row["total_votes"] != 9:
                raise ValueError(f"{path}:{line_number} has malformed vote data")
            rows.append(row)
    return rows


def load_round(data_dir: Path, round_number: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    audit_path = data_dir / f"round_{round_number}_phase_b.jsonl"
    receipt_path = data_dir / f"round_{round_number}.json"
    if not audit_path.is_file() or not receipt_path.is_file():
        raise FileNotFoundError(f"missing round {round_number} files under {data_dir}")
    rows = read_jsonl(audit_path)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("evaluated_candidate_count") != len(rows):
        raise ValueError(
            f"round {round_number} receipt says {receipt.get('evaluated_candidate_count')} rows, "
            f"but {audit_path} contains {len(rows)}"
        )
    return rows, {
        "audit_path": str(audit_path.resolve()),
        "audit_sha256": file_sha256(audit_path),
        "receipt_path": str(receipt_path.resolve()),
        "receipt_sha256": file_sha256(receipt_path),
        "receipt": receipt,
    }


def prepare(data_dir: Path, output_dir: Path, per_round: int, seed: int) -> list[dict[str, Any]]:
    if per_round < 1:
        raise ValueError("per-round must be positive")
    output_dir.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    global_occurrences: Counter[str] = Counter()
    global_answers: dict[str, set[str]] = defaultdict(set)
    selected: list[dict[str, Any]] = []
    sources: dict[str, Any] = {}
    stats: dict[str, Any] = {
        "raw_rows_by_round": {}, "owned_unique_questions_by_round": {},
        "duplicate_occurrences_removed_by_round": {},
        "duplicate_answer_conflict_groups_by_round": {},
        "empty_question_rows_by_round": {},
    }

    for round_number in ROUNDS:
        rows, source = load_round(data_dir, round_number)
        round_name = f"v{round_number}"
        sources[round_name] = source
        groups: dict[str, list[tuple[int, dict[str, Any]]]] = defaultdict(list)
        for source_index, row in enumerate(rows):
            normalized = normalize_question(row["question"])
            groups[normalized].append((source_index, row))
            global_occurrences[normalized] += 1
            global_answers[normalized].add(row["answer"].strip())
        conflict_groups = sum(
            len({entry[1]["answer"].strip() for entry in entries}) > 1
            for entries in groups.values() if len(entries) > 1
        )

        owned: list[tuple[int, dict[str, Any]]] = []
        removed = 0
        for normalized, entries in groups.items():
            if normalized in seen:
                removed += len(entries)
                continue
            seen.add(normalized)
            owned.append(entries[0])
            removed += len(entries) - 1
        if len(owned) < per_round:
            raise ValueError(
                f"round {round_number} has only {len(owned)} globally unique questions; "
                f"cannot sample {per_round}"
            )
        rng = random.Random(stable_int(seed, round_name, "clean-formal-question-audit"))
        sampled = rng.sample(owned, per_round)
        for source_index, row in sampled:
            item_id = f"q_{question_hash(row['question'])[:16]}"
            selected.append({
                "id": item_id,
                "round": round_name,
                "source_index": source_index,
                "question": row["question"],
                "majority_answer": row["answer"],
                "solver_results": row["results"],
                "solver_score": row["score"],
                "total_votes": row["total_votes"],
                "source_validity_decision": row["validity_decision"],
                "source_invalid_votes": row["invalid_votes"],
                "source_validity_format_failures": row["validity_format_failures"],
                "source_validity_outputs": row["validity_outputs"],
                "source_validity_penalty": row["validity_penalty"],
                "source_discarded_by_validity": row["discarded_by_validity"],
                "source_passed_rzero_filter": row["passed_rzero_filter"],
            })
        stats["raw_rows_by_round"][round_name] = len(rows)
        stats["owned_unique_questions_by_round"][round_name] = len(owned)
        stats["duplicate_occurrences_removed_by_round"][round_name] = removed
        stats["duplicate_answer_conflict_groups_by_round"][round_name] = conflict_groups
        stats["empty_question_rows_by_round"][round_name] = sum(
            not row["question"].strip() for row in rows
        )

    ids = [row["id"] for row in selected]
    if len(set(ids)) != len(ids):
        raise RuntimeError("opaque ID collision")
    selected.sort(key=lambda row: (int(row["round"][1:]), row["id"]))
    write_jsonl(output_dir / "sampled_questions.jsonl", selected)
    write_jsonl(
        output_dir / "terra_blind_input.jsonl",
        ({"id": row["id"], "question": row["question"]} for row in selected),
    )
    stats["sampled_by_round"] = dict(Counter(row["round"] for row in selected))
    stats["global_unique_questions"] = len(seen)
    stats["global_duplicate_question_groups"] = sum(
        count > 1 for count in global_occurrences.values()
    )
    stats["global_duplicate_answer_conflict_groups"] = sum(
        len(answers) > 1 for answers in global_answers.values()
    )
    stats["total_duplicate_occurrences_removed"] = sum(
        stats["duplicate_occurrences_removed_by_round"].values()
    )
    atomic_json(output_dir / "prepare_manifest.json", {
        "data_dir": str(data_dir.resolve()), "sampling_seed": seed,
        "per_round": per_round, "sampled_count": len(selected),
        "deduplication": "normalized question text; earliest round and first row own duplicates",
        "sources": sources, "statistics": stats,
    })
    print(
        f"[prepare] complete: sampled={len(selected)} per_round={per_round} "
        f"duplicates_removed={stats['total_duplicate_occurrences_removed']}",
        flush=True,
    )
    return selected


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--per-round", type=int, default=300)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    prepare(args.data_dir.resolve(), args.output_dir.resolve(), args.per_round, args.seed)


if __name__ == "__main__":
    main()
