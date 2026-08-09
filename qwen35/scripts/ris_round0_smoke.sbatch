#!/usr/bin/env bash
#SBATCH --account=compute2-jiaxinh
#SBATCH --partition=general-gpu
#SBATCH --job-name=rzero-qwen35-round0-smoke
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=512G
#SBATCH --gpus=4
#SBATCH --time=08:00:00
#SBATCH --output=/storage1/fs1/jiaxinh/Active/jinyuan/R-Zero-Qwen3.5/runs/slurm-logs/%x-%j.out
#SBATCH --error=/storage1/fs1/jiaxinh/Active/jinyuan/R-Zero-Qwen3.5/runs/slurm-logs/%x-%j.err

set -euo pipefail

PROJECT=${PROJECT:-/storage1/fs1/jiaxinh/Active/jinyuan/R-Zero-Qwen3.5}
RUN_DIR=${PROJECT}/runs/rzero-qwen35-smoke
HF_CACHE=${HF_CACHE:-/scratch2/fs1/jiaxinh/${USER}/hf-cache}
IMAGE=${IMAGE:-ghcr.io#jinyuanli0012/rzero-qwen35:commit-81d554f1c4a871cc19387db929b1fad4a78cf170}

export ENROOT_CACHE_PATH=${ENROOT_CACHE_PATH:-/scratch2/fs1/jiaxinh/${USER}/enroot-cache}
export ENROOT_DATA_PATH=${ENROOT_DATA_PATH:-/tmp/${USER}/enroot-data-${SLURM_JOB_ID}}
export ENROOT_TEMP_PATH=${ENROOT_TEMP_PATH:-/tmp/${USER}/enroot-tmp-${SLURM_JOB_ID}}
export TMPDIR=/tmp

mkdir -p \
  "${ENROOT_CACHE_PATH}" \
  "${ENROOT_DATA_PATH}" \
  "${ENROOT_TEMP_PATH}" \
  "${HF_CACHE}" \
  "${PROJECT}/runs/slurm-logs" \
  "${RUN_DIR}"

echo "job_id=${SLURM_JOB_ID}"
echo "node=${SLURMD_NODENAME:-unknown}"
echo "project=${PROJECT}"
echo "run_dir=${RUN_DIR}"
echo "image=${IMAGE}"
nvidia-smi --query-gpu=index,name,memory.total,driver_version --format=csv,noheader

srun \
  --nodes=1 \
  --ntasks=1 \
  --container-image="${IMAGE}" \
  --container-mounts="${PROJECT}:/workspace/R-Zero,${HF_CACHE}:/root/.cache/huggingface" \
  --container-workdir=/opt/verl \
  env \
    PYTHONPATH=/opt/verl:/workspace/R-Zero \
    HF_HOME=/root/.cache/huggingface \
    VLLM_USE_V1=1 \
  bash /workspace/R-Zero/qwen35/scripts/run.sh \
    --run-dir /workspace/R-Zero/runs/rzero-qwen35-smoke \
    --config /workspace/R-Zero/qwen35/configs/a100_4x_qwen35_4b_base_smoke.yaml \
    --dry-run

srun \
  --nodes=1 \
  --ntasks=1 \
  --container-image="${IMAGE}" \
  --container-mounts="${PROJECT}:/workspace/R-Zero,${HF_CACHE}:/root/.cache/huggingface" \
  --container-workdir=/opt/verl \
  env \
    PYTHONPATH=/opt/verl:/workspace/R-Zero \
    HF_HOME=/root/.cache/huggingface \
    VLLM_USE_V1=1 \
  bash /workspace/R-Zero/qwen35/scripts/run.sh \
    --run-dir /workspace/R-Zero/runs/rzero-qwen35-smoke \
    --config /workspace/R-Zero/qwen35/configs/a100_4x_qwen35_4b_base_smoke.yaml \
    --resume
