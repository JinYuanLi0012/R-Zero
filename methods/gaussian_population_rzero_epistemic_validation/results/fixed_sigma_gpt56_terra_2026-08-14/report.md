# R-Zero V1–V3 Epistemic Offline Validation

## Scope and fixed-scale design

This exploratory pilot covers 600 stratified questions from the old-reward-retained V1–V3 Solver datasets. The deleted 8k candidate pools are not represented. All five perturbation scales were fixed before analysis and are reported equally; no sigma is selected as a primary or best result. Sigma zero is the sampling-randomness control.

The core question is whether epistemic disagreement stably separates reasonable capability boundaries from question-induced confusion across scales, and at what scale this ability disappears as perturbations become destructive.

## Cross-sigma results

|   sigma |   extraction_failure_rate |   high_consensus_historical_agreement |   mean_u_epi |   u_epi_valid_roc_auc |   v23_matched_pairs |   v23_matched_difference_pp |   v23_ci95_low_pp |   v23_ci95_high_pp |
|--------:|--------------------------:|--------------------------------------:|-------------:|----------------------:|--------------------:|----------------------------:|------------------:|-------------------:|
|  0      |                0.00671875 |                              0.686228 |     0.51889  |              0.469936 |                  11 |                    -27.2727 |          -54.5455 |             0      |
|  0.0001 |                0.00596354 |                              0.675509 |     0.518927 |              0.484746 |                  11 |                     18.1818 |          -18.1818 |            54.5455 |
|  0.0003 |                0.00588542 |                              0.681504 |     0.520077 |              0.473103 |                   4 |                      0      |          -75      |            75      |
|  0.001  |                0.00789063 |                              0.631541 |     0.575536 |              0.481741 |                   5 |                      0      |          -60      |            60      |
|  0.003  |                0.0444531  |                              0.281613 |     0.851731 |              0.478427 |                   3 |                    -33.3333 |         -100      |             0      |

For every sigma, `analysis_summary.json` contains V2+V3 and per-round paired H1 results, exact McNemar tests, Valid-label relationships, and Precision@10/20/30. The trajectory plots show historical-answer retention on high-consensus questions, extraction failure, mean U_epi, matched validity separation, and Precision@20.

The interpretation should emphasize stability across adjacent nonzero scales and jointly inspect rising U_epi, answer retention, and extraction failure. An isolated best-looking scale is not treated as confirmatory evidence.
