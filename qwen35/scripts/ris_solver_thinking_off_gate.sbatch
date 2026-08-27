#!/usr/bin/env bash
#SBATCH --account=compute2-jiaxinh
#SBATCH --partition=general-gpu
#SBATCH --job-name=qwen35-s-no-think
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=256G
#SBATCH --gpus=1
#SBATCH --time=7-00:00:00
#SBATCH --output=/storage1/fs1/jiaxinh/Active/jinyuan/R-Zero-Qwen3.5/runs/slurm-logs/%x-%j.out
#SBATCH --error=/storage1/fs1/jiaxinh/Active/jinyuan/R-Zero-Qwen3.5/runs/slurm-logs/%x-%j.err

set -euo pipefail

PROJECT=${PROJECT:-/storage1/fs1/jiaxinh/Active/jinyuan/R-Zero-Qwen3.5}
SOURCE_RUN_DIR=${SOURCE_RUN_DIR:-${PROJECT}/runs/rzero-qwen35-questioner-thinking-off-one-step}
CANDIDATES=${CANDIDATES:-${SOURCE_RUN_DIR}/round_01/diagnostics/solver_n9_gate/candidates.json}
SOLVER_MODEL=${SOLVER_MODEL:-${PROJECT}/runs/rzero-qwen35-formal-c150ede/models/base}
OUTPUT_DIR=${OUTPUT_DIR:-${SOURCE_RUN_DIR}/round_01/diagnostics/solver_n9_thinking_off_gate}
HF_CACHE=${HF_CACHE:-/scratch2/fs1/jiaxinh/${USER}/hf-cache}
IMAGE=${IMAGE:-/scratch2/fs1/jiaxinh/${USER}/images/rzero-qwen35-bdc8b2c29981.sqsh}
EXPECTED_IMAGE_SHA256=${EXPECTED_IMAGE_SHA256:-26e47958e9b689f21eb63b730fff88c5d13854d407fff592cdddcda87f329ec5}

PYXIS_XDG_CACHE_HOME=/scratch2/fs1/jiaxinh/${USER}/pyxis-cache
PYXIS_XDG_DATA_HOME=/tmp/${USER}/pyxis-data-${SLURM_JOB_ID}
PYXIS_TMPDIR=/tmp/${USER}/pyxis-tmp-${SLURM_JOB_ID}
export SLURM_EXPORT_ENV=ALL

for value in CANDIDATES SOLVER_MODEL OUTPUT_DIR; do
  path=${!value}
  case "${path}" in
    "${PROJECT}"/*) ;;
    *) echo "${value} must be inside PROJECT: ${path}" >&2; exit 2 ;;
  esac
done
CONTAINER_CANDIDATES="/workspace/R-Zero/${CANDIDATES#"${PROJECT}"/}"
CONTAINER_SOLVER_MODEL="/workspace/R-Zero/${SOLVER_MODEL#"${PROJECT}"/}"
CONTAINER_OUTPUT_DIR="/workspace/R-Zero/${OUTPUT_DIR#"${PROJECT}"/}"

mkdir -p \
  "${PYXIS_XDG_CACHE_HOME}" "${PYXIS_XDG_DATA_HOME}" "${PYXIS_TMPDIR}" \
  "${HF_CACHE}" "${PROJECT}/runs/slurm-logs" "${OUTPUT_DIR}"

[[ -s "${CANDIDATES}" ]] || { echo "missing fixed 64-candidate input: ${CANDIDATES}" >&2; exit 2; }
[[ -s "${SOLVER_MODEL}/config.json" ]] || { echo "missing frozen Base Solver" >&2; exit 2; }
[[ -s "${SOLVER_MODEL}/RZERO_MODEL_REVISION" ]] || { echo "missing Solver revision receipt" >&2; exit 2; }
[[ "$(<"${SOLVER_MODEL}/RZERO_MODEL_REVISION")" == "1001bb4" ]] || {
  echo "Solver is not Qwen3.5-4B-Base@1001bb4" >&2; exit 2;
}
[[ -s "${IMAGE}" ]] || { echo "missing prepared image: ${IMAGE}" >&2; exit 2; }
image_checksum=$(sha256sum "${IMAGE}")
image_checksum=${image_checksum%% *}
[[ "${image_checksum}" == "${EXPECTED_IMAGE_SHA256}" ]] || {
  echo "prepared image checksum mismatch: got ${image_checksum}, expected ${EXPECTED_IMAGE_SHA256}" >&2
  exit 2
}
candidate_checksum=$(sha256sum "${CANDIDATES}")
candidate_checksum=${candidate_checksum%% *}

echo "job_id=${SLURM_JOB_ID}"
echo "node=${SLURMD_NODENAME:-unknown}"
echo "git_commit=$(git -C "${PROJECT}" rev-parse HEAD)"
echo "candidates=${CANDIDATES}"
echo "candidates_sha256=${candidate_checksum}"
echo "solver_model=${SOLVER_MODEL}"
echo "output_dir=${OUTPUT_DIR}"
echo "image_sha256=${image_checksum}"
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
    VLLM_NO_USAGE_STATS=1 \
  bash /workspace/R-Zero/qwen35/scripts/solver_thinking_off_gate.sh \
    --candidates "${CONTAINER_CANDIDATES}" \
    --solver-model "${CONTAINER_SOLVER_MODEL}" \
    --output-dir "${CONTAINER_OUTPUT_DIR}"
