# 普通 R-Zero：逐轮原始出题与多数投票采样

本入口只做推理并保存分析数据。它不会调用训练、Hugging Face 上传、
validity gate 或 novelty，也不修改任何现有训练文件。

采样完成后，可用独立的 [API validity 入口](API_VALIDITY.md) 为全部 1000 条记录追加有效性标签，保留所有多数投票结果。

目标实验：`qwen3_4b_rzero_8k_5round`。
按原始 Phase-B 时序，Questioner r 的问题由尚未在本轮更新的 Solver r-1 标注：

| 分析轮次 | 出题模型 | 投票模型 |
|---|---|---|
| 1 | Questioner v1 / step 5 | Qwen/Qwen3-4B-Base |
| 2 | Questioner v2 / step 5 | Solver v1 / step 15 |
| 3 | Questioner v3 / step 5 | Solver v2 / step 15 |
| 4 | Questioner v4 / step 5 | Solver v3 / step 15 |
| 5 | Questioner v5 / step 5 | Solver v4 / step 15 |

所有训练模型路径都指向 `global_step_N/actor/huggingface`，不会加载 Solver v5。

## Linux 执行

将本目录安装到仓库的 `methods/rzero_raw_audit/` 后，在已有四卡资源的终端执行：

```bash
cd /storage1/jiaxinh/Active/jinyuan/R-zero
source env_rzero.sh

python -u -m methods.rzero_raw_audit.run \
  --storage /engrfs/project/jiaxinh/jinyuan/R-zero-storage \
  --experiment qwen3_4b_rzero_8k_5round \
  --rounds 1,2,3,4,5 \
  --per-round 200 \
  --gpu-ids 0,1,2,3 \
  --output-dir /engrfs/project/jiaxinh/jinyuan/R-zero-storage/analysis_results/qwen3_4b_rzero_8k_5round_raw200_v1
```

先查看计划可以加 `--plan-only`，不会启动 GPU 或创建文件。
中断后原命令加 `--resume`：保留已经完成的生成/投票分片，仅补未完成部分。
每个阶段默认最多运行 14400 秒，可用 `--timeout-seconds` 调整。
配置或代码协议变化会拒绝复用旧输出目录。重新采样应使用新目录。

四卡每卡各生成 50 次，seed 按原脚本设为 shard index 0/1/2/3。
每轮严格保存 200 条原始生成记录；重复保留，不补采、不去重。
若某条没有可解析的 question/boxed answer，仍保留原始输出并标记
`questioner_parse_failed`，不凭空制造一道题交给 Solver。因此可解析题数可能小于 200。

这批是已有 checkpoint 的新采样，不是当年被删除的 8000 条数据的恢复。
缩小 batch、改变软件/硬件环境都可能改变具体采样，即使种子相同。

## 与普通 R-Zero 一致的推理协议

- Questioner：原题目生成 system/user prompt，max_tokens=4096，temperature=1.0，top_p=0.95，n=1。
- Solver：原数学 system prompt，max_tokens=4096，temperature=1.0，top_p=1.0，top_k=40，n=9。
- prompt 使用各 checkpoint 自带 chat template；没有模板时用原脚本的 system/user 拼接。
- 多数投票使用原数学答案等价聚类：精确字符串与 `no ` 快捷比较，再双向 mathruler grading，单次 10 秒 timeout。
- `score` = 最大答案簇票数 / 非空解析答案数，而非固定除以 9。
- 平票按原代码选最先出现的答案簇代表。额外记录平票簇数。
- 原过滤条件只作标记：证明/box/text、score 不在 0.3–0.8、答案为空或 `None`。任何一项都不会删除本分析数据中的记录。

协议依据：原实验历史提交 `c61ebb1` 与当前 `3259270` 的普通分支。
本模块固化这些 prompt 与投票逻辑，CPU 测试直接比对现有源码中的 prompt 和聚类实现。

## 输出

```
manifest.json
round_1.jsonl
round_2.jsonl
round_3.jsonl
round_4.jsonl
round_5.jsonl
all_rounds.jsonl       # 1000 行，全部保留
summary.json
round_1/
  generate_shard_0.jsonl ... generate_shard_3.jsonl
  vote_shard_0.jsonl ... vote_shard_3.jsonl
... round_5/
```

每条记录包含：

- `id`、round/shard/index：按出现位置唯一标识，重复题不发生 ID 冲突。
- `questioner_model`、`solver_model`、种子。
- `questioner_raw`：未经裁剪的 Questioner 原始输出。
- `question`、`questioner_answer`、`questioner_parse_ok`。
- `solver_responses`：全部 9 条原始回答；`solver_answers`：9 个解析槽位，包括空解析。
- `majority_answer`、`majority_count`、`parsed_answer_count`、`answer_counts`、`score`。
- `majority_fraction_of_all_votes`：多数票数 / 9，便于与原版 score 对照。
- `vote_status`、`original_filter_reasons`、`would_pass_original_filter`。

原始生成分片永久保留，投票不会覆盖或删除它们。模型推理失败会中止该阶段，
不会写入不完整分片；单题 grading 异常保留原始回答及错误标记。

## 验证

```bash
python -m pytest -q methods/rzero_raw_audit/tests
```

本地 6 项 CPU 测试通过，包括原 prompt/聚类一致性、前一轮 Solver 配对、
解析分母、平票/timeout，以及完整 200 行（重复/失败/被过滤候选全部保留）和续跑测试。
本地未执行 GPU 采样；服务器 SSH 认证失败，实际数据需在服务器上运行得到。
