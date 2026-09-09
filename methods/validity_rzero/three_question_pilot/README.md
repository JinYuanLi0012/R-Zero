# Frozen Novelty K8 Q4 + S3: three questions per request

独立推理和数据过滤实验。使用已有 Q4 与 S3，不训练模型、不运行 Questioner reward、不调用 novelty/semantic judge，也不上传 Hugging Face。所有新代码均在本目录，现有各版 R-Zero 入口不变。

## 固定协议

- 原始生成预算：4 卡 × 2500 次 × 1 题 = 10000 题。
- 本实验：4 卡 × **833 次 × 最多 3 题 = 9996 题**。不补足解析失败，不去重。
- Q4 默认解析到 `global_step_5/actor/huggingface`；S3 默认解析到 `global_step_15/actor/huggingface`。也可以直接传入已 merge 的 HF 目录。缺失时明确报错，绝不自动挑选 latest checkpoint。
- 出题 prompt 从原始 `question_generate/question_generate.py` 中读取，仅四处最小文字替换：设计三个题、每个题可来自任意数学领域、按顺序输出三对题目/答案块、用户请求三个题。没有增加“必须不同”、topic、CoT 或历史参考要求。
- 每次 completion 形式为 `<question>...</question>\boxed{...}` 连续三次。保留前三个 opening tag 对应的完整题块；若只有一或两道完整题则全部保留。缺失前题答案不会借用后题答案；第 4 题及以后忽略并记录。
- Q 生成与原流程相同：`temperature=1.0, top_p=0.95, max_tokens=4096, n=1, EOS stop`；每卡 vLLM seed 为 shard index 0/1/2/3。**4096 仍是整次调用的上限，没有扩大到 12288**。截断请求数另行记录。
- 四卡生成全部结束、进程退出后，四卡加载同一 S3，各自评分本卡题目。
- S3 每题只看到该题自身，先 9 次 validity；至少 5 票 INVALID 淘汰。通过的题再独立 9 次纯数学作答；两阶段均沿用 `max_tokens=4096, temperature=1.0, top_p=1.0, top_k=40`。
- 原数学答案提取、空答案处理、等价聚类、多数率分母、特殊题跳过规则不变；最终复用 `passes_rzero_filter`，保留非 INVALID、非空答案、score 在 **[0.3, 0.8]** 的题。
- 比较分布的产物是 **R-Zero-only** 保留集，不混入 Terra replay。原正式 Solver 训练会在此后混入 Terra；本实验停在此前，不进行训练或上传。比较原 S4 训练集时应排除 `source=terra`，或使用原 K8 v4 的过滤后题集。

## Linux 运行

```bash
cd /storage1/jiaxinh/Active/jinyuan/R-zero
git pull --ff-only
source env_rzero.sh

bash methods/validity_rzero/three_question_pilot/run.sh
```

默认模型根目录就是本次指定的：

```text
/engrfs/project/jiaxinh/jinyuan/R-zero-storage/models/qwen3_4b_validity_rzero_semantic_novelty_gate_k8_4gpu_v1_questioner_v4
/engrfs/project/jiaxinh/jinyuan/R-zero-storage/models/qwen3_4b_validity_rzero_semantic_novelty_gate_k8_4gpu_v1_solver_v3
```

默认输出：

```text
/engrfs/project/jiaxinh/jinyuan/R-zero-storage/rzero_runs/novelty_k8_q4_s3_three_questions_v1
```

配置、模型身份与代码 hash 写入 manifest。父 shell 残留的 domain、novelty、Terra 环境变量不会改变子进程的协议；`STORAGE_PATH` 在子进程中重定向至本实验私有 workspace，评分器只能删除其中的暂存副本。

先查看 prompt 和协议（不加载模型，不写文件）：

```bash
bash methods/validity_rzero/three_question_pilot/run.sh --dry-run
```

可选四卡小规模 smoke（每卡 2 次，最多 24 题，使用独立目录）：

```bash
bash methods/validity_rzero/three_question_pilot/run.sh \
  --requests-per-gpu 2 \
  --output-dir /engrfs/project/jiaxinh/jinyuan/R-zero-storage/rzero_runs/novelty_k8_q4_s3_three_questions_smoke
```

失败后恢复相同实验：

```bash
bash methods/validity_rzero/three_question_pilot/run.sh --resume
```

按 shard 验证产物 hash，跳过已完成的生成/评分；失败 shard 从该阶段重跑。输入副本即使被原评分器删除，也能从永久 candidates 重新生成。更换模型、代码、环境包版本或参数时拒绝混用结果。默认评分超时 14400 秒，可在新运行开始前用 `--eval-timeout-seconds` 指定。失败日志保留，父进程收到错误或中断时终止本次启动的进程组。

## 产物

| 文件 | 含义 |
|---|---|
| `manifest.json` | 实际 HF checkpoint、文件身份、源码 hash、包版本、prompt 和参数 |
| `generation/shard_N_prompt.json` | 原始 messages 与实际渲染 prompt |
| `generation/shard_N_raw.jsonl` | 所有请求原始 completion、长度、finish reason、解析状态 |
| `generation/shard_N_candidates.json` | 每卡所有完整题块，永久保留 |
| `datasets/candidates.jsonl` | 合并后的未过滤题集 |
| `datasets/round_4_phase_b.jsonl` | 原评分器返回的全部题目与 votes、score、是否通过过滤 |
| `datasets/evaluator_skipped.jsonl` | 原评分器省略的题目 ID；具体原因查日志，未改变原跳过行为 |
| `datasets/round_4.json` | 最终 R-Zero-only 保留集，可对照原 v4 |
| `datasets/solver_train_rzero.jsonl` | 同一保留集转换成 problem/answer/source 格式，保留位置 ID |
| `summary.json`, `report.md` | 总量、解析/截断计数、第 1/2/3 题和合并集的文本分布指标 |
| `logs/generate_N.log`, `logs/evaluate_N.log` | 每卡独立日志 |
| `_SUCCESS.json` | 全流程完成标记 |

所有题目的 `sample_id/request_id/question_position/shard/request_index` 都会保留。原始同题多次出现不会被合并。生成时 Questioner 的答案另存为 `questioner_answer`，最终训练答案仍来自 S3 多数投票。

数字归一化模板只是轻量文本指标，不等同于解法/语义多样性，也未冒充之前 TF-IDF 全量分析的口径。不同位置样本数可能不同，比较历史数据时需要控制样本数；不要直接用总 unique 数判定胜负。

## 评分一致性与本地验证

`evaluate_snapshot.py` 是 `b2e2d24` 的生产 `question_evaluate/evaluate.py` 快照，仅在两处结果 append 前增加 provenance 字段透传。打分、prompt、sampling、过滤与异常分支不变；绝对路径的 validity prompt 由入口显式指定。保留快照是为避免改动共享评分器，以及在 duplicate/skip 场景下准确保留题目位置。

CPU 测试会删除这两行透传、统一行尾空白后与原文件逐字比较，并用假的推理依赖执行真实评分器控制流，验证 validity gate、九样本多数投票、原始跳过规则和重复题 provenance。测试不代表真实 GPU smoke。

```bash
python -m unittest methods.validity_rzero.three_question_pilot.test_protocol -v
```

## 用已生成数据训练 Solver（独立 S4 分支）

```bash
cd /storage1/jiaxinh/Active/jinyuan/R-zero
git pull --ff-only
source env_rzero.sh
bash methods/validity_rzero/three_question_pilot/train_solver.sh
```

默认读取原实验 Linux 输出目录的 `datasets/round_4.json` 和
`datasets/round_4_phase_b.jsonl`，校验两者一致；不会再次出题、打分或去重。
使用保留行的 Solver 多数投票 `answer`，不使用 `questioner_answer`。
复用 `build_mixed_rows`，同一 Terra 数据集、default config、10% 比例和 seed=1。
当前 5633 条 R-Zero 配 625 条 Terra，总计 6258 条。
数据上传到 `$HUGGINGFACENAME/novelty_k8_q4_s3_three_questions_v1_solver_v4`
（私有仓库；未设置 namespace 时默认 jinyuan222）。需要原环境的 HF 上传凭据。

训练直接调用原 `scripts/solver_train.sh` 的 `SOLVER_DATASET_READY=1` 路径。
初始模型为原 S3 的 `global_step_15/actor/huggingface`，显式对齐
`scripts/main.sh` 的 Solver 设置：4 卡、15 steps、rollout batch 512、
4096 response tokens、100 epochs 上限、val_freq=4、save_freq=1、save_limit=1。
其余算法、学习率、KL、采样设置和 source 专用 prompt/reward 均来自原训练脚本及
`examples/config.yaml`，未修改。继承的 SOLVER_* 覆盖会清除，避免污染实验。
数据较少会改变跨 epoch 后的重复采样比例；训练步数和 batch 大小保持一致。

像原 validity 主流程一样，训练后合并 step15 模型，不自动执行最终 benchmark。
输出模型：
`/engrfs/project/jiaxinh/jinyuan/R-zero-storage/models/novelty_k8_q4_s3_three_questions_v1_solver_v4/global_step_15/actor/huggingface`

receipt、混合数据副本、启动配置和日志独立保存在：
`/engrfs/project/jiaxinh/jinyuan/R-zero-storage/rzero_runs/novelty_k8_q4_s3_three_questions_v1_solver_v4/`

可选命令：

```bash
# 只检查输入并打印参数；不上传、不加载模型、不启动 GPU
bash methods/validity_rzero/three_question_pilot/train_solver.sh --dry-run
# 数据目录不同则指定实际包含 round_4.json 的目录
bash methods/validity_rzero/three_question_pilot/train_solver.sh --data-dir /path/to/datasets
# 只混合并上传，之后不带该选项启动时会复用匹配的 receipt
bash methods/validity_rzero/three_question_pilot/train_solver.sh --prepare-only
```

已有模型输出目录时拒绝重训覆盖；本入口不提供自动断点续训。
训练中断后应按实际 checkpoint 单独恢复，不能删除目录后盲目重启。
评测时对新模型复用原 S4 的评测命令、任务及 recheck 配置。

本地验证：`python3 -m unittest methods.validity_rzero.three_question_pilot.test_train_solver methods.validity_rzero.three_question_pilot.test_protocol`。
GPU 训练和 HF 上传需在 Linux 环境执行，Mac 测试不会执行这两步。
