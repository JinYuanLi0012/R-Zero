# RIS Slurm 运行手册（Qwen3.5）

本文记录 2026-08-08 在 Washington University RIS Compute2 上的实际调试结果。
它只适用于 `feature/qwen3.5-4b-base`，不改变原始 R-Zero 工作树。

## 当前验证边界

已经实测通过：

- `general-short` 单张 NVIDIA H100 80GB（driver `580.105.08`）。
- Pyxis 从公开 GHCR 拉取并启动固定的 Qwen3.5 运行时镜像。
- Python 3.12、CUDA、Torch、官方 `/opt/verl` 来源检查。
- 本地 `Qwen/Qwen3.5-4B-Base@1001bb4` 的 vLLM
  `language_model_only=True` 加载和真实文本生成。
- Gated DeltaNet 的 Triton kernel 首次 JIT 编译。

尚未验证：

- 四卡环境 smoke、FSDP2 GRPO 更新/checkpoint/HF export。
- 缩小版 Round 0 和正式五轮训练。

因此单卡成功不能替代四卡 Round 0 验收。

## 固定资源和路径

```bash
export PROJECT=/storage1/fs1/jiaxinh/Active/jinyuan/R-Zero-Qwen3.5
export RUN_ROOT=$PROJECT/runs/rzero-qwen35
export HF_CACHE=/scratch2/fs1/jiaxinh/$USER/hf-cache

export ENROOT_CACHE_PATH=/scratch2/fs1/jiaxinh/$USER/enroot-cache
export ENROOT_DATA_PATH=/tmp/$USER/enroot-data
export ENROOT_TEMP_PATH=/tmp/$USER/enroot-tmp
export TMPDIR=/tmp
```

用途约定：

- `/storage1/.../R-Zero-Qwen3.5/runs`：模型、dataset、checkpoint、manifest，持久化。
- `/scratch2/.../hf-cache`：Hugging Face 缓存，持久化共享。
- `/scratch2/.../enroot-cache`：镜像下载缓存。
- 计算节点 `/tmp`：Enroot 展开目录和 GPU 编译缓存；任务结束后允许丢失。
- 不把 Enroot data/temp 或 GPU JIT 缓存放进配额较小的 Home。

模型已经解析到：

```text
/storage1/fs1/jiaxinh/Active/jinyuan/R-Zero-Qwen3.5/runs/rzero-qwen35/models/base
```

## 固定运行时

成功实测的镜像引用：

```text
ghcr.io/jinyuanli0012/rzero-qwen35:verl-main-vllm024
sha256:bdc8b2c299813f958489686e0e5a2b9d97dcc94b66af81069b7db88aa040cfb7
```

镜像底座和关键依赖：

```text
verlai/verl:vllm024.dev2
base digest: sha256:b867883b0dd011363e69ab2ab344922a28c5bd0409e2a324e3ee70fb27ca7543
verl commit: 4a2cba76f7f605d2b9f56e640faaeaa71c2c7f71
Python: 3.12
CUDA: 13.0.2
Torch: 2.11.0
vLLM: 0.24.0
Transformers: 5.5.3
```

所有容器内训练进程必须满足：

```bash
cd /opt/verl
export PYTHONPATH=/opt/verl:/workspace/R-Zero
```

`/opt/verl` 必须排在仓库之前，否则仓库旧版 `verl/` 会遮蔽官方版本。

## Slurm 分区结论

- 账户：`compute2-jiaxinh`。
- `general-short`：已成功申请一张 H100；四卡请求会触发
  `QOSMaxGRESPerUser`，只用于单卡诊断。
- `general-gpu`：用于四卡任务。2026-08-08 的一次 `sbatch --test-only`
  估计约等待五天；这只是调度器瞬时预测，不是保证。
- 当时没有真正提交四卡作业。

查看队列和预估：

```bash
squeue -u "$USER" -o "%.10i %.12u %.20j %.8T %.10M %.4D %R"
squeue --start -j JOB_ID
scontrol show job JOB_ID
```

四卡提交前只做调度预测：

```bash
sbatch --test-only \
  -A compute2-jiaxinh \
  -p general-gpu \
  --nodes=1 \
  --ntasks=1 \
  --cpus-per-task=16 \
  --mem=128G \
  --gpus=4 \
  --time=00:30:00 \
  --job-name=rzero-env-smoke \
  --wrap=true
```

## 已成功的单卡 vLLM smoke

先设置节点本地缓存。FlashInfer 不使用 `XDG_CACHE_HOME` 作为其主工作目录，
所以 `FLASHINFER_WORKSPACE_BASE` 必须单独设置：

```bash
export XDG_CACHE_HOME=/tmp/$USER/xdg-cache
export TRITON_CACHE_DIR=/tmp/$USER/triton-cache
export TORCHINDUCTOR_CACHE_DIR=/tmp/$USER/torchinductor-cache
export CUDA_CACHE_PATH=/tmp/$USER/cuda-cache
export VLLM_CACHE_ROOT=/tmp/$USER/vllm-cache
export FLASHINFER_WORKSPACE_BASE=/tmp/$USER/flashinfer-workspace
```

以下参数组合已在一张 H100 上真实成功：

```bash
srun \
  -A compute2-jiaxinh \
  -p general-short \
  --nodes=1 \
  --ntasks=1 \
  --cpus-per-task=16 \
  --mem=128G \
  --gpus=1 \
  --time=00:30:00 \
  --job-name=rzero-qwen35-vllm-smoke \
  --container-image='ghcr.io#jinyuanli0012/rzero-qwen35:verl-main-vllm024' \
  --container-mounts="$PROJECT:/workspace/R-Zero,$HF_CACHE:/root/.cache/huggingface" \
  --container-workdir=/opt/verl \
  env \
    PYTHONPATH=/opt/verl:/workspace/R-Zero \
    HF_HOME=/root/.cache/huggingface \
    VLLM_USE_V1=1 \
  python3.12 -c '
from pathlib import Path
import torch
import transformers
import verl
import vllm
from vllm import LLM, SamplingParams

print("verl:", Path(verl.__file__).resolve())
print("torch:", torch.__version__)
print("transformers:", transformers.__version__)
print("vllm:", vllm.__version__)
print("GPU:", torch.cuda.get_device_name(0))

assert str(Path(verl.__file__).resolve()).startswith("/opt/verl/")
assert vllm.__version__ == "0.24.0"
assert transformers.__version__ == "5.5.3"

model = "/workspace/R-Zero/runs/rzero-qwen35/models/base"
llm = LLM(
    model=model,
    tokenizer=model,
    tensor_parallel_size=1,
    dtype="bfloat16",
    language_model_only=True,
    max_model_len=4096,
    gpu_memory_utilization=0.70,
    enforce_eager=True,
    enable_chunked_prefill=False,
)
outputs = llm.generate(
    ["Solve carefully: What is 17 multiplied by 23?"],
    SamplingParams(temperature=0.0, max_tokens=64),
)
print("GENERATED:", outputs[0].outputs[0].text)
print("QWEN35_VLLM_SMOKE_OK")
'
```

成功判据是产生非空文本并打印：

```text
QWEN35_VLLM_SMOKE_OK
```

第一次请求出现
`fused_recurrent_gated_delta_rule_packed_decode_kernel` JIT latency warning 是
Gated DeltaNet kernel 首次编译，不代表启用了训练数据 packed/remove-padding
路径。进程退出时的 EngineCore SIGTERM/cleanup 信息也不是 smoke 失败。

## 已排除的失败路线

1. `verl v0.8.0 + vLLM 0.11.0`：vLLM 不接受 `language_model_only`，不能作为
   Qwen3.5 文本 RL 底座。不要通过删除该参数绕过。
2. 仓库根目录作为 cwd/PYTHONPATH 首项：会导入仓库旧版 `verl/`。必须从
   `/opt/verl` 启动并把它放在 `PYTHONPATH` 第一位。
3. Enroot data/temp 放在 scratch NFS：镜像虽然能导入，但曾在容器启动时报
   `/bin/sh: Permission denied`。data/temp 使用节点本地 `/tmp`。
4. Enroot cache 使用 Home：Home 空间不足，镜像层下载失败。下载 cache 使用
   `/scratch2`。
5. Triton/FlashInfer cache 使用 Home：分别触发 `No space left on device`，并
   伪装成模型架构检查或 Engine Core 失败。GPU 编译 cache 使用节点本地
   `/tmp`。
6. 在 `bash -lc` 中再次嵌套长 Python 引号：容易产生 `unexpected EOF`。诊断
   命令使用 `env ... python3.12 -c '...'` 这一层引号结构。

## 正式入口中的固化行为

`qwen35/scripts/run.sh` 已自动设置以下缓存变量，无需在每次正式 pipeline
命令前手工重复：

```text
XDG_CACHE_HOME
TRITON_CACHE_DIR
TORCHINDUCTOR_CACHE_DIR
CUDA_CACHE_PATH
VLLM_CACHE_ROOT
FLASHINFER_WORKSPACE_BASE
```

Slurm 下默认根目录是：

```text
/tmp/rzero-qwen35-$UID/$SLURM_JOB_ID
```

这些只是可重建缓存。`--run-dir` 必须继续指向 `/storage1` 下的持久目录。

## 下一验收点

下一步只提交缩小版四卡 Round 0，不直接开始正式五轮。仓库已经提供
`qwen35/scripts/ris_round0_smoke.sbatch`，固定请求单节点、4 GPU、32 CPU、
512 GB RAM 和 8 小时。[RIS Compute2 General Guidelines](https://washu.atlassian.net/wiki/spaces/RUD/pages/2140667974/Compute2%2BGeneral%2BGuidelines)
记录的 `general-gpu` 上限为 15 天，因此该时限合法；
8 小时是故障保护上限，不代表预计一定运行 8 小时。

提交脚本使用构建 commit 对应的不可变镜像标签
`commit-81d554f1c4a871cc19387db929b1fad4a78cf170`，而不是依赖可能被未来构建
更新的友好标签。

拉取最新分支后先创建 Slurm 输出目录：

```bash
cd /storage1/fs1/jiaxinh/Active/jinyuan/R-Zero-Qwen3.5
mkdir -p runs/slurm-logs
```

只查询预计启动时间，不提交：

```bash
sbatch --test-only qwen35/scripts/ris_round0_smoke.sbatch
```

确认预估后正式提交：

```bash
sbatch qwen35/scripts/ris_round0_smoke.sbatch
```

脚本在同一四卡 allocation 内先执行 pipeline `--dry-run`，成功后才执行：

```bash
qwen35/scripts/run.sh \
  --run-dir /workspace/R-Zero/runs/rzero-qwen35-smoke \
  --config /workspace/R-Zero/qwen35/configs/a100_4x_qwen35_4b_base_smoke.yaml \
  --resume
```

观察任务：

```bash
squeue -j JOB_ID -o "%.10i %.8T %.10M %.20R"
squeue --start -j JOB_ID
tail -f runs/slurm-logs/rzero-qwen35-round0-smoke-JOB_ID.out
```

取消任务（只在确实需要停止时执行）：

```bash
scancel JOB_ID
```

`--resume` 是故障恢复语义；同一 `RUN_DIR` 已提交的完整 stage 会跳过，未完成
stage 会继续。不要为普通失败追加 `--from-stage`。
