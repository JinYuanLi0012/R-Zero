# Frozen Qwen3-4B-Base Judge comparison

Terra is used only as a reference judgment, not as absolute ground truth.

Parsed coverage: **557/600**; final parse failures: **43**.

## Overall binary comparison

| Judge | Accuracy | Balanced accuracy | Valid P/R/F1 | Invalid recall | MCC | Kappa | AUC |
|---|---:|---:|---:|---:|---:|---:|---:|
| Qwen3-4B-Base | 0.713 | 0.492 | 0.724/0.978/0.832 | 0.007 | -0.052 | -0.022 | 0.559 |
| Always valid | 0.708 | 0.500 | 0.708/1.000/0.829 | 0.000 | 0.000 | 0.000 | 0.500 |

## Valid-rate trend

| Round | Qwen | Terra reference |
|---:|---:|---:|
| V1 | 100.0% | 83.0% |
| V2 | 98.9% | 74.0% |
| V3 | 95.6% | 55.5% |

The always-valid baseline is mandatory because the reference class distribution is imbalanced. 
Interpret balanced accuracy, invalid recall, MCC, kappa, and AUC alongside ordinary accuracy.

Detailed per-round metrics, A-F confusion matrices, and disagreements are in the companion CSV files.
