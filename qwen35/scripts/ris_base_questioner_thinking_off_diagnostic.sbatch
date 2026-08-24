#!/usr/bin/env bash
#SBATCH --account=compute2-jiaxinh
#SBATCH --partition=general-short
#SBATCH --job-name=qwen35-q32-no-think
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --gpus=1
#SBATCH --time=02:00:00
#SBATCH --output=/storage1/fs1/jiaxinh/Active/jinyuan/R-Zero-Qwen3.5/runs/slurm-logs/%x-%j.out
#SBATCH --error=/storage1/fs1/jiaxinh/Active/jinyuan/R-Zero-Qwen3.5/runs/slurm-logs/%x-%j.err

set -euo pipefail

PROJECT=${PROJECT:-/storage1/fs1/jiaxinh/Active/jinyuan/R-Zero-Qwen3.5}
MODEL_DIR=${MODEL_DIR:-${PROJECT}/runs/rzero-qwen35-formal-c150ede/models/base}
OUTPUT_DIR=${OUTPUT_DIR:-${PROJECT}/runs/diagnostics/qwen35-base-questioner-thinking-off-1001bb4}
HF_CACHE=${HF_CACHE:-/scratch2/fs1/jiaxinh/${USER}/hf-cache}
IMAGE=${IMAGE:-/scratch2/fs1/jiaxinh/${USER}/images/rzero-qwen35-bdc8b2c29981.sqsh}
EXPECTED_IMAGE_SHA256=${EXPECTED_IMAGE_SHA256:-26e47958e9b689f21eb63b730fff88c5d13854d407fff592cdddcda87f329ec5}
JOB_TMP=/tmp/${USER}/qwen35-q32-no-think-${SLURM_JOB_ID}

case "${MODEL_DIR}" in
  "${PROJECT}"/*) CONTAINER_MODEL_DIR="/workspace/R-Zero/${MODEL_DIR#"${PROJECT}"/}" ;;
  *) echo "MODEL_DIR must be inside PROJECT: ${MODEL_DIR}" >&2; exit 2 ;;
esac
case "${OUTPUT_DIR}" in
  "${PROJECT}"/*) CONTAINER_OUTPUT_DIR="/workspace/R-Zero/${OUTPUT_DIR#"${PROJECT}"/}" ;;
  *) echo "OUTPUT_DIR must be inside PROJECT: ${OUTPUT_DIR}" >&2; exit 2 ;;
esac

mkdir -p \
  "${PROJECT}/runs/slurm-logs" \
  "${OUTPUT_DIR}" \
  "${HF_CACHE}" \
  "${JOB_TMP}/home" \
  "${JOB_TMP}/triton" \
  "${JOB_TMP}/flashinfer" \
  "${JOB_TMP}/vllm" \
  "${JOB_TMP}/torchinductor" \
  "${JOB_TMP}/cuda"

[[ -s "${MODEL_DIR}/config.json" ]] || { echo "missing Base model: ${MODEL_DIR}" >&2; exit 2; }
[[ -s "${MODEL_DIR}/RZERO_MODEL_REVISION" ]] || {
  echo "missing immutable model revision receipt: ${MODEL_DIR}/RZERO_MODEL_REVISION" >&2
  exit 2
}
[[ "$(<"${MODEL_DIR}/RZERO_MODEL_REVISION")" == "1001bb4" ]] || {
  echo "MODEL_DIR is not Qwen3.5-4B-Base@1001bb4" >&2
  exit 2
}
[[ -s "${IMAGE}" ]] || { echo "missing prepared image: ${IMAGE}" >&2; exit 2; }
image_checksum=$(sha256sum "${IMAGE}")
image_checksum=${image_checksum%% *}
[[ "${image_checksum}" == "${EXPECTED_IMAGE_SHA256}" ]] || {
  echo "prepared image checksum mismatch: got ${image_checksum}, expected ${EXPECTED_IMAGE_SHA256}" >&2
  exit 2
}

echo "job_id=${SLURM_JOB_ID}"
echo "node=${SLURMD_NODENAME:-unknown}"
echo "git_commit=$(git -C "${PROJECT}" rev-parse HEAD)"
echo "model_dir=${MODEL_DIR}"
echo "output_dir=${OUTPUT_DIR}"
echo "image_sha256=${image_checksum}"
nvidia-smi --query-gpu=index,name,memory.total,driver_version --format=csv,noheader

srun \
  --nodes=1 \
  --ntasks=1 \
  --container-image="${IMAGE}" \
  --container-mounts="${PROJECT}:/workspace/R-Zero,${HF_CACHE}:/root/.cache/huggingface" \
  --container-workdir=/opt/verl \
  env \
    HOME="${JOB_TMP}/home" \
    TMPDIR="${JOB_TMP}" \
    PYTHONPATH=/opt/verl:/workspace/R-Zero \
    HF_HOME=/root/.cache/huggingface \
    XDG_CACHE_HOME="${JOB_TMP}/home/.cache" \
    FLASHINFER_WORKSPACE_BASE="${JOB_TMP}/flashinfer" \
    TRITON_CACHE_DIR="${JOB_TMP}/triton" \
    VLLM_CACHE_ROOT="${JOB_TMP}/vllm" \
    TORCHINDUCTOR_CACHE_DIR="${JOB_TMP}/torchinductor" \
    CUDA_CACHE_PATH="${JOB_TMP}/cuda" \
    VLLM_USE_V1=1 \
    VLLM_NO_USAGE_STATS=1 \
    python3.12 -m qwen35.rzero.diagnostics.base_questioner_thinking_off \
      --model "${CONTAINER_MODEL_DIR}" \
      --output-dir "${CONTAINER_OUTPUT_DIR}" \
      --expected-revision 1001bb4 \
      --samples 32 \
      --seed 0 \
      --temperature 1.0 \
      --top-p 0.95 \
      --max-tokens 4096
