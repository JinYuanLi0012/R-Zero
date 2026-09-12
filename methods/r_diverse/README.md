# R-Diverse: minimal paper-described baseline

这是为后续论文比较准备的独立 R-Diverse 基线，不是作者官方代码，也不承诺复现论文数值。
算法基于 Chengsong-Huang/R-Zero (`5699329`)，按 arXiv:2602.13103v2 加入 SAM、MAP、30% 历史 replay。
不使用本仓库后续的 Validity、Terra、semantic-MC、novelty gate、domain、in-context、population 或 Q reset。
保留已有四卡工程约定及 Questioner actor global batch=4，不强求论文的八卡/128 配置。

## Linux 直接运行

在当前 R-Zero 环境中运行，不需要先跑 smoke。公开模型首次自动下载，缓存位置沿用 HF_HOME。

```bash
cd /storage1/jiaxinh/Active/jinyuan/R-zero
git fetch origin
git switch baseline/r-diverse
git pull --ff-only
source env_rzero.sh

bash methods/r_diverse/run.sh
```

默认配置：

- Q/S 从 `Qwen/Qwen3-4B-Base` 分别初始化；各自逐轮继承。
- Q 用 GPU0/1；奖励推理用 GPU2/3，Solver -> Coder -> Encoder 顺序进程。
- Phase-B 出题、标注与 SAM 使用四个单卡副本；Solver GRPO 使用四卡。
- 5 轮，每轮 Questioner 5 步、Solver 15 步，分别保留最后 checkpoint。
- 每卡生成 1000 次，四卡总计 4000；如已有 `SOLVER_GENERATE_SAMPLES` 则沿用该每卡数量。
- 每步 512 个 prompts；Q n=4、actor global batch=4；S n=5、actor global batch=128。
- 两端 LR=1e-6、weight decay=0.01、KL=0.01、temperature=1、top-p=0.99、GRPO unchanged。
- 4096 response tokens；单卡 inference context=8192、显存比例0.8。
- Coder 默认 **`Qwen/Qwen2.5-Coder-7B`（Base）**，temperature=0，max_new_tokens=2048。
- Encoder `jinaai/jina-code-embeddings-1.5b`，原始代码、无检索前缀、last-token pooling、L2 归一化、最多4096 tokens。
- 默认 W&B + console。只用 console：`--logger '["console"]'`。

可选新运行：

```bash
bash methods/r_diverse/run.sh \
  --run-name qwen3_4b_r_diverse_10000_v1 \
  --questions-per-gpu 2500
```

所有选项用 `bash methods/r_diverse/run.sh --help` 查看。`--gpu-ids 0,1,2,3` 的前两卡用于 Q，后两卡用于反馈。
模型已缓存时可加 `--local-files-only`；也可通过 `--base-model`、`--coder-model`、`--embedding-model` 指定本地路径。
采用 Base Coder 是对论文未写 Instruct 后缀的字面选择，不自动换模型；显式指定 Instruct 则算一个不同配置。

结果默认保存在：

```text
${STORAGE_PATH}/rzero_runs/qwen3_4b_r_diverse_minimal_v1/
  requested_config.json / config.json / provenance.json
  latest.json                         # 最新已完成轮次的 Q/S 路径
  sam_cache/                          # 每个 exact question 的代码和向量
  round_1/ ... round_5/
    questioner/attempt_1/train.log
    solver/attempt_1/train.log
    generated.json / labeled.json
    solver.parquet / mixed_rows.json / dataset_summary.json
    memory_rows.json / memory.npy
    reward_*/scores.json / questions.json
    state.json
```

主进程显示当前阶段和日志路径，训练细节进入 `train.log`/W&B。不存在自动 GPU smoke、自动 API judge、自动基准评测。
训练数据使用本地 Parquet，不必上传 Hugging Face。

恢复同一命令的已完成阶段，附加 `--resume`：

```bash
bash methods/r_diverse/run.sh --resume
```

必须保留原命令的全部参数。恢复会跳过完成阶段；未完成训练阶段从该轮输入模型重新训练，保留旧 attempt，
不承诺从某个训练 step 恢复。配置或方法代码改变则需要新 run name。初始化模型下载中断也可用同命令 `--resume`。

## 方法与最简单的未披露项选择

```text
q -> Qwen2.5-Coder -> <CODE> Python solver -> Jina -> unit embedding e

P_rep = cosine-distance average-linkage cluster size / current parseable batch size
P_MAP = 0.5 * max(max_history_cosine - 0.5, 0)
      + 0.5 * max(mean_history_cosine - 0.25, 0)
R_Q   = min(majority_score, 1 - majority_score) - P_rep - P_MAP
```

- 批内聚类保留上游 `average` linkage、distance threshold=0.5，距离由 BLEU 改为 `1-cosine`；
  这是论文未完整披露部分的简单实现，不改成 mean similarity、K-neighbor 或二值 gate。
- 第一轮历史为空，MAP=0、replay=0；之后每轮 Q reward 只读此前轮次 memory，不含当前候选的自匹配。
- Memory 收录正式 Phase-B 中通过原版过滤、且多数率在 `[0.3,0.8]` 的新题，保留伪标签及重复行。
  不收录 Phase-A 训练临时题，不把 replay 行再次插入 memory；不引入容量上限或淘汰策略。
- 相同文本只缓存一次 SAM 推理，但恢复原 multiplicity 后再算 batch cluster/history mean/replay。
- Replay 从所有历史行均匀抽样；数量 `floor(current_count * 0.3 / 0.7)`；历史不足时有放回抽样。
  直接使用历史伪标签，不重标注、不追加 verified answer。
- 完整 code prompt 按论文附录转录；不加 AST 改写、常数删除、实体分类或额外 prompt 修复。
  优先截取 `<CODE>` 内容，缺失标签则直接嵌入原输出；语法错误和长度截断记录但不 gate。
  空输出无法产生表示时清楚报错，不伪造零向量或 novelty 满分；没有额外 retry。
- 代码不执行；SAM 不判断数学有效性。论文中对 flawed input 推断合理含义的指令原样保留。
- Embedding 候选/历史采用完全相同的无前缀表示，无 query/document 不对称检索。
  不缩减1536维向量；mean 使用单位向量均值的点积，**均值不再归一化**；max 分块精确计算。
- 模型一次解析为 HF snapshot 路径，运行配置/方法哈希/代码缓存留存。推理固定引擎随机种子，
  不为每个相同 Questioner prompt 设同一个 SamplingParams seed（那会导致逐条复制）。

## 与原版 R-Zero 的关系

`train.yaml`、`questioner.jinja`、`solver.jinja`、`solver_reward.py` 来自上游 `5699329`，保留上游许可证。
`prompts.py` 的 Q messages 来自该提交的 question generator；训练中普通 Q/S prompt 分支与上游保持一致。
`gpu_worker.py` 将原服务/标注脚本的采样和投票搬入短生命周期 worker，去掉 HTTP、GPU idle 占用与全局临时文件。

- Q feedback：10 samples，temperature=1/top-p=1/top-k=40，多数分母包含空答案。
- Phase-B labels：9 samples，相同 decoding；去掉空答案后算多数比例。
- 答案等价沿用 mathruler、双向判断、原有 `no ` 字符串特例、10秒 grader timeout。
- Phase-B 原有 `证明`、question 含 `box`、answer 含 `text` 排除规则保留。
- Q 输出缺失 question/box 时设 reward=-1；不送 SAM、不参与簇分母。这是简单的格式失败处理。
- 修正上游 Q parser 对已提取答案字符串再 `[-1]` 的切字问题：保留完整 boxed 内容；
  Q 自报答案仅用于非空格式检查，不用于奖励正确性或 Solver 标签。
- Solver reward 保留上游 `0.9 * answer-match + 0.1 * format`，而非额外 judge。
- Dummy Parquet 只提供固定 Q prompt 的行数，不向模型注入人工题目、答案或领域。
- `train.py` 复用普通 EasyR1/FSDP/GRPO，并禁用额外 validation reward 调用；5/15步结束后直接保存与 merge。
  本目录不调用 `scripts/main.sh` 或 `methods/validity_rzero`。入口清除旧研究环境变量，强制 validity disabled。

## 依赖与四卡运行

沿用现有 `env_rzero.sh` 的 vLLM、PyTorch、Transformers、mathruler、stopit、datasets、numpy、sklearn。
Encoder 使用 Transformers 原生 Qwen2 模型 + last-token pooling，不需要 Jina API 或 sentence-transformers。
不自动升级现有训练环境。若旧环境不能加载 Jina，可将兼容的独立 Python 路径放到
`RDIVERSE_SAM_PYTHON`，只用于 Coder/Encoder 子进程；该环境也需 vLLM/Transformers/numpy。

Q reward 每步依次启动并退出 Solver、Coder、Encoder 进程，释放GPU后才进入下一推理模型。
仅GPU2/3做这些工作，不抢占GPU0/1，也不需要改训练器的语义屏障。
这比常驻服务朴素，模型重载开销较大；目标是清楚、独立、能实施的四卡基线，不追求作者吞吐。
每个 worker 有独立 input/output/log，失败时保留，主异常带日志尾部。

## 评测

训练后用与其他基线相同的评测流程。现有七数学任务脚本可这样调用（它可能使用现有 API recheck 配置）：

```bash
RUN_ROOT="$STORAGE_PATH/rzero_runs/qwen3_4b_r_diverse_minimal_v1"
MODEL_PATH=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["solver"])' "$RUN_ROOT/latest.json")
export EVAL_ARTIFACT_DIR="$RUN_ROOT/evaluation_final"
export EVAL_GPU_IDS=0,1,2,3
bash evaluation/evaluate.bash "$MODEL_PATH"
```

各轮 `round_N/state.json` 也记录 solver 路径，可逐轮评测。不要把这份最小实现的结果标为作者官方结果；
建议论文描述为 “our implementation of R-Diverse based on the published method, with four-GPU engineering adaptations”。

## 本地 CPU 检查

```bash
python3 -m unittest discover -s methods/r_diverse/tests -v
```

仅检查 MAP、聚类、replay、过滤、四卡参数和环境隔离，不启动任何 GPU。
