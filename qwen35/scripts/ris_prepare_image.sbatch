#!/usr/bin/env bash
#SBATCH --account=compute2-jiaxinh
#SBATCH --partition=general-short
#SBATCH --job-name=rzero-qwen35-image
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=00:30:00
#SBATCH --output=/storage1/fs1/jiaxinh/Active/jinyuan/R-Zero-Qwen3.5/runs/slurm-logs/%x-%j.out
#SBATCH --error=/storage1/fs1/jiaxinh/Active/jinyuan/R-Zero-Qwen3.5/runs/slurm-logs/%x-%j.err

set -euo pipefail

SCRATCH_ROOT=${SCRATCH_ROOT:-/scratch2/fs1/jiaxinh/${USER}}
IMAGE_DIR=${IMAGE_DIR:-${SCRATCH_ROOT}/images}
IMAGE_PATH=${IMAGE_PATH:-${IMAGE_DIR}/rzero-qwen35-bdc8b2c29981.sqsh}
IMAGE_URI=${IMAGE_URI:-docker://ghcr.io#jinyuanli0012/rzero-qwen35:commit-81d554f1c4a871cc19387db929b1fad4a78cf170}
TEMP_IMAGE=${IMAGE_PATH}.partial-${SLURM_JOB_ID}

# This job calls Enroot directly, not through Pyxis. Direct Enroot honors these
# paths, while Pyxis intentionally filters ENROOT_* variables from job steps.
export ENROOT_CACHE_PATH=${SCRATCH_ROOT}/enroot-cache
export ENROOT_DATA_PATH=/tmp/${USER}/enroot-import-data-${SLURM_JOB_ID}
export ENROOT_TEMP_PATH=/tmp/${USER}/enroot-import-tmp-${SLURM_JOB_ID}
export TMPDIR=/tmp

mkdir -p "${IMAGE_DIR}" "${ENROOT_CACHE_PATH}" "${ENROOT_DATA_PATH}" "${ENROOT_TEMP_PATH}"

if [[ -s "${IMAGE_PATH}" ]]; then
  echo "image already prepared: ${IMAGE_PATH}"
  sha256sum "${IMAGE_PATH}" | tee "${IMAGE_PATH}.sha256"
  exit 0
fi

cleanup() {
  rm -f "${TEMP_IMAGE}"
}
trap cleanup EXIT

echo "importing ${IMAGE_URI}"
echo "output=${IMAGE_PATH}"
enroot import --output "${TEMP_IMAGE}" "${IMAGE_URI}"
test -s "${TEMP_IMAGE}"
mv "${TEMP_IMAGE}" "${IMAGE_PATH}"
trap - EXIT
sha256sum "${IMAGE_PATH}" | tee "${IMAGE_PATH}.sha256"
