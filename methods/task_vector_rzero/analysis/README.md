# Task-Vector R-Zero Delta Geometry

This package implements the run-faithful analysis specified in
`analysis/DELTA_GEOMETRY_PLAN.md` under the target run.

## Definitions

- Questioner full delta: `Q1 - Base`, then `Qi - Q(i-1)`.
- Solver rank1 delta: `rank1_fit_i - Base` (primary Solver analysis).
- Solver full delta: `base_fit_i_step15 - Base` (RELEX control).

The code never writes full delta checkpoints. It streams safetensors chunks and
accumulates exact full-parameter Gram matrices, norms, layer metrics, and module
metrics.

## Environment

Run in the same Python environment as the R-Zero training code. Required for
the scan:

```text
torch
numpy
safetensors
huggingface_hub (through the existing composer import)
```

Required only for plotting:

```text
matplotlib
```

The analysis source directory and the R-Zero repository root must both be on
`PYTHONPATH` until this package is installed into the R-Zero repository.

## 1. Input-only discovery

Path discovery is performed automatically from:

```text
state/run_state.json
state/base_manifest.json
```

No `global_step_1006` Questioner checkpoint is selected. Q2--Q5 always use the
pipeline-selected `global_step_5/actor/huggingface` checkpoint.

## 2. Dry-run

The dry-run processes only a limited number of real tensors and writes a
partial resumable cache. Use a separate output directory from the production
scan:

```bash
python -m methods.task_vector_rzero.analysis.analyze_delta_geometry \
  --run-root "$RUN_ROOT" \
  --output "$RUN_ROOT/analysis/delta_geometry_v1_dryrun" \
  --device cuda \
  --chunk-elements 1000000 \
  --max-tensors 2
```

## 3. Full scan

```bash
python -m methods.task_vector_rzero.analysis.analyze_delta_geometry \
  --run-root "$RUN_ROOT" \
  --output "$RUN_ROOT/analysis/delta_geometry_v1" \
  --device cuda \
  --chunk-elements 1000000 \
  --resume
```

CUDA matmul TF32 is disabled. Delta subtraction and chunk Gram multiplication
use float32; cross-chunk accumulation uses float64 on CPU.

The cache is bound to an input fingerprint containing delta definitions,
resolved model paths, file sizes, mtimes, and Base identity. An incompatible
cache is rejected.

After the main 15-delta scan, a second resumable pass verifies every saved
`composed_solvers/v{i}` checkpoint against
`Base + sum_{j<=i}(rank1_fit_j - Base)`. This produces
`metrics/composition_consistency.csv`. It can be omitted only for an explicitly
limited diagnostic run with `--skip-composed-validation`.

## 4. Plots

```bash
python -m methods.task_vector_rzero.analysis.plot_delta_geometry \
  --analysis-root "$RUN_ROOT/analysis/delta_geometry_v1" \
  --evaluation-csv methods/task_vector_rzero/analysis/evaluation_scores.csv
```

Every figure is saved in PNG and PDF. Coordinates and matrices are saved
separately as CSV/NPZ, so the plots are auditable and can be redrawn without
reading model weights.

## 5. Report

```bash
python -m methods.task_vector_rzero.analysis.build_report \
  --analysis-root "$RUN_ROOT/analysis/delta_geometry_v1"
```

This creates `report.md` and a dependency-free `report.html`.

## Output contract

The scan creates:

```text
delta_geometry_v1/
├── manifest.json
├── cache/
├── metrics/
├── matrices/
└── embeddings/
```

Plotting adds `figures/`; report generation adds `report.md` and `report.html`.

Do not treat the five-round parameter/performance association as causal or as
a statistically powered correlation study.
