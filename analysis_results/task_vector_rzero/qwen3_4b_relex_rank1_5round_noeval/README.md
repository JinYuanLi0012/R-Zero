# Qwen3-4B RELEX Rank-1 Delta Geometry Results

This directory contains the portable analysis outputs for
`qwen3_4b_relex_rank1_5round_noeval`.

Definitions:

- Questioner full delta: `Q1 - Base`, then `Qi - Q(i-1)`.
- Solver primary delta: `Ri - Base`, matching the rank-1 task vector used by composition.
- Solver full control: `Ai(global_step_15) - Base`.

Start with [`delta_geometry_v1/report.html`](delta_geometry_v1/report.html) or
[`delta_geometry_v1/report.md`](delta_geometry_v1/report.md). The underlying
CSV/Parquet metrics, Gram matrix, SVD coordinates, and PNG/PDF figures are kept
beside the report for local follow-up analysis.

The large model checkpoints and resumable per-tensor scan caches are intentionally
excluded. `delta_geometry_v1/cache/gram_matrices.npz` is retained because it is
small and sufficient for recomputing downstream geometry without model weights.

The original implementation plan is in
[`DELTA_GEOMETRY_PLAN.md`](DELTA_GEOMETRY_PLAN.md), and the generating code is in
`methods/task_vector_rzero/analysis/` at the repository root.
