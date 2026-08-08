FROM verlai/verl:vllm024.dev2@sha256:b867883b0dd011363e69ab2ab344922a28c5bd0409e2a324e3ee70fb27ca7543

ARG VERL_REF=4a2cba76f7f605d2b9f56e640faaeaa71c2c7f71

# The official image supplies the mutually tested CUDA/Torch/vLLM stack.  Pin
# the verl source independently because the application image intentionally
# expects users to install the desired verl checkout with --no-deps.
RUN test ! -e /opt/verl \
    && git init /opt/verl \
    && git -C /opt/verl remote add origin https://github.com/verl-project/verl.git \
    && git -C /opt/verl fetch --depth 1 origin "${VERL_REF}" \
    && git -C /opt/verl checkout --detach FETCH_HEAD
WORKDIR /opt/verl
RUN python3.12 -m pip install -r requirements.txt \
    && python3.12 -m pip install --no-deps -e . \
    && python3.12 -m pip install --no-deps transformers==5.5.3

COPY qwen35/environment/requirements.in /tmp/rzero-qwen35-requirements.in
# Ubuntu's python3-blinker has no pip RECORD.  Overlay it first so Flask's
# dependency resolver never attempts the unsupported Debian-package uninstall.
RUN python3.12 -m pip install --ignore-installed blinker==1.9.0 \
    && python3.12 -m pip install -r /tmp/rzero-qwen35-requirements.in

WORKDIR /workspace/R-Zero
ENV VERL_SOURCE_ROOT=/opt/verl
ENV PYTHONPATH=/opt/verl:/workspace/R-Zero
ENV VLLM_USE_V1=1
