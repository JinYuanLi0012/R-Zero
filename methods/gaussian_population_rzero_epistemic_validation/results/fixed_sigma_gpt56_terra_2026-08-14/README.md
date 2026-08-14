# Fixed-Sigma V1–V3 Epistemic Validation Results

This directory contains the completed offline validation artifacts for ordinary
R-Zero V1–V3, judged with `gpt-5.6-terra`.

## Experiment identity

- Questions: 600 (200 per round)
- Fixed sigmas: `0`, `1e-4`, `3e-4`, `1e-3`, `3e-3`
- Population: `M=8` experts
- Samples per expert: `K=8`
- Completions per sigma: 38,400
- Total completions: 192,000
- Judge coverage: 600/600 questions

## Headline findings

The GPT-5.6 Terra reference-validity rate falls substantially across rounds:

| Round | Valid (A) |
|---|---:|
| V1 | 83.0% |
| V2 | 74.0% |
| V3 | 55.5% |

This supports the mechanism-level observation that question quality deteriorates
from V1 to V3. However, the preregistered epistemic-disagreement hypotheses are
not supported:

- `U_epi` Valid ROC-AUC is below 0.5 at every sigma (approximately 0.470–0.485).
- V2+V3 matched estimates are unstable, with only 3–11 matched pairs per sigma.
- In the non-destructive perturbation range, `U_epi` Precision@20 is below both
  historical difficulty and the simpler `-H_within` baseline.
- At `sigma=0.003`, apparent Top-K gains coincide with strong model damage:
  historical-answer retention falls to about 28.2% and extraction failure rises
  to about 4.45%.

The most important measurement diagnostic is that mean `U_epi` is already about
0.519 at `sigma=0`, although all experts have identical weights. With only eight
samples per expert, the plug-in mutual-information estimate is therefore strongly
inflated by finite-sampling variation. The registered result should remain
negative. Permutation-null bias correction and paired delta analysis are possible
follow-up exploratory analyses that do not require rerunning the GPU generations.

## Artifacts

- [`report.md`](report.md): generated experiment report.
- [`analysis_summary.json`](analysis_summary.json): complete structured results.
- [`cross_sigma_summary.csv`](cross_sigma_summary.csv): headline metrics by sigma.
- [`question_level_scores_all_sigmas.csv`](question_level_scores_all_sigmas.csv):
  question-level metrics and Judge labels.
- [`precision_at_k_all_sigmas.csv`](precision_at_k_all_sigmas.csv): all fixed-budget
  ablations.
- [`matched_pairs_all_sigmas.csv`](matched_pairs_all_sigmas.csv): retained matched
  pairs and outcomes.
- [`round_diagnostics_all_sigmas.csv`](round_diagnostics_all_sigmas.csv): round-level
  label and entropy diagnostics.
- [`cross_sigma_trajectories.png`](cross_sigma_trajectories.png): scale trajectories.
- [`precision_at_20_across_sigmas.png`](precision_at_20_across_sigmas.png):
  Precision@20 comparison.

## Scope limitation

The source questions are the old-reward-retained Solver training datasets. The
deleted full 8k candidate pools are not represented, so these results test
secondary discrimination inside retained data rather than full candidate-pool
selection by a replacement Questioner reward.
