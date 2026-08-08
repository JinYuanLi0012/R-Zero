# R-Zero on Qwen3.5-4B-Base

This directory is an additive, isolated migration of the released R-Zero
algorithm to `Qwen/Qwen3.5-4B-Base`. Existing upstream files are intentionally
left unchanged. Training, rollout, checkpointing and model export are delegated
to upstream verl/vLLM; this directory contains only R-Zero rewards, data
adaptation and fault-tolerant orchestration.

## Fixed formal profile

- Model: `Qwen/Qwen3.5-4B-Base`, revision `1001bb4`
- Runtime: Python 3.12, CUDA 13.0.2, Torch 2.11.0, vLLM 0.24.0,
  Transformers 5.5.3 and verl commit `4a2cba76`; FSDP2 and vLLM text-only
- Hardware: one node with 4×A100 80GB
- Five rounds; Questioner step 5 and Solver step 15
- Released-code voting: online Challenger Solver `n=10`, candidate curation `m=9`
- Difficulty interval `[0.3, 0.8]`
- Four generation shards × 2000 = 8000 raw candidates per round
- Checkpoint every completed step; retain the latest two complete checkpoints

The Challenger stage uses GPUs 0–1 for Questioner training and GPUs 2–3 for
two frozen Solver services. Solver GRPO and benchmarks use all four GPUs.

## Environment

Build from the repository root:

```bash
docker build -f qwen35/environment/Dockerfile -t rzero-qwen35:vllm024 .
docker run --gpus all --ipc=host --shm-size=64g \
  -v "$PWD:/workspace/R-Zero" \
  -v /path/to/runs:/runs \
  -v /path/to/hf-cache:/root/.cache/huggingface \
  -e HF_TOKEN \
  -it rzero-qwen35:vllm024 bash
```

On the target GPU host, capture the fully resolved environment after the
pinned official-image smoke succeeds:

```bash
bash qwen35/environment/capture_lock.sh /runs/environment/requirements.lock
```

The image is derived from the official public
`verlai/verl:vllm024.dev2@sha256:b867883b0dd011363e69ab2ab344922a28c5bd0409e2a324e3ee70fb27ca7543`
application image. It pins the verl checkout at `/opt/verl` to
`4a2cba76f7f605d2b9f56e640faaeaa71c2c7f71`; it does not run verl's legacy
installer or replace the official CUDA/Torch/vLLM dependency stack. As in the
official vLLM CI, it installs that exact verl commit's `requirements.txt`, then
installs verl itself with `--no-deps`. `run.sh` always places
`/opt/verl` before the repository on `PYTHONPATH`, while retaining the repository
as the second entry so verl reward workers can import `qwen35`. Training and the
environment smoke run with `/opt/verl` as their working directory. The smoke
stage rejects any `verl.__file__` outside `/opt/verl`, verifies every pinned
runtime version and the verl Git commit, composes `verl.trainer.main_ppo`
through Hydra, checks `qwen3_5`, the official chat template, four visible GPUs,
and a real vLLM `language_model_only` load-and-generate cycle.

## Dry-run and smoke Round 0

Dry-run does not download models or create a run manifest:

```bash
qwen35/scripts/run.sh \
  --run-dir /runs/rzero-qwen35-formal \
  --config qwen35/configs/a100_4x_qwen35_4b_base.yaml \
  --dry-run
```

Run the reduced one-step, eight-candidate integration profile first:

```bash
qwen35/scripts/run.sh \
  --run-dir /runs/rzero-qwen35-smoke \
  --config qwen35/configs/a100_4x_qwen35_4b_base_smoke.yaml \
  --resume
```

The smoke profile skips the expensive benchmark but exercises model loading,
both GRPO roles, Solver services, four generation/evaluation shards, curation,
checkpoint recovery and model export.

Because a one-step Base-model Questioner may produce no parseable candidate,
the smoke profile may seed Solver training from eight rows of the fixed
validation Parquet. This is recorded as `used_smoke_fallback` in curation
metadata and is forbidden by the formal profile.

## Formal five-round run

```bash
qwen35/scripts/run.sh \
  --run-dir /runs/rzero-qwen35-formal \
  --config qwen35/configs/a100_4x_qwen35_4b_base.yaml \
  --resume
```

Recovery is always from the latest fully committed optimizer step. If a machine
fails during step 3, verl restores complete step 2 and re-executes step 3. The
orchestrator independently validates each generation/evaluation shard, so a
single corrupt shard does not force the other three to rerun.

Before invoking verl, the recovery preflight checks that every expected FSDP
model, optimizer and extra-state rank shard exists. If the official tracker
points at a partial checkpoint, it is atomically rewound to the newest complete
step; checkpoint contents themselves are never rewritten.

Every checkpoint root also contains `RZERO_TRAINING_LINEAGE.json`, binding it to
the role, parent model artifact, training/validation data hashes, total steps and
run configuration fingerprint. Ordinary `--resume` is refused if any of those
inputs differs, or if pre-existing checkpoint state has no lineage file.

To invalidate a stage and every later manifest in the selected graph:

```bash
qwen35/scripts/run.sh ... --resume --from-stage round_02.evaluate.3
```

`--from-stage` is an explicit recomputation, not a failure resume. Before
invalidating manifests, every affected Questioner/Solver checkpoint root is
atomically moved under `RUN_DIR/recompute_backups/<event>/`; affected training
stages then start with verl resume disabled. The move is recorded under
`manifests/recomputations/`. If that fresh training is later interrupted, restart
with plain `--resume` (without repeating `--from-stage`) to resume its latest
complete, lineage-matching step. `--round` and `--from-stage` cannot be combined,
because doing so would leave later-round model lineage stale.

To operate on one round whose dependencies already exist:

```bash
qwen35/scripts/run.sh ... --resume --round 3
```

## Run artifacts

```text
RUN_DIR/
├── environment.json
├── manifests/
│   ├── run.json
│   └── stages/*.json
├── models/base/
├── data/seed/
└── round_01/ ... round_05/
    ├── questioner/{checkpoints,export}/
    ├── generated/shard_{0..3}.json
    ├── scored/shard_{0..3}.json
    ├── dataset/{train.parquet,curation.json}
    ├── solver/{checkpoints,export}/
    ├── evaluation/
    └── logs/
```

The local Parquet file is authoritative. Optional Hugging Face publication is
explicit and idempotent:

```bash
python3.12 -m qwen35.rzero.publish_dataset \
  --dataset /runs/rzero-qwen35-formal/round_01/dataset/train.parquet \
  --repo-id YOUR_ORG/rzero-qwen35 \
  --config-name round_01 \
  --receipt /runs/rzero-qwen35-formal/round_01/dataset/publish.json \
  --private
```

## Local tests and isolation audit

```bash
bash qwen35/scripts/test.sh
git diff --name-status 5699329d018d79535b7910abdedf5a6eebf355fd
git diff --diff-filter=MDR --name-only 5699329d018d79535b7910abdedf5a6eebf355fd
```

The second audit command must print nothing: every migration change must be a
new file under `qwen35/` or `docs/plans/`.
