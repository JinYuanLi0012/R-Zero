#!/usr/bin/env python3
"""Build auditable Markdown and HTML reports from completed analysis artifacts."""

from __future__ import annotations

import argparse
import csv
import html
import json
from pathlib import Path
from typing import Any


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = [
        "| " + " | ".join(str(row.get(column, "")) for column in columns) + " |"
        for row in rows
    ]
    return "\n".join([header, separator, *body])


def rounded(value: str, digits: int = 5) -> str:
    try:
        return f"{float(value):.{digits}g}"
    except (TypeError, ValueError):
        return value


def figure_block(filename: str, caption: str) -> str:
    return f"![{caption}](figures/{filename}.png)\n\n*{caption}*"


def build_markdown(root: Path) -> str:
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    norms = read_rows(root / "metrics/global_norms.csv")
    relex = read_rows(root / "metrics/relex_retention.csv")
    directions = read_rows(root / "metrics/direction_metrics.csv")
    composition_path = root / "metrics/composition_consistency.csv"
    composition = read_rows(composition_path) if composition_path.is_file() else []

    norm_rows = [
        {
            "family": row["family"],
            "round": row["round"],
            "L2": rounded(row["l2_norm"]),
            "RMS": rounded(row["rms"]),
            "relative": rounded(row["relative_l2"]),
        }
        for row in norms
    ]
    relex_rows = [
        {
            "round": row["round"],
            "rank/full norm": rounded(row["norm_ratio"]),
            "cosine": rounded(row["cosine"]),
            "angle": rounded(row["angle_degrees"], 4),
            "relative error": rounded(row["relative_reconstruction_error"]),
        }
        for row in relex
    ]
    historical = [
        {
            "family": row["family"],
            "round": row["round"],
            "history cosine": rounded(row["history_cosine"]),
            "angle": rounded(row["history_angle_degrees"], 4),
            "orthogonal ratio": rounded(row["orthogonal_ratio"]),
        }
        for row in directions
        if row.get("metric") == "historical" and int(row["round"]) > 1
    ]
    composition_rows = [
        {
            "round": row["round"],
            "actual/intended cosine": rounded(row["actual_intended_cosine"]),
            "relative residual": rounded(row["relative_residual"]),
        }
        for row in composition
    ]

    sections = [
        "# Task-Vector R-Zero Delta Geometry Report",
        "",
        "## Scope and definitions",
        "",
        "This report uses the run-faithful definitions:",
        "",
        "- Questioner: `Q1 - Base`, then `Qi - Q(i-1)`.",
        "- Solver primary: `RELEX_Ri - Base`.",
        "- Solver control: `BaseFit_Ai_step15 - Base`.",
        "",
        f"Input fingerprint: `{manifest['input_fingerprint']}`",
        "",
        f"Floating parameter count: `{manifest['floating_parameter_count']}`",
        "",
        f"Compute device: `{manifest['device']}`",
        "",
        "Q1 is a bootstrap Questioner. Since its pre-training checkpoint is unavailable locally, Base is used as its baseline.",
        "",
        "## A. Questioner: actual full-delta evolution",
        "",
        figure_block("global_delta_norms", "Global and relative delta magnitudes."),
        "",
        figure_block("questioner_full_cosine", "Pairwise Questioner full-delta cosine similarity."),
        "",
        figure_block("layer_norm_heatmap_questioner_full", "Questioner relative update by transformer layer."),
        "",
        "## B. Solver: actual rank1-delta evolution",
        "",
        figure_block("solver_rank1_cosine", "Pairwise Solver rank1-delta cosine similarity."),
        "",
        figure_block("direction_progression", "Adjacent-round turns and alignment with accumulated history."),
        "",
        figure_block("historical_alignment", "Fraction of each update orthogonal to accumulated history."),
        "",
        figure_block("layer_norm_heatmap_solver_rank1", "Solver rank1 relative update by transformer layer."),
        "",
        "## C. RELEX: full delta to rank1 delta",
        "",
        figure_block("relex_retention", "RELEX magnitude, direction, and reconstruction retention."),
        "",
        figure_block("rank1_vs_full_plane", "Paired full and rank1 directions in a shared exact SVD plane."),
        "",
        figure_block("solver_full_cosine", "Pairwise Solver full-delta cosine similarity."),
        "",
        "### RELEX summary",
        "",
        markdown_table(relex_rows, ["round", "rank/full norm", "cosine", "angle", "relative error"]),
        "",
        "### Composed Solver consistency",
        "",
        markdown_table(
            composition_rows,
            ["round", "actual/intended cosine", "relative residual"],
        )
        if composition_rows
        else "Composition validation was skipped.",
        "",
        "## D. Cross-family geometry",
        "",
        figure_block("questioner_solver_cross_cosine", "Questioner full and Solver rank1 joint cosine matrix."),
        "",
        figure_block("direction_plane", "Joint unit-delta direction plane."),
        "",
        figure_block("cumulative_trajectory", "Cumulative Questioner and Rank1 Solver trajectories."),
        "",
        "### Alignment with accumulated history",
        "",
        markdown_table(
            historical,
            ["family", "round", "history cosine", "angle", "orthogonal ratio"],
        ),
        "",
        "## E. Evaluation and geometry",
        "",
        figure_block("evaluation_geometry", "Rank1 V1--V5 benchmark scores and changes from Base."),
        "",
        "The evaluation contains only five iterations. Any association with parameter geometry is descriptive, not causal or statistically conclusive.",
        "",
        "## Global norm table",
        "",
        markdown_table(norm_rows, ["family", "round", "L2", "RMS", "relative"]),
        "",
        "## F. Numerical interpretation boundaries",
        "",
        "- RELEX is a per-tensor rank-1 trajectory reconstruction, not one global rank-1 SVD over the model.",
        "- Two-dimensional SVD figures retain only the energy reported in `manifest.json`; cosine matrices remain the primary direction evidence.",
        "- Global metrics weight every parameter element equally. Per-layer tables provide a complementary layer-balanced view.",
        "- Full Solver deltas are controls. Rank1 Solver deltas are the vectors aligned with the evaluated Rank1 V1--V5 models.",
        "",
    ]
    return "\n".join(sections)


def markdown_to_html(markdown: str) -> str:
    """Minimal dependency-free renderer for the report's controlled Markdown subset."""

    lines = markdown.splitlines()
    rendered: list[str] = []
    in_list = False
    in_table = False
    for index, line in enumerate(lines):
        if line.startswith("| "):
            cells = [html.escape(cell.strip()) for cell in line.strip("|").split("|")]
            if all(set(cell) <= {"-", ":"} for cell in cells):
                continue
            if not in_table:
                rendered.append("<table>")
                in_table = True
                rendered.append("<tr>" + "".join(f"<th>{cell}</th>" for cell in cells) + "</tr>")
            else:
                rendered.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in cells) + "</tr>")
            continue
        if in_table:
            rendered.append("</table>")
            in_table = False
        if line.startswith("- "):
            if not in_list:
                rendered.append("<ul>")
                in_list = True
            rendered.append(f"<li>{html.escape(line[2:])}</li>")
            continue
        if in_list:
            rendered.append("</ul>")
            in_list = False
        if line.startswith("### "):
            rendered.append(f"<h3>{html.escape(line[4:])}</h3>")
        elif line.startswith("## "):
            rendered.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.startswith("# "):
            rendered.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("![") and "](" in line:
            alt, target = line[2:].split("](", 1)
            rendered.append(f'<img src="{html.escape(target[:-1])}" alt="{html.escape(alt)}">')
        elif line.startswith("*") and line.endswith("*"):
            rendered.append(f"<p><em>{html.escape(line.strip('*'))}</em></p>")
        elif not line:
            rendered.append("")
        else:
            rendered.append(f"<p>{html.escape(line)}</p>")
    if in_list:
        rendered.append("</ul>")
    if in_table:
        rendered.append("</table>")
    body = "\n".join(rendered)
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Delta Geometry Report</title>
<style>
body {{ max-width: 1180px; margin: 40px auto; padding: 0 24px; font-family: Arial, sans-serif; line-height: 1.5; color: #1a202c; }}
img {{ max-width: 100%; border: 1px solid #e2e8f0; }}
table {{ border-collapse: collapse; width: 100%; margin: 18px 0; font-size: 14px; }}
th, td {{ border: 1px solid #cbd5e0; padding: 6px 9px; text-align: right; }}
th:first-child, td:first-child {{ text-align: left; }}
h1, h2, h3 {{ color: #2d3748; }}
code {{ background: #edf2f7; padding: 2px 4px; }}
</style></head><body>{body}</body></html>"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis-root", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = args.analysis_root.expanduser().resolve()
    markdown = build_markdown(root)
    (root / "report.md").write_text(markdown + "\n", encoding="utf-8")
    (root / "report.html").write_text(markdown_to_html(markdown), encoding="utf-8")
    print(f"Reports written to {root}")


if __name__ == "__main__":
    main()
