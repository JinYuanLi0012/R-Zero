#!/usr/bin/env python3
"""Audit the Terra dataset and optionally export tiny parquet smoke fixtures."""

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from datasets import DatasetDict, get_dataset_config_names, load_dataset


DEFAULT_DATASET = "jinyuan222/rzero-validity-rl-terra-v1"
REQUIRED_COLUMNS = {
    "id",
    "round",
    "question",
    "terra_validity",
    "canonical_final_answer",
    "answer_verified",
    "validity_rl_target",
    "split",
}


def _validate_split(name: str, split: Any) -> Dict[str, int]:
    missing = REQUIRED_COLUMNS.difference(split.column_names)
    if missing:
        raise ValueError(f"{name} is missing columns: {sorted(missing)}")

    counts = {"VALID": 0, "INVALID": 0}
    for index, row in enumerate(split):
        validity = row["terra_validity"]
        target = row["validity_rl_target"]
        if validity not in counts:
            raise ValueError(f"{name}[{index}] has unknown terra_validity={validity!r}")
        counts[validity] += 1
        if row["split"] != name:
            raise ValueError(f"{name}[{index}] carries split={row['split']!r}")
        if validity == "INVALID":
            if target != "INVALID":
                raise ValueError(f"{name}[{index}] INVALID row has target={target!r}")
        else:
            if row["answer_verified"] is not True:
                raise ValueError(f"{name}[{index}] VALID answer is not verified")
            if not row["canonical_final_answer"]:
                raise ValueError(f"{name}[{index}] VALID row has no canonical answer")
            if target != row["canonical_final_answer"]:
                raise ValueError(f"{name}[{index}] target differs from canonical answer")
    return counts


def audit_dataset(dataset_name: str) -> tuple[DatasetDict, Dict[str, Any]]:
    configs = get_dataset_config_names(dataset_name)
    dataset = load_dataset(dataset_name, "default")
    if set(dataset) != {"train", "validation"}:
        raise ValueError(f"expected train/validation splits, got {sorted(dataset)}")

    report: Dict[str, Any] = {"dataset": dataset_name, "configs": configs, "splits": {}}
    for name, split in dataset.items():
        report["splits"][name] = {
            "rows": len(split),
            "columns": split.column_names,
            "validity_counts": _validate_split(name, split),
        }
    return dataset, report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--train-limit", type=int, default=0)
    parser.add_argument("--validation-limit", type=int, default=0)
    args = parser.parse_args()

    dataset, report = audit_dataset(args.dataset)
    print(json.dumps(report, indent=2))
    for split_name in ("train", "validation"):
        sample = dataset[split_name][0]
        print(
            f"{split_name} sample: "
            + json.dumps(
                {
                    "id": sample["id"],
                    "terra_validity": sample["terra_validity"],
                    "question": sample["question"],
                    "validity_rl_target": sample["validity_rl_target"],
                },
                ensure_ascii=False,
            )
        )

    if args.output_dir:
        if args.train_limit <= 0 or args.validation_limit <= 0:
            parser.error("--output-dir requires positive --train-limit and --validation-limit")
        args.output_dir.mkdir(parents=True, exist_ok=True)
        for split_name, limit in (
            ("train", args.train_limit),
            ("validation", args.validation_limit),
        ):
            selected = dataset[split_name].select(range(min(limit, len(dataset[split_name]))))
            destination = args.output_dir / f"{split_name}.parquet"
            selected.to_parquet(destination)
            print(f"wrote {len(selected)} rows to {destination}")


if __name__ == "__main__":
    main()
