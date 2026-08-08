# R-Zero Qwen3.5-4B-Base 独立迁移实施方案

## 仓库隔离与安全边界

- 迁移分支基于干净上游提交 `5699329d018d79535b7910abdedf5a6eebf355fd`。
- 分支名为 `feature/qwen3.5-4b-base`。
- 原始 R-Zero 文件保持不变；实现仅新增 `qwen35/` 与本计划文件。
- 不引入 Gaussian/task-vector 算法扩展，只复用通用的 manifest、原子提交和断点校验思想。
- 完成时通过 `git diff upstream/main` 审计原始文件零修改。

当前执行环境不允许写原仓库的 `.git`，因此使用独立本地 clone 代替 `git worktree`。该 clone 的 `origin` 和 `upstream` 分别指向用户 fork 与原始上游，分支和提交结构与计划一致，且不会接触用户现有脏工作树。

## 目录结构

```text
qwen35/
├── README.md
├── configs/
├── environment/
├── rzero/
│   ├── rewards/
│   ├── pipeline/
│   └── validation/
├── scripts/
└── tests/
```

- `qwen35/README.md` 记录安装、4×A100 拓扑、正式/恢复运行、产物结构和兼容边界。
- 不复制整个仓库，只迁移必须调整的 Prompt、奖励、生成和筛选逻辑，并用 parity tests 固定行为。

## Qwen3.5 官方底座

- 模型固定为 `Qwen/Qwen3.5-4B-Base`，正式运行前解析并锁定 Hugging Face revision。
- 使用上游 verl、Python 3.12、FSDP2 和配套 vLLM，不修改仓库内旧版 verl。
- 2026-08-08 RIS 单卡 smoke 证明原定 `verl v0.8.0` 安装器固定的
  vLLM 0.11 不支持 `language_model_only`，故正式运行时底座修订为官方
  `verlai/verl:vllm024.dev2`（锁定 digest），并锁定已包含 Qwen3.5 FSDP2
  recipes 的 verl main commit。最终矩阵为 CUDA 13.0.2、Torch 2.11.0、
  vLLM 0.24.0、Transformers 5.5.3；RIS 580.105.08 驱动满足 CUDA 13.0。
- 使用 verl 官方安装和 checkpoint/merger 接口，记录依赖锁、verl commit、模型 revision 和容器 digest。
- 仅启用文本路径：vLLM 使用 `language-model-only`，沿用官方 tokenizer/chat template，禁用 packed/remove-padding 路径。
- XDG、Triton、TorchInductor、CUDA、vLLM 和 FlashInfer 编译缓存统一写入
  计算节点本地临时目录；模型、数据、checkpoint 和 manifest 仍写入持久化
  run directory，禁止大缓存占用配额较小的 Home。
- Challenger 接入 verl 官方 batch reward manager；Solver 接入官方逐样本 reward manager。

## R-Zero 算法与五轮流程

- 保持发布代码语义：五轮交替训练、`m=9`、难度区间 `0.3–0.8`、Questioner step 5、Solver step 15，以及原有 Prompt/奖励/数学验证行为。
- 每轮依次执行 Questioner GRPO、Questioner 导出、4×2000 候选生成、Solver 投票、合并筛选、Solver GRPO、Solver 导出和固定评测。
- Questioner 阶段使用 2 张训练卡和 2 张冻结 Solver 服务卡；Solver 训练使用全部 4 张 A100。
- 本地 Parquet 是权威训练输入，Hugging Face 上传是可选幂等发布动作。

## 运行与恢复接口

```bash
qwen35/scripts/run.sh \
  --run-dir /path/to/run \
  --config qwen35/configs/a100_4x_qwen35_4b_base.yaml \
  --resume
```

- 支持 `--resume`、`--from-stage`、`--dry-run` 和 `--round`。
- Run fingerprint 固定模型 revision、verl commit、依赖锁、算法参数、输入哈希和随机种子；不一致时拒绝续跑。
- verl 每步保存完整 checkpoint，滚动保留最近两份；失败发生在 step 3 内部时从完整 step 2 重跑 step 3。
- 生成/评估按 shard 独立提交，所有 stage 经验证后原子提交 manifest，不提前删除输入。

## 实施顺序

1. Plan 独立提交。
2. 新增环境锁、配置 schema 和 Qwen3.5/verl smoke tests。
3. 迁移奖励、Prompt、生成/筛选逻辑并完成 parity tests。
4. 接入 Questioner/Solver 的 verl FSDP2 GRPO、checkpoint 和导出。
5. 实现五轮 manifest pipeline、shard 恢复和故障注入测试。
6. 完成缩小版 Round 0、正式配置、文档和零侵入审计。

## 验收

- Qwen3.5 能由 Transformers、vLLM text-only 和 verl FSDP2 正确加载。
- 固定样本下新旧奖励、分组、验证和筛选结果一致。
- 训练、生成、评估、合并、导出和上传中断后可幂等恢复。
- 每轮登记 8000 道原始候选题，五轮模型、数据和 manifest 均可独立追溯。
- `git diff 5699329d018d79535b7910abdedf5a6eebf355fd` 只包含新增的 `docs/plans/` 和 `qwen35/` 文件。
