# Task-Vector R-Zero

This method keeps the original R-Zero Questioner loop, but changes how every
Solver is obtained. In round `i`, the current questions are labeled by the
current composed Solver, while the new Solver update is trained independently
from the immutable Base:

```text
A_i   = Tune(Base, D_i)
Delta_i = A_i - Base
pi_i  = Base + sum_{k=1..i}(lambda_k * Delta_k)
```

Recomposing from Base on every round is intentional. It is equivalent to
recursive addition in exact arithmetic and avoids repeatedly rounding an
already composed BF16 checkpoint.

At run initialization, a Hub Base is resolved to one immutable commit snapshot;
a local Base is resolved to an absolute path. Config, tokenizer assets and all
safetensors are hashed into `state/base_manifest.json`. Every round uses that
same resolved directory, and resume fails if any tracked Base file changes.

## Two one-command experiment chains

Prepare the normal R-Zero environment and edit `config.sh`. Run the complete
five-round full-delta experiment with:

```bash
source env_rzero.sh
bash methods/task_vector_rzero/run_full_delta.sh \
  --config methods/task_vector_rzero/config.sh
```

Run the independent five-round RELEX rank-1 experiment with:

```bash
bash methods/task_vector_rzero/run_rank1.sh \
  --config methods/task_vector_rzero/config.sh
```

Both commands use the same orchestrator. The full chain always feeds its
full-delta Solver into the next round; the rank-1 chain always feeds its RELEX
rank-1 Solver into the next round. Their run roots and Hugging Face names are
separate.

Rank-1 mode preserves and merges Base-fit checkpoints at steps 5, 10 and 15.
For every tensor it follows RELEX reconstruct mode: form FP16 absolute deltas
relative to the immutable Base, build the FP32 Gram matrix, retain the leading
singular direction, reconstruct the step-15 delta, and save `Base + delta_rank1`
as BF16. The selected steps are configurable through `RANK1_HISTORY_STEPS`.

Resume a run whose completed stages already have `_SUCCESS.json` markers:

```bash
bash methods/task_vector_rzero/run_full_delta.sh \
  --config methods/task_vector_rzero/config.sh \
  --resume
```

Use `--no-eval` for a training smoke test. For a different experiment, use a
different `RUN_NAME`; the runner rejects an existing run whose algorithm or
training configuration fingerprint does not match.

## Round contract

For round `i`:

1. `Q_i` starts from `Q_(i-1)` and trains against composed `pi_(i-1)`.
2. `Q_i` generates questions; composed `pi_(i-1)` labels and filters them.
3. `A_i` always starts from `BASE_MODEL` and trains on local `D_i/train.parquet`.
4. Full mode uses `A_i - Base`; rank-1 mode reconstructs the step-15 delta from
   the per-tensor SVD of step 5/10/15 and keeps only rank 1.
5. The composer rebuilds `pi_i` from Base and all effective full/rank-1 deltas.
6. `pi_i` is validated, optionally uploaded, evaluated, and passed to round `i+1`.

The two Solver paths are deliberately separate in logs and state:
`labeler_model` is the current composed Solver, and `train_init_model` is always
the immutable Base.

## Artifacts

The run is stored under:

```text
$STORAGE_PATH/task_vector_rzero/$RUN_NAME/
  questioners/q1...q5/
  datasets/d1...d5/
  base_fits/a1...a5/
  rank1_fits/r1...r5/       # rank-1 mode
  composed_solvers/v1...v5/
  evaluations/v1...v5/
  state/run_state.json
  logs/
```

Local Parquet is canonical. By default each dataset is also mirrored to a
private Hugging Face dataset. Models remain local unless `UPLOAD_MODELS=true`.
Raw evaluated question shards are retained next to each Parquet dataset.

Every composed Solver contains:

- `task_vector_manifest.json`: Base, auxiliary models, scales, shards and hashes.
- `task_vector_diagnostics.json`: vector norms, per-tensor norms, Gram matrix and
  cosine similarities.

For tied models such as Qwen3, the composer follows RELEX: `embed_tokens` is the
canonical task-vector tensor and redundant `lm_head.weight` storage is ignored.
Transformers recreates the tie when loading the checkpoint. Formal runs also
perform a real `AutoModelForCausalLM` and tokenizer load after every composition;
set `FULL_LOAD_VALIDATE=false` only for lightweight component debugging.

## Composer

The composer accepts local Hugging Face checkpoints or a Hub Base model:

```bash
python methods/task_vector_rzero/compose_task_vectors.py \
  --base Qwen/Qwen3-4B-Base \
  --auxiliary /path/to/a1/huggingface --scale 1 \
  --auxiliary /path/to/a2/huggingface --scale 1 \
  --output /path/to/composed_v2
```

It validates model configs, tensor keys and shapes; computes in FP32; rejects
NaN/Inf; and saves BF16 safetensors. Work is processed by model shard and tensor
chunks, so all full checkpoints are never loaded into RAM simultaneously.

## Existing-artifact V2 validation

To validate the teacher's proposal with existing artifacts, run:

```bash
bash methods/task_vector_rzero/validate_existing_v2.sh \
  Qwen/Qwen3-4B-Base \
  jinyuan222/qwen3_4b_fullrun_authorsettings_solver_v1 \
  jinyuan222/SECOND_ROUND_DATASET@train \
  "$STORAGE_PATH/task_vector_rzero/existing_v2_validation"
```

The script performs exactly this experiment:

1. Treat the existing standard `V1` as `A1`.
2. Train a new `A2` from Base on the existing second-round question Parquet.
3. Compose `Base + (V1 - Base) + (A2 - Base)`.
4. Run `evaluation/evaluate.bash` only for the composed V2 and compare it with
   the recorded standard V2.

This does not require regenerating questions or reevaluating Base/V1.

## Tests

In the training environment (where `torch` and `safetensors` are installed):

```bash
python -m unittest discover -s methods/task_vector_rzero/tests -v
```
