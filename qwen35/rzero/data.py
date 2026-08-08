"""Build verl-compatible Parquet inputs without changing upstream verl."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from qwen35.rzero.prompts import QUESTIONER_MESSAGES, solver_messages


def questioner_record(index: int, answer: str = "") -> dict[str, Any]:
    return {
        "data_source": "rzero_questioner",
        "prompt": QUESTIONER_MESSAGES,
        "ability": "math",
        "reward_model": {"style": "rule", "ground_truth": answer},
        "extra_info": {"index": index},
    }


def solver_record(problem: str, answer: str, score: float, index: int) -> dict[str, Any]:
    return {
        "data_source": "rzero_solver",
        "prompt": solver_messages(problem),
        "ability": "math",
        "reward_model": {"style": "rule", "ground_truth": answer},
        "extra_info": {"index": index, "vote_score": score},
    }


def prepare_seed_data(dataset_id: str, train_split: str, val_split: str, output_dir: Path) -> None:
    from datasets import Dataset, load_dataset

    output_dir.mkdir(parents=True, exist_ok=True)
    train = load_dataset(dataset_id, split=train_split)
    val = load_dataset(dataset_id, split=val_split)
    train_answers = train["answer"] if "answer" in train.column_names else [""] * len(train)
    val_problems = val["problem"] if "problem" in val.column_names else val["question"]
    val_answers = val["answer"]

    Dataset.from_list([questioner_record(i, str(answer)) for i, answer in enumerate(train_answers)]).to_parquet(
        output_dir / "questioner_train.parquet"
    )
    Dataset.from_list([questioner_record(i, str(answer)) for i, answer in enumerate(val_answers)]).to_parquet(
        output_dir / "questioner_val.parquet"
    )
    Dataset.from_list(
        [solver_record(str(problem), str(answer), 0.0, i) for i, (problem, answer) in enumerate(zip(val_problems, val_answers))]
    ).to_parquet(output_dir / "solver_val.parquet")

    metadata = {
        "dataset_id": dataset_id,
        "train_split": train_split,
        "val_split": val_split,
        "questioner_train_rows": len(train),
        "questioner_val_rows": len(val),
        "solver_val_rows": len(val),
    }
    (output_dir / "seed_data.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--train-split", default="train")
    parser.add_argument("--val-split", default="test")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    prepare_seed_data(args.dataset_id, args.train_split, args.val_split, args.output_dir)


if __name__ == "__main__":
    main()
