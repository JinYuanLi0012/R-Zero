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
IMAGE=${IMAGE:-/scratch2/fs1/jiaxinh/${USER}/images/rzero-qwen35-bdc8b2c29981.sqsh}

PYXIS_XDG_CACHE_HOME=/scratch2/fs1/jiaxinh/${USER}/pyxis-cache
PYXIS_XDG_DATA_HOME=/tmp/${USER}/pyxis-data-${SLURM_JOB_ID}
PYXIS_TMPDIR=/tmp/${USER}/pyxis-tmp-${SLURM_JOB_ID}
export SLURM_EXPORT_ENV=ALL

mkdir -p \
  "${PYXIS_XDG_CACHE_HOME}" \
  "${PYXIS_XDG_DATA_HOME}" \
  "${PYXIS_TMPDIR}" \
  "${HF_CACHE}" \
  "${PROJECT}/runs/slurm-logs" \
  "${RUN_DIR}"

if [[ ! -s "${IMAGE}" ]]; then
  echo "missing prepared image: ${IMAGE}" >&2
  echo "submit qwen35/scripts/ris_prepare_image.sbatch first" >&2
  exit 2
fi

echo "job_id=${SLURM_JOB_ID}"
echo "node=${SLURMD_NODENAME:-unknown}"
echo "project=${PROJECT}"
echo "run_dir=${RUN_DIR}"
echo "image=${IMAGE}"
nvidia-smi --query-gpu=index,name,memory.total,driver_version --format=csv,noheader

srun \
  --nodes=1 \
  --ntasks=1 \
  --export="ALL,XDG_CACHE_HOME=${PYXIS_XDG_CACHE_HOME},XDG_DATA_HOME=${PYXIS_XDG_DATA_HOME},TMPDIR=${PYXIS_TMPDIR}" \
  --container-image="${IMAGE}" \
  --container-mounts="${PROJECT}:/workspace/R-Zero,${HF_CACHE}:/root/.cache/huggingface" \
  --container-workdir=/opt/verl \
  env -u XDG_CACHE_HOME -u XDG_DATA_HOME \
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
  --export="ALL,XDG_CACHE_HOME=${PYXIS_XDG_CACHE_HOME},XDG_DATA_HOME=${PYXIS_XDG_DATA_HOME},TMPDIR=${PYXIS_TMPDIR}" \
  --container-image="${IMAGE}" \
  --container-mounts="${PROJECT}:/workspace/R-Zero,${HF_CACHE}:/root/.cache/huggingface" \
  --container-workdir=/opt/verl \
  env -u XDG_CACHE_HOME -u XDG_DATA_HOME \
    PYTHONPATH=/opt/verl:/workspace/R-Zero \
    HF_HOME=/root/.cache/huggingface \
    VLLM_USE_V1=1 \
  bash /workspace/R-Zero/qwen35/scripts/run.sh \
    --run-dir /workspace/R-Zero/runs/rzero-qwen35-smoke \
    --config /workspace/R-Zero/qwen35/configs/a100_4x_qwen35_4b_base_smoke.yaml \
    --resume
