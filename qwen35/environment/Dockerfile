FROM nvidia/cuda:12.8.1-cudnn-devel-ubuntu24.04

ARG VERL_REF=v0.8.0
ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    git python3.12 python3.12-dev python3.12-venv ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

RUN python3.12 -m venv /opt/rzero-venv \
    && /opt/rzero-venv/bin/python -m pip install --upgrade pip setuptools wheel
ENV PATH=/opt/rzero-venv/bin:${PATH}

WORKDIR /opt
RUN git clone --branch "${VERL_REF}" --depth 1 https://github.com/verl-project/verl.git
WORKDIR /opt/verl
RUN USE_MEGATRON=0 USE_SGLANG=0 bash scripts/install_vllm_sglang_mcore.sh \
    && python3.12 -m pip install --no-deps -e .

COPY qwen35/environment/requirements.in /tmp/rzero-qwen35-requirements.in
RUN python3.12 -m pip install -r /tmp/rzero-qwen35-requirements.in

WORKDIR /workspace/R-Zero
ENV VERL_SOURCE_ROOT=/opt/verl
ENV PYTHONPATH=/opt/verl:/workspace/R-Zero
ENV VLLM_USE_V1=1
