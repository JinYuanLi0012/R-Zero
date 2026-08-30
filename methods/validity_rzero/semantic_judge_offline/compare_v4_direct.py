#!/usr/bin/env python3
"""Compare v4 direct-label metrics/runtime with the v3-max1024 baseline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from run_pair_judge import atomic_json
from run_pair_judge_v2 import ORDERS


def delta(
    direct: float | int | None, baseline: float | int | None,
) -> dict[str, float | int | None]:
    if direct is None or baseline is None:
        return {
            "baseline": baseline, "direct": direct,
            "delta_direct_minus_baseline": None, "ratio_direct_over_baseline": None,
        }
    return {
        "baseline": baseline,
        "direct": direct,
        "delta_direct_minus_baseline": direct - baseline,
        "ratio_direct_over_baseline": direct / baseline if baseline else None,
    }


def compare(
    baseline_metrics: dict[str, Any], direct_metrics: dict[str, Any],
    baseline_manifest: dict[str, Any], direct_manifest: dict[str, Any],
) -> dict[str, Any]:
    orders = {}
    for order in ORDERS:
        baseline = baseline_metrics["conditions"][order]
        direct = direct_metrics["conditions"][order]
        orders[order] = {
            "accuracy_end_to_end": delta(
                direct["accuracy_end_to_end"], baseline["accuracy_end_to_end"]
            ),
            "accuracy_parseable_only": delta(
                direct["accuracy_parseable_only"], baseline["accuracy_parseable_only"]
            ),
            "format_errors": delta(direct["format_errors"], baseline["format_errors"]),
            "format_error_rate": delta(
                direct["format_error_rate"], baseline["format_error_rate"]
            ),
        }
    baseline_runtime = baseline_manifest["runtime"]
    direct_runtime = direct_manifest["runtime"]
    return {
        "evaluation_status": "controlled_diagnostic_ablation_not_held_out",
        "delta_definition": "direct minus brief-analysis baseline",
        "orders": orders,
        "runtime": {
            "mean_generated_tokens": delta(
                direct_runtime["tokens"]["generated"]["mean"],
                baseline_runtime["tokens"]["generated"]["mean"],
            ),
            "output_tokens_per_second": delta(
                direct_runtime["throughput"]["output_tokens_per_second"],
                baseline_runtime["throughput"]["output_tokens_per_second"],
            ),
            "conditions_per_second": delta(
                direct_runtime["throughput"]["conditions_per_second"],
                baseline_runtime["throughput"]["conditions_per_second"],
            ),
            "generation_wall_seconds": delta(
                direct_runtime["timing_seconds"]["generation_wall"],
                baseline_runtime["timing_seconds"]["generation_wall"],
            ),
            "total_wall_seconds": delta(
                direct_runtime["timing_seconds"]["total_wall"],
                baseline_runtime["timing_seconds"]["total_wall"],
            ),
        },
        "order_stability": {
            "baseline": baseline_metrics["order_stability"],
            "direct": direct_metrics["order_stability"],
        },
    }


def markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Direct-label vs brief-analysis diagnostic ablation", "",
        "Same 50 pairs; this is not a held-out validation.", "",
        "## Accuracy and formatting", "",
        "| Order | Baseline accuracy | Direct accuracy | Accuracy delta | Baseline format errors | Direct format errors | Format delta |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for order in ORDERS:
        row = result["orders"][order]
        accuracy = row["accuracy_end_to_end"]
        formatting = row["format_errors"]
        lines.append(
            f"| `{order}` | {accuracy['baseline']:.1%} | {accuracy['direct']:.1%} | "
            f"{accuracy['delta_direct_minus_baseline']:+.1%} | {formatting['baseline']} | "
            f"{formatting['direct']} | {formatting['delta_direct_minus_baseline']:+} |"
        )
    lines.extend(["", "## Runtime deltas (direct minus baseline)", ""])
    for name, value in result["runtime"].items():
        lines.append(
            f"- `{name}`: baseline={value['baseline']}, direct={value['direct']}, "
            f"delta={value['delta_direct_minus_baseline']}"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-metrics", type=Path, required=True)
    parser.add_argument("--baseline-manifest", type=Path, required=True)
    parser.add_argument("--direct-metrics", type=Path, required=True)
    parser.add_argument("--direct-manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    load = lambda path: json.loads(path.read_text(encoding="utf-8"))
    result = compare(
        load(args.baseline_metrics), load(args.direct_metrics),
        load(args.baseline_manifest), load(args.direct_manifest),
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    atomic_json(args.output_dir / "comparison_v4_direct_vs_v3.json", result)
    (args.output_dir / "comparison_v4_direct_vs_v3.md").write_text(
        markdown(result), encoding="utf-8"
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
