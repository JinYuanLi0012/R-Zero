# Binary few-shot logprob Judge

Terra first-pass label A is the Valid reference; B-F are Invalid. Terra is a reference judgment, not absolute ground truth.

## Overall

| Method | Accuracy | Balanced accuracy | Valid P/R/F1 | Invalid recall | MCC | Kappa | AUC |
|---|---:|---:|---:|---:|---:|---:|---:|
| Direct few-shot | 0.662 | 0.491 | 0.704/0.901/0.791 | 0.080 | -0.029 | -0.024 | 0.441 |
| Solver-first few-shot | 0.640 | 0.559 | 0.742/0.753/0.748 | 0.366 | 0.120 | 0.120 | 0.647 |
| Always valid | 0.708 | 0.500 | 0.708/1.000/0.829 | 0.000 | 0.000 | 0.000 | 0.500 |

## Valid-rate trend

| Round | Direct | Solver-first | Terra reference |
|---:|---:|---:|---:|
| V1 | 97.0% | 85.5% | 83.0% |
| V2 | 80.0% | 63.0% | 74.0% |
| V3 | 95.0% | 67.0% | 55.5% |

Paired questions: 600; same verdict: 465; direct-only correct: 74; solver-first-only correct: 61.

Generation diagnostics: direct truncated=20, empty=0, mean_tokens=237.2; solver_first truncated=41, empty=0, mean_tokens=673.8.

`valid_score` is a logprob-derived ranking score: the two-candidate softmax of model-computed sequence log-likelihoods for ` VALID` and ` INVALID`. It is not self-reported confidence or a calibrated probability.
