# Binary few-shot logprob Judge

Terra first-pass label A is the Valid reference; B-F are Invalid. Terra is a reference judgment, not absolute ground truth.

## Overall

| Method | Accuracy | Balanced accuracy | Valid P/R/F1 | Invalid recall | MCC | Kappa | AUC |
|---|---:|---:|---:|---:|---:|---:|---:|
| Direct few-shot | 0.640 | 0.479 | 0.698/0.866/0.773 | 0.091 | -0.059 | -0.052 | 0.448 |
| Solver-first few-shot | 0.635 | 0.557 | 0.742/0.744/0.743 | 0.371 | 0.115 | 0.115 | 0.635 |
| Always valid | 0.708 | 0.500 | 0.708/1.000/0.829 | 0.000 | 0.000 | 0.000 | 0.500 |

## Valid-rate trend

| Round | Direct | Solver-first | Terra reference |
|---:|---:|---:|---:|
| V1 | 94.0% | 84.5% | 83.0% |
| V2 | 75.5% | 61.0% | 74.0% |
| V3 | 94.0% | 67.5% | 55.5% |

Paired questions: 600; same verdict: 475; direct-only correct: 64; solver-first-only correct: 61.

Generation diagnostics: direct truncated=43, empty=0, mean_tokens=198.1; solver_first truncated=92, empty=0, mean_tokens=582.9.

`valid_score` is a logprob-derived ranking score: the two-candidate softmax of model-computed sequence log-likelihoods for ` VALID` and ` INVALID`. It is not self-reported confidence or a calibrated probability.
