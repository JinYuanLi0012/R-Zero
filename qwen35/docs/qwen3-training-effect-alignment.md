# Qwen3 → Qwen3.5 训练效果语义对齐审计

审计日期：2026-08-14。权威 Qwen3 基点为
`5699329d018d79535b7910abdedf5a6eebf355fd`，Qwen3.5 运行时的 verl commit 为
`4a2cba76f7f605d2b9f56e640faaeaa71c2c7f71`。

## P0 裁决：Questioner PPO mini-batch

原版五轮入口 `scripts/main.sh` 调用的是
`scripts/questioner_train_penalty.sh`。该脚本设置
`worker.actor.global_batch_size=16` 和 `worker.rollout.n=4`，而旧 EasyR1 的
`verl/workers/fsdp_workers.py` 会执行
`config.global_batch_size *= config.rollout.n`。因此原版每个 optimizer
mini-batch 实际包含 `16 × 4 = 64` trajectories；每个外层 batch 是
`512 × 4 = 2048` trajectories，共执行 `2048 / 64 = 32` 个 mini-batch。

锁定的新 verl 在 `ray_trainer.py` 中同样先把
`actor.ppo_mini_batch_size` 乘以 `rollout.n`。所以这个字段仍按 prompt 数填写：

- `ppo_mini_batch_size=4` 会得到 16 trajectories/update 和 128 mini-batches/step；
- `ppo_mini_batch_size=16` 才得到 64 trajectories/update 和 32 mini-batches/step。

结论：正式配置和 one-step profile 必须使用 16。此前使用 4 的结论来自对未被
五轮主流程采用的脚本及 batch 展开语义的误判。轻量 smoke 的 prompt batch 只有
4，因此继续使用 4，只用于集成验证而不声明训练效果等价。

## 参数矩阵

| 参数 | clean Qwen3 | 审计前 Qwen3.5 | 不可避免差异 | 当前目标 | 证据与风险 | 验证方式 |
|---|---:|---:|---|---:|---|---|
| Questioner prompt batch | 512 | 512 | 否 | 512 | 五轮入口继承默认 `rollout_batch_size` | 配置 invariant |
| Questioner rollout `n` | 4 | 4 | 否 | 4 | penalty 脚本直接设置 | 配置 invariant |
| Questioner PPO mini-batch（prompts） | 16 | 4 | 否 | **16** | 新旧 verl 都按 `n` 展开；4 会多做四倍 optimizer mini-batch | 效果等价回归测试 |
| Questioner trajectories/update | 64 | 16 | 否 | **64** | `ppo_mini × n` | 回归测试 |
| Questioner mini-batches/outer step | 32 | 128 | 否 | **32** | `prompt_batch / ppo_mini` | 回归测试 |
| Questioner update micro/GPU | 2 | 1 | 是，Qwen3.5 稳定性 | 先保留 1 | 锁定 verl 的 Qwen3.5 FSDP recipe 使用 1；只影响内存拆分 | 独立测试 1→2，记录峰值显存/吞吐 |
| ref/rollout log-prob micro/GPU | 8 | 1 | 是，Qwen3.5 稳定性 | 先保留 1 | 官方 Qwen3.5 FSDP recipe 使用 1；较小值可能增加前向开销 | 独立测试 1→2→4→8 |
| max response length | 4096 | 4096 | 否 | 4096 | penalty 脚本覆盖默认值 | 命令回归测试 |
| packed/remove-padding | true | true | 实现不同 | true | 锁定 verl 含 Qwen3.5 Gated DeltaNet packed 实现；服务器 padded 路径曾失败 | one-step + shape parity |
| actor torch compile | true | false | 是，Qwen3.5 稳定性 | 先保留 false | 官方 Qwen3.5 FSDP recipe 为 false；首次编译成本及稳定性风险 | 最后单独测试 false→true |
| dynamic batch | 旧版无等价开关 | false | 是 | false | 官方 Qwen3.5 recipe 为 false | 有官方新证据后才测试 |
| rollout eager | false | true | 否，但有兼容风险 | 待测 false | 原版和官方 Qwen3.5 GRPO recipe 均可用 false；CUDA Graph/Gated DeltaNet 需专项验证 | 单卡 load/generate 后 one-step A/B |
| rollout GPU memory utilization | 0.7 | 0.45 | 是，模型/运行时内存布局不同 | 先保留 0.45 | 官方 Qwen3.5 recipes 在 0.4–0.6；直接上 0.7 有 OOM 风险 | 0.45→0.6→0.7 逐级测试 |
| rollout tensor parallel | 2 | 1 | 拓扑相关 | 暂不改 | 不能脱离 2+2 Questioner/Solver 拓扑机械对齐 | 独立拓扑/吞吐验证 |
| 在线 Solver samples | 10 | 10 | 否 | 10 | Challenger 奖励采样语义 | reward service 测试 |
| Challenger population | 2048 | 2048 | 否 | 2048 | `512 × 4`，BLEU 聚类必须覆盖完整 population | population manager 测试 |
| Solver prompt/rollout/mini | 512 / 5 / 128 | 512 / 5 / 128 | 否 | 保持 | 640 trajectories/update；本次没有相反证据 | 配置及命令回归测试 |
| 下游 checkpoint | Q step 5 / S step 15 | 相同 | 否 | 保持 | 发布流程语义 | 配置与 pipeline 测试 |

## 性能验证顺序

当前 Compute1 one-step baseline 不应中断；它记录的是纠偏前
`ppo_mini_batch_size=4` 的基线。完成后收集生成、reward、old/ref log-prob、
actor update、checkpoint 各阶段耗时以及峰值显存。

纠偏后的运行必须使用新的 run directory，不能在旧 fingerprint 上 `--resume`。
先用 `ppo_mini_batch_size=16` 建立效果等价基线；随后每次只改变一个内存/执行参数：

1. ref/rollout log-prob micro：1 → 2 → 4 → 8；
2. actor update micro：1 → 2；
3. `enforce_eager`：true → false，先通过 Qwen3.5 Gated DeltaNet CUDA Graph smoke；
4. rollout memory utilization：0.45 → 0.6 → 0.7；
5. `torch_compile`：false → true，最后验证。

任一实验不得改变 prompt batch、rollout `n`、在线 Solver `n=10`、完整 reward
population 或 max response length。优化结果需同时记录吞吐、峰值显存、首步编译
开销、失败类型和输出/奖励 parity，才能进入正式配置。

## 源码证据

- [R-Zero 五轮入口](https://github.com/Chengsong-Huang/R-Zero/blob/5699329d018d79535b7910abdedf5a6eebf355fd/scripts/main.sh)
- [实际 Questioner penalty 训练脚本](https://github.com/Chengsong-Huang/R-Zero/blob/5699329d018d79535b7910abdedf5a6eebf355fd/scripts/questioner_train_penalty.sh)
- [旧 EasyR1 batch 按 rollout.n 展开](https://github.com/Chengsong-Huang/R-Zero/blob/5699329d018d79535b7910abdedf5a6eebf355fd/verl/workers/fsdp_workers.py)
- [锁定新 verl PPO batch 展开](https://github.com/verl-project/verl/blob/4a2cba76f7f605d2b9f56e640faaeaa71c2c7f71/verl/trainer/ppo/ray_trainer.py)
- [锁定 verl 的 Qwen3.5 FSDP GRPO recipe](https://github.com/verl-project/verl/blob/4a2cba76f7f605d2b9f56e640faaeaa71c2c7f71/examples/grpo_trainer/run_qwen3_5_27b_fsdp.sh)
- [锁定 verl 的 Qwen3.5-4B FSDP recipe](https://github.com/verl-project/verl/blob/4a2cba76f7f605d2b9f56e640faaeaa71c2c7f71/examples/on_policy_distillation_trainer/run_qwen3_5_4b_fsdp.sh)
