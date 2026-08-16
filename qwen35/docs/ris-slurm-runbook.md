# RIS Slurm 运行手册（Qwen3.5）

本文记录 2026-08-08 在 Washington University RIS Compute2 上的实际调试结果。
它只适用于 `feature/qwen3.5-4b-base`，不改变原始 R-Zero 工作树。

## 完整 population 奖励的 Ray 并发

正式 Questioner 的奖励 population 包含 `512 × 4 = 2048` 条 trajectory。
Ray async actor 默认只允许 1000 个并发调用，而 R-Zero population manager
必须收齐全部 2048 条后才能返回任意单条奖励；默认限制会让前 1000 条等待、
后 1048 条无法进入，形成确定性死锁。`qwen35.rzero.verl_main_ppo` 保持官方
verl trainer 和 RewardLoopWorker 的创建流程，只把这个单一 R-Zero reward
actor 的 `max_concurrency` 动态提高到完整 population 大小。禁止用多个 reward
worker 拆分 population，因为这会改变 BLEU diversity reward 的语义。
由于 manager 实际在远端 CPU `TaskRunner` 中构造，兼容层只包装该 actor 的
`run()` 入口：先在 TaskRunner 进程内安装补丁，再委托给未修改的官方实现。
不得使用 job-wide 或可继承的 `worker_process_setup_hook`，否则补丁会提前进入
GPU/FSDP child worker。训练日志必须出现
`RZERO_REWARD_LOOP_MAX_CONCURRENCY=2048`。

## 当前验证边界

已经实测通过：

- `general-short` 单张 NVIDIA H100 80GB（driver `580.105.08`）。
- Pyxis 从公开 GHCR 拉取并启动固定的 Qwen3.5 运行时镜像。
- Python 3.12、CUDA、Torch、官方 `/opt/verl` 来源检查。
- 本地 `Qwen/Qwen3.5-4B-Base@1001bb4` 的 vLLM
  `language_model_only=True` 加载和真实文本生成。
- Gated DeltaNet 的 Triton kernel 首次 JIT 编译。

尚未验证：

- FSDP2 GRPO 更新/checkpoint/HF export。
- 缩小版 Round 0 和正式五轮训练。

因此单卡成功不能替代四卡 Round 0 验收。

## 最短 Solver gate

Compute1 one-step baseline 已成功完成 Questioner step 1、Questioner export、候选
生成、评分和 curate，但整理结果只有 32 行。verl 的训练 DataLoader 会丢弃不足
`train_batch_size=512` 的尾 batch，因此 Solver 在模型加载前以
`Train dataloader is empty` 退出。这不是模型、显存或 reward 故障。

为了尽快验证剩余的 Solver FSDP2 update、checkpoint 和官方 HF export，不再从头
运行完整 smoke。`solver_gate.sh` 直接读取该 baseline 的 32 行 Parquet，使用已有
轻量 smoke profile（4 prompts、Solver rollout `n=5`、一步、最大回复 512 tokens）
并写入完全独立的输出目录：

```bash
bash /workspace/R-Zero/qwen35/scripts/solver_gate.sh \
  --source-run-dir /workspace/R-Zero/runs/rzero-qwen35-one-step \
  --output-dir /workspace/R-Zero/runs/rzero-qwen35-solver-gate
```

成功标志是 `RZERO_SOLVER_GATE_OK`。该 gate 只验证工程链路，不声称复现正式 Solver
训练效果；正式配置仍保持 512 prompts、`n=5`、128 prompts/optimizer mini-batch。
在 Compute2 登录节点应使用后台 Slurm 脚本提交，而不是直接前台 `srun`：

```bash
mkdir -p runs/slurm-logs
sbatch qwen35/scripts/ris_solver_gate.sbatch
```

脚本已固定 `compute2-jiaxinh`、`general-gpu`、4 GPUs、32 CPUs、512 GB RAM 和
4 小时时限；SSH 断开不会终止作业。登录 shell 不要设置 `set -e`，否则任一提交
错误都会直接结束该 shell。

Compute2 首次 gate 已成功启动四个 vLLM server，但在生成前发现固定 verl 的另一项
缩小 batch 约束：4 prompts × `n=5` 产生 20 trajectories，而官方默认 8 个
agent-loop workers 的 `DataProto.chunk(8)` 只支持严格等分。训练适配器现按
`gcd(8, prompt_batch × n)` 选择最大合法 worker 数，所以 gate 使用 4；Questioner
正式 population 2048 和 Solver 正式 population 2560 都仍使用官方默认 8。该值只
改变 CPU agent-loop 请求分发并发，不改变采样数、trajectory、reward 或 optimizer
batch 语义。Compute2 失败发生在首个 rollout 请求前，没有 checkpoint；拉取修复后
可在同一 gate 输出目录使用 `--resume` 安全重试。

curation 现始终检查输出至少能组成一个 Solver training batch。正式 profile 不足
512 行会在 curate 阶段提前失败，绝不重复训练题；只有非正式集成 profile 才允许
确定性重复已有题目到一个 batch，并在 `curation.json` 分别登记唯一题数、训练行数
和重复行数。

2026-08-09 的首个四卡作业 `2692300` 已成功获得 4×H100、完成 pipeline
dry-run、模型解析和 seed data 准备，但 environment smoke 在真正加载模型前被
过严的版本断言终止：PyTorch 正常报告 CUDA ABI `13.0`，而固定镜像版本是
`13.0.2`。校验现已改为要求 CUDA major.minor 一致；patch 级镜像内容继续由
不可变 digest 锁定。同一 run directory 可用 `--resume` 跳过已完成 stage。

同日作业 `2693471` 在 Pyxis 导入前失败。虽然 batch shell 已设置
`ENROOT_CACHE_PATH`，该值没有进入 SPANK job-step 环境，Enroot 仍尝试在已满的
`$HOME/.cache/enroot` 创建 registry token。随后使用 `srun --export` 的单卡
复现实验仍然失败。NVIDIA Pyxis 源码明确将 `ENROOT_CACHE_PATH`、
`ENROOT_DATA_PATH` 和 `ENROOT_TEMP_PATH` 列入 job environment denylist；因此这
三项不能作为 Pyxis 启动参数。最终方案是先用裸 Enroot 将固定 OCI 镜像原子
导入 scratch 上的 SquashFS，再让 Pyxis 直接加载该文件，彻底移除正式作业的
registry/token 步骤。参见 [Pyxis `enroot_deny_env`](https://github.com/NVIDIA/pyxis/blob/main/pyxis_slurmstepd.c#L360-L388)。

作业 `2696377` 随后成功生成 24.1 GB SquashFS：

```text
/scratch2/fs1/jiaxinh/ljinyuan/images/rzero-qwen35-bdc8b2c29981.sqsh
sha256:26e47958e9b689f21eb63b730fff88c5d13854d407fff592cdddcda87f329ec5
```

该文件已在 `general-short` 的一张 H100 上由 Pyxis 直接启动，容器确认导入
`/opt/verl/verl/__init__.py` 并打印 `PYXIS_SQSH_OK`。四卡脚本会在启动容器前
重新计算并核对上述 SHA256。

四卡作业 `2696442` 随后通过 environment smoke 并进入真实
`round_01.questioner_train`。冻结 Solver 已完成 vLLM 初始化，但 Flask 因共享
节点上的 TCP `5000` 已被占用而退出。Solver service 现通过 Werkzeug 以端口
`0` 让操作系统原子分配空闲端口，再用原子 JSON receipt 将实际 endpoint 回传
给 orchestrator；配置中的旧固定端口仅为已有 run fingerprint 兼容而保留，不再
用于绑定。

下一次作业进入官方 `verl.trainer.main_ppo` 后，Hydra 默认尝试在只读 SquashFS
中的 `/opt/verl/outputs` 创建运行目录并失败。训练命令现显式设置
`hydra.run.dir=ROUND_DIR/logs/hydra/EXPERIMENT/${now:...}` 且
`hydra.job.chdir=false`：Hydra 配置与日志持久化到 `/storage1`，进程 cwd 仍保持
官方 `/opt/verl`，不会重新引入仓库旧版 verl 遮蔽问题。

作业 `2709139` 已验证上述 Hydra 修复并进入 verl 配置校验，随后发现旧 smoke
缩放参数自相矛盾：`train_batch_size=4` 小于 `ppo_mini_batch_size=16`。smoke 的
Questioner/Solver update batch 现均缩为 `4`；配置加载器会在提交前检查 update
batch 不大于 prompt batch 且能整除它。由于配置属于 run fingerprint，修复后的
作业使用新目录 `runs/rzero-qwen35-smoke-v2`，不会把旧 manifest 冒充成新配置的
结果。该作业中 vLLM 遥测线程还曾尝试写满额的 Home；运行入口现设置
`VLLM_NO_USAGE_STATS=1`，编译缓存仍留在节点本地 `/tmp`。

正式 profile 的 batch 映射按 Qwen3 实际五轮训练的有效更新语义审计：Questioner
使用 512 prompts、rollout `n=4`、`ppo_mini_batch_size=16`，因此每个 optimizer
mini-batch 为 64 trajectories、每个外层 batch 有 32 个 mini-batch；Solver
保持 512 prompts、`n=5`、`ppo_mini_batch_size=128`，即 640
trajectories/mini-batch。Questioner/Solver 分别消费 `global_step_5` 和
`global_step_15`。此次只改变正式 profile fingerprint；正在运行或已经产生状态的
`rzero-qwen35-smoke-v2` 使用独立 smoke 配置，不受影响。

2026-08-14 对 clean upstream 再审计后，纠正了上一段历史记录最初采用的错误
`ppo_mini_batch_size=4` 结论。实际五轮入口调用
`scripts/questioner_train_penalty.sh`，其 `worker.actor.global_batch_size=16`；旧
EasyR1 随后按 rollout `n=4` 展开为 64 trajectories/update。锁定的新 verl 也会
将 `ppo_mini_batch_size` 按 rollout `n` 展开，因此效果等价的新值必须为 16。
one-step profile 同步保持这一正式训练语义；轻量 smoke 因 prompt batch 仅为 4，
仍保留 mini-batch 4。正在 Compute1 运行的旧 one-step baseline 不应中断，也不得
在配置更新后用原 run directory 续跑；纠偏后的运行必须使用新的 run directory。

`smoke-v2` 作业 `2721258` 随后通过 batch-size 校验，在新版 verl 的 log-prob
配置校验处停止。该版本在关闭 dynamic batch 时要求 Reference policy 和 rollout
分别显式设置且只能设置新版 per-GPU 参数。训练适配器现为两者设置
`log_prob_micro_batch_size_per_gpu=1`；这只拆分 ref/rollout 的 log-prob 前向计算，
不改变 Questioner/Solver 的全局 optimizer mini-batch 或 trajectory 语义。失败发生
在 Ray/模型训练启动前，没有产生可复用的训练 checkpoint，同一 `smoke-v2`
目录可安全使用普通 `--resume`。

作业 `2729570` 已通过上述配置校验并启动 Ray，但 RIS/Pyxis 在 NVIDIA allocation
中同时传入 `CUDA_VISIBLE_DEVICES` 与 ROCm 兼容变量 `ROCR_VISIBLE_DEVICES`，触发
锁定 verl worker 的防歧义检查，两个 actor 在加载模型前退出。统一入口现保留
Slurm/Ray 所需的 `CUDA_VISIBLE_DEVICES`，在 Ray 初始化前移除不适用于 NVIDIA
运行的 `ROCR_VISIBLE_DEVICES` 和 `HIP_VISIBLE_DEVICES`；训练适配器对子进程再做
同样清理，避免绕过 `run.sh` 直接调用时复发。该修复不改变 run fingerprint、
GPU 分配或训练算法，同一 `smoke-v2` 目录继续普通 `--resume`。

2026-08-13 在 Compute1 的 4×A100 交互式节点上，`smoke-v2` 已通过
Qwen3.5/vLLM text-only environment smoke 并进入 Questioner FSDP2 初始化。
权重成功加载后，固定 verl commit 的 reward loop 因未注册旧 `batch` manager
而拒绝启动。随后实测确认 `trainer.use_v1=false` 虽切换到了官方 V0 TaskRunner，
但该 commit 的 V0/V1 已共同使用新的逐 trajectory reward loop；旧
`verl.workers.reward_manager.BatchRewardManager` 属于另一套 registry，因此单纯
切换 trainer 无法解决。不能将 Questioner 改成逐样本 `naive`，否则会破坏完整
rollout population 上的 BLEU 聚类奖励。

最终适配使用 verl 官方 `reward.reward_manager.source=importlib` 扩展点：新增的
`RZeroPopulationRewardManager` 在唯一 reward worker 内收齐
`train_batch_size * rollout.n` 个并发 trajectory，再调用未修改的 Challenger
`compute_score` 一次并按原顺序返回奖励。Questioner 因而仍在正式 profile 的
2048 trajectories（smoke 为 16）完整 population 上聚类；Solver 继续使用新
reward loop 的官方 `NaiveRewardManager`。两种 role 保留官方同步 V0 trainer，
用于已建立的 PPO/checkpoint 路径。失败发生在首个 optimizer step 之前，未产生
可复用 checkpoint。

随后 `smoke-v2` 已完成真实 rollout，并在 actor 的 `old_log_prob` 前向进入
Qwen3.5 full-attention 层；原先设置的 `use_remove_padding=false` 仍由默认
FlashAttention 2 进入 varlen kernel，但 padded Q/K/V 形状不一致，报
`shape ... is invalid`。固定 verl commit 的官方纯文本 Qwen3.5 27B/35B FSDP
recipes 均明确设置 `actor_rollout_ref.model.use_remove_padding=True`，而该 commit
的 `verl/models/transformers/qwen3_5.py` 已专门实现 packed Gated DeltaNet 的
`cu_seqlens`、分段 causal-conv 和 full-attention 传递。因此训练适配器改为
`use_remove_padding=true`，与官方纯文本 recipe 对齐；vLLM 仍保持
`language_model_only`，不启用图像/视频输入。原迁移计划中基于旧版支持状态作出的
“禁用 packed”假设已由官方代码和 A100 实测共同推翻。

下一处失败发生在 Questioner `old_log_prob`：真实 packed token 长度为 710，
但 RoPE 收到的轴长度为 32。这里的 32 正好是单 rank 的 8 条轨迹乘 Qwen3.5
的 4 个 M-RoPE 轴，说明纯文本 batch 被不必要地构造成 3-D jagged position
IDs 后，在 micro-batch 切分时发生布局转置。当前通过 verl 官方
`actor_rollout_ref.model.external_lib` 扩展点禁用未使用的多模态 processor，
仍使用模型自带 tokenizer；纯文本 position IDs 保持 1-D，并由 Qwen3.5
模型内部展开。同时显式设置 `trainer.balance_batch=false`，与锁定 commit 的
官方 Qwen3.5 FSDP recipe 一致。

## Compute1 交互式节点：固定路径与启动命令

Compute1 与 Compute2 看到的项目是同一份共享 storage，只是挂载路径
少了 `fs1`：

```text
Compute2: /storage1/fs1/jiaxinh/Active/jinyuan/R-Zero-Qwen3.5
Compute1: /storage1/jiaxinh/Active/jinyuan/R-Zero-Qwen3.5
container: /workspace/R-Zero
```

`/workspace/R-Zero` 是容器内挂载点，不是第二份代码。容器内写入
`/workspace/R-Zero/runs/...` 会直接落到 Compute1 主机的
`/storage1/jiaxinh/Active/jinyuan/R-Zero-Qwen3.5/runs/...`。代码、dataset、
checkpoint、manifest 和 stage log 继续保留在 storage；镜像、Enroot rootfs
和缓存使用 IB scratch。

Compute1 站点 `/etc/enroot/enroot.conf` 将 Pyxis 解压目录强制设为
`/scratch/enroot-data-user-UID`，而 2026-08-13 当时 `/scratch` 已 100% 满。
Pyxis 又会过滤 `ENROOT_DATA_PATH`，无法通过 `srun --export` 改到 IB
scratch。该节点也没有 `squashfuse`，因此不能用 `enroot start IMAGE.sqsh`
直接挂载。已验证的路线是：在 IB scratch 上执行一次 `enroot create`，
之后始终从持久容器目录启动。

每次新交互式 shell 先设置：

```bash
export PROJECT=/storage1/jiaxinh/Active/jinyuan/R-Zero-Qwen3.5
export IMAGE=/ib-scratch/jiaxinh01/project/rzero-runtime/images/rzero-qwen35-bdc8b2c29981.sqsh
export RUNTIME_ROOT=/ib-scratch/jiaxinh01/project/rzero-runtime
export HF_CACHE=$RUNTIME_ROOT/hf-cache
export CONTAINER=rzero-qwen35-bdc8b2c29981

export ENROOT_RUNTIME_PATH=$RUNTIME_ROOT/enroot-runtime/user-$(id -u)
export ENROOT_CACHE_PATH=$RUNTIME_ROOT/enroot-cache/user-$(id -u)
export ENROOT_DATA_PATH=$RUNTIME_ROOT/enroot-data/user-$(id -u)
export ENROOT_TEMP_PATH=$RUNTIME_ROOT/enroot-tmp/user-$(id -u)

mkdir -p \
  "$HF_CACHE" \
  "$ENROOT_RUNTIME_PATH" \
  "$ENROOT_CACHE_PATH" \
  "$ENROOT_DATA_PATH" \
  "$ENROOT_TEMP_PATH"
```

只在 `$ENROOT_DATA_PATH/$CONTAINER` 不存在时执行一次：

```bash
export ENROOT_MAX_PROCESSORS=32
enroot create --name "$CONTAINER" "$IMAGE"
```

已持有 4 GPU 的交互式 allocation 时，不再嵌套 `srun`，直接启动
`smoke-v2`：

```bash
enroot start \
  --root \
  --rw \
  --mount "$PROJECT:/workspace/R-Zero" \
  --mount "$HF_CACHE:/root/.cache/huggingface" \
  --env PYTHONPATH=/opt/verl:/workspace/R-Zero \
  --env HF_HOME=/root/.cache/huggingface \
  --env VLLM_NO_USAGE_STATS=1 \
  "$CONTAINER" \
  /bin/bash -lc '
    set -euo pipefail
    cd /opt/verl
    unset ROCR_VISIBLE_DEVICES HIP_VISIBLE_DEVICES

    exec bash /workspace/R-Zero/qwen35/scripts/run.sh \
      --run-dir /workspace/R-Zero/runs/rzero-qwen35-smoke-v2 \
      --config /workspace/R-Zero/qwen35/configs/a100_4x_qwen35_4b_base_smoke.yaml \
      --resume
  '
```

容器 rootfs 只需 `enroot create` 一次。之后更新共享 storage 中的
`qwen35/` 代码不需重建容器，因为运行时使用的是
`$PROJECT:/workspace/R-Zero` 挂载。但镜像中 `/opt/verl` 或 Python/CUDA/vLLM
依赖发生变化时，必须生成新镜像和新容器名，不得覆盖现有固定容器。

当前 terminal 只显示 stage 边界，详细日志在：

```text
$PROJECT/runs/rzero-qwen35-smoke-v2/logs/
$PROJECT/runs/rzero-qwen35-smoke-v2/round_01/logs/
```

例如：

```bash
tail -n 100 -F \
  "$PROJECT/runs/rzero-qwen35-smoke-v2/round_01/logs/questioner_train.log"
```

### Compute1 one-step 全链路与 Ray GPU 隔离

`one-step` 不是单一训练 stage，而是保留正式训练/奖励语义的一轮完整 R-Zero
集成运行；只缩小轮数、训练步数和候选题规模：

```bash
enroot start \
  --root \
  --rw \
  --mount "$PROJECT:/workspace/R-Zero" \
  --mount "$HF_CACHE:/root/.cache/huggingface" \
  --env PYTHONPATH=/opt/verl:/workspace/R-Zero \
  --env HF_HOME=/root/.cache/huggingface \
  --env VLLM_NO_USAGE_STATS=1 \
  "$CONTAINER" \
  /bin/bash -lc '
    set -euo pipefail
    cd /opt/verl
    unset ROCR_VISIBLE_DEVICES HIP_VISIBLE_DEVICES

    exec bash /workspace/R-Zero/qwen35/scripts/run.sh \
      --run-dir /workspace/R-Zero/runs/rzero-qwen35-one-step \
      --config /workspace/R-Zero/qwen35/configs/a100_4x_qwen35_4b_base_one_step.yaml \
      --resume
  '
```

2026-08-14 的一次运行在 Questioner FSDP2 加载阶段报
`Duplicate GPU detected: rank 0 and rank 1 both on CUDA device 1000`。这不是
reward、数据或 checkpoint 错误；两个 rank 在 NCCL 第一次 broadcast 前已映射到
同一块物理 A100。根因边界是此前的 reward concurrency 适配把 Ray
`worker_process_setup_hook` 安装到了整个 job，因而也会在 GPU worker 完成各自
accelerator visibility 分配前加载 verl/torch。兼容层随后曾尝试把 callable
setup hook 放入 CPU TaskRunner 的 actor-level `runtime_env`；Compute1 实测表明
当前 Ray 在 actor 创建时把该值直接走 JSON 序列化，报
`TypeError: Object of type function is not JSON serializable`，而且 actor runtime
env 还可能被 child actor 继承，因此该路线也已废弃。

最终实现完全不使用 setup-hook runtime env，而只包装官方 CPU TaskRunner actor
class 的 `run()`：进入该远端方法后安装 reward patch，再调用保存下来的官方
`run()`。FSDP worker 完全使用官方 Ray/verl GPU 分配路径。训练进程同时显式启动
新的单节点 local Ray runtime，并清除
`RAY_ADDRESS` 及所有会阻止 Ray 设置 `*_VISIBLE_DEVICES` 的
`RAY_EXPERIMENTAL_NOSET_*` 开关。

这项修复不改变 2+2 拓扑、Questioner/Solver batch、rollout、reward、训练步数或
run fingerprint。失败发生在 optimizer step 之前，所以更新代码后继续对同一个
`rzero-qwen35-one-step` 目录使用上述 `--resume` 命令；无需删除 dataset、模型或
run manifest，也不得设置 NCCL 的 duplicate-GPU 忽略开关。

## 固定资源和路径

```bash
export PROJECT=/storage1/fs1/jiaxinh/Active/jinyuan/R-Zero-Qwen3.5
export RUN_ROOT=$PROJECT/runs/rzero-qwen35
export HF_CACHE=/scratch2/fs1/jiaxinh/$USER/hf-cache
export RZERO_IMAGE=/scratch2/fs1/jiaxinh/$USER/images/rzero-qwen35-bdc8b2c29981.sqsh
```

用途约定：

- `/storage1/.../R-Zero-Qwen3.5/runs`：模型、dataset、checkpoint、manifest，持久化。
- `/scratch2/.../hf-cache`：Hugging Face 缓存，持久化共享。
- `/scratch2/.../images/*.sqsh`：正式 Pyxis 作业使用的固定容器镜像。
- `/scratch2/.../enroot-cache`：只供一次性裸 Enroot 导入作业使用。
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
Gated DeltaNet rollout decode kernel 首次编译；它与 FSDP actor/ref 是否使用
remove-padding 是两个不同执行路径。进程退出时的 EngineCore SIGTERM/cleanup
信息也不是 smoke 失败。

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

一次性导入脚本从构建 commit 对应的不可变镜像标签
`commit-81d554f1c4a871cc19387db929b1fad4a78cf170` 生成 scratch SquashFS；四卡
脚本只读取该本地文件，不再联系 GHCR。

拉取最新分支后先创建 Slurm 输出目录：

```bash
cd /storage1/fs1/jiaxinh/Active/jinyuan/R-Zero-Qwen3.5
mkdir -p runs/slurm-logs
```

首次运行或镜像文件缺失时，提交一次性导入作业：

```bash
sbatch qwen35/scripts/ris_prepare_image.sbatch
```

该作业运行在 `general-short`，不申请 GPU。它先写
`.partial-$SLURM_JOB_ID`，验证非空后再原子重命名；已有完整目标文件时幂等
跳过。完成后确认：

```bash
ls -lh /scratch2/fs1/jiaxinh/$USER/images/rzero-qwen35-bdc8b2c29981.sqsh
cat runs/slurm-logs/rzero-qwen35-image-JOB_ID.out
```

只有 `.sqsh` 存在且导入 job 成功后，才继续四卡 `--test-only` 和正式提交。

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
  --run-dir /workspace/R-Zero/runs/rzero-qwen35-smoke-v2 \
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
