# Compute1：用本地 Qwen3-32B 复核数学评估

工作方式仍是 Mac 修改和测试 → 推送 GitHub main → 在 Compute1 拉取运行。
本功能不改变训练或 frozen semantic judge。默认 `RECHECK_BACKEND=api` 保留旧 API 路径；
只有显式选择 `local` 才使用新功能。

## 1. 更新代码和环境

在 Compute1 的四卡 A100 80GB GPU allocation 内运行。先查看工作区状态，保留服务器上的本地修改。
如果 fast-forward pull 因修改冲突而拒绝，先处理具体冲突，不要 reset 或覆盖文件。

```bash
cd /storage1/jiaxinh/Active/jinyuan/R-zero
git status --short
git pull --ff-only origin main

conda activate /ib-scratch/jiaxinh01/project/envs/rzero-py310
export STORAGE_PATH=/engrfs/project/jiaxinh/jinyuan/R-zero-storage
export HF_HOME="$STORAGE_PATH/cache/huggingface"
export HF_HUB_CACHE="$HF_HOME/hub"

python -c 'import vllm, transformers, requests; print("vllm", vllm.__version__, "transformers", transformers.__version__)'
```

需要支持 Qwen3 及请求级 `chat_template_kwargs` 的 vLLM。Qwen 官方说明的最低版本为
vLLM 0.8.5、Transformers 4.51.0；实际 GPU/CUDA 兼容性需要在 Compute1 验证。
仓库 requirements.txt 当前固定 vLLM 0.9.1、Transformers 4.52.4，版本号满足上述要求；
已核对 [vLLM 0.9.1 文档](https://docs.vllm.ai/en/v0.9.1/serving/openai_compatible_server.html)支持请求级 chat_template_kwargs。
不需要 openai Python SDK，也不需要有效 OpenAI key。
不要为了部署 judge 直接升级正在训练使用的环境；如果使用独立 judge 环境，设置
`RECHECK_LOCAL_PYTHON=/你的/judge环境/bin/python`，仅 vLLM 服务会用该解释器。

模型默认 `Qwen/Qwen3-32B`，首次启动会通过 Hugging Face 下载约 66GB BF16 权重到模型缓存。
也可以把 `RECHECK_LOCAL_MODEL` 指向已下载的完整模型目录。
如果计算节点不能联网，请事先在可联网节点下载到上述共享缓存；已缓存时可以设置 `HF_HUB_OFFLINE=1`。
固定版本实验可使用 `RECHECK_LOCAL_REVISION` 指定 Hugging Face commit，并保持模型目录内容不变。

## 2. 完整评估：生成后自动启动本地 judge

### 任意 N 个模型：传路径即可

激活环境并设置 `STORAGE_PATH` 后，可以用通用入口代替手写循环：

```bash
python evaluation/evaluate_models.py /模型目录1 /模型目录2 /模型目录3
```

每个参数可以是包含 `config.json` 的 merged checkpoint 目录，也可以是模型运行目录；
后一种自动补上 `global_step_15/actor/huggingface`。路径不固定组名和轮数，按参数顺序运行。
非 step15 checkpoint 请直接传完整 merged 目录。启动前检查所有 config，重复模型路径会报错。

你当前的 K16/min1 四轮可执行：

```bash
python evaluation/evaluate_models.py \
  /storage1/jiaxinh/Active/jinyuan/R-zero-storage/models/qwen3_4b_validity_rzero_semantic_novelty_gate_k16_min1_4gpu_v1_solver_v{1,2,3,4}
```

可以先在命令中加入 `--dry-run`，只检查路径而不启动评估。
默认使用 GPU `0,1,2,3`（已设置 CUDA_VISIBLE_DEVICES 时沿用它），可用 `--gpu-ids 0,1,2,3` 指定。
每个模型先生成全部七项数学评测，再启动 Qwen3-32B 本地 judge，结束后释放 judge，再处理下一个。
入口固定 local backend、Qwen3-32B、关闭 thinking、max_tokens=32、并发 8；
支持沿用 `RECHECK_LOCAL_REVISION` 固定版本，避免旧 API 配置和 EVAL_TASKS 改变本批次范围。

### 数学复核 prompt 模式

默认 `--judge-prompt-mode corrected`，保留现有正确的答案角色映射。批量入口不受旧的
`RECHECK_JUDGE_PROMPT_MODE` 环境变量影响，切换模式必须显式传参数：

```bash
python evaluation/evaluate_models.py --suite math --gpu-ids 0,1,2,3 \
  --judge-prompt-mode rzero-original /模型目录1 /模型目录2
```

`rzero-original` 的 system/user 消息逐字来自上游固定提交
[`5699329d018d79535b7910abdedf5a6eebf355fd`](https://github.com/Chengsong-Huang/R-Zero/blob/5699329d018d79535b7910abdedf5a6eebf355fd/evaluation/results_recheck.py)。
上游调用 `process_example(results[i]['answer'], results[i]['response'])`，对应 prompt 原文：

```text
Hi, there is a answer: {answer}

, and the ground truth answer is: {response}

, please check whether the answer is correct or not, and return the **only** Yes or No.
```

这里 `{answer}` 是 benchmark 标准答案，`{response}` 是 solver 输出；原始模式有意保留这一反转映射。
这只是复用上游 **prompt**，不是完整复现论文评估设置：本地仍用 Qwen3-32B、temperature=0、
thinking=False、max_tokens=32，上游脚本使用 GPT-4o、temperature=0.1。

结果中的 `recheck.prompt_mode` 和 `recheck.prompt_version` 标识评分模式；原始模式还记录源提交与链接。
终端和 `summary.md` 显示模式及版本，checkpoint 旁的结果和 `evaluation.json` 同样保留这些信息。
两种模式使用不同批次目录；混合模式记录被判为无效，不参与平均；禁止跨模式追加或覆盖结果。
`--summary-only` 使用原 manifest 中的模式，不能通过新参数改写已有分数的模式。

仅复核已有基础输出时，`run_local_recheck.py`、`results_recheck.py`、`recheck_resume.py`
也接受 `--judge-prompt-mode`，这些底层入口可用 `RECHECK_JUDGE_PROMPT_MODE` 传递模式。
切换时必须指定新的输出文件；续跑只复用匹配 judge 元数据的结果，旧版 local-v1 元数据视为 corrected。
非数学 `--suite nonmath` 不使用该模式参数，原有三卡评估调度不变。

三张 GPU 并发非数学评估时，可设置 `export RZERO_NONMATH_VLLM_PORT_BASE=31000`，
分别向 SuperGPQA、BBEH、MMLU-Pro 子进程传入 `VLLM_PORT=31000,31256,31512`，
避免它们继承同一个端口。仅在设置该变量时启用；数学评估和其他 GPU 数量的调度不变。
这不会检测端口是否被其他任务占用，基准端口需按节点使用情况选择。


模型路径可以在 `/storage1`，而 `STORAGE_PATH` 仍指向 `/engrfs`：后者控制基础生成结果和默认批次输出位置，
不会被用来拼接或替换你传入的 checkpoint 路径。也可显式使用 `--storage-path /结果存储根目录`。

默认每次创建新的 `$STORAGE_PATH/evaluation_batches/math_qwen3_32b_模式_时间戳`；
`--batch-dir /全新目录` 可以指定位置，拒绝覆盖已有批次。
终端会打印批次目录，每完成一个模型更新 `summary.csv` 和 `summary.md`，最后自动打印整张表：

`id | name | status | math | gsm8k | amc | minerva | olympiad | aime2024 | aime2025 | ave`

CSV 另含完整模型路径和结果文件路径。`ave` 是七项百分比分数的简单平均，不是官方综合指标；
只有模型成功且七项记录完整时才计算。失败、缺失项留空，并标明状态。
每个模型的详细结果和日志保存在批次的 `001/`、`002/` 等子目录，不会覆盖同名模型的汇总。
原有基础逐题输出仍在 `STORAGE_PATH/evaluation` 下；重新完整评估同一个 checkpoint 会更新其基础输出。

每个模型成功完成七项评估后，还会自动在**实际 merged checkpoint 目录**内保存独立副本：

```text
global_step_15/actor/huggingface/evaluations/<批次名>_<模型序号>/
  final_results.jsonl
  summary.csv
  summary.md
  evaluation.json
```

这里仅保存该 checkpoint 的七项最终分数、单模型汇总和来源信息。
`evaluation.json` 记录 judge 配置、批次目录、原结果/日志路径及基础逐题结果位置。
不是符号链接，因此即使集中汇总目录不可访问，仍可在 checkpoint 旁查看这份分数。
大体积逐题文件与日志继续留在 STORAGE_PATH，不重复复制。
checkpoint 在 storage 就存 storage，在 engr 就存 engr；参数是模型根目录或完整 merged 路径时，
副本都会归到同一个实际 merged checkpoint 目录，避免不同 step 混淆。
失败/不完整结果不会发布为成功副本；遇到副本目录无写权限时会报错，中央结果保留。
批次名和模型序号用于分隔不同评估；若同名目录属于其他批次则报错，不覆盖它。

已运行完的旧批次可以补写 checkpoint 副本，无需重新评估：

```bash
python evaluation/evaluate_models.py --summary-only /已有批次目录 --copy-to-checkpoints
```

任一模型失败时停止后续模型，保留已有结果。此入口不自动恢复旧批次；
需要恢复时可使用前文 `run_local_recheck.py --models_file` 仅复核已有基础结果，
或向本入口只传尚需评估的模型路径开始新批次。保持前台会话及 GPU allocation 有效。

重新打印或刷新任意批次的汇总（不需要 GPU）：

```bash
python evaluation/evaluate_models.py --summary-only /上面打印的批次目录
```

### 单个模型的原有命令

将 MODEL 改为目标 solver 的 huggingface 目录，然后执行：

```bash
MODEL="$STORAGE_PATH/models/qwen3_4b_validity_rzero_semantic_novelty_gate_k16_min2_4gpu_v1_solver_v1/global_step_15/actor/huggingface"
test -s "$MODEL/config.json" || exit 1
RUN="${MODEL%/global_step_15/actor/huggingface}"
TAG="rzero_math_qwen3_32b_$(date +%Y%m%d_%H%M%S)"

export RECHECK_BACKEND=local
export RECHECK_LOCAL_MODEL=Qwen/Qwen3-32B
export RECHECK_GPU_IDS=0,1,2,3
export RECHECK_TENSOR_PARALLEL_SIZE=4
export RECHECK_CONCURRENCY=8
export RECHECK_MAX_COMPLETION_TOKENS=32

EVAL_GPU_IDS=0,1,2,3 \
EVAL_TENSOR_PARALLEL_SIZE=1 \
EVAL_MATH_ONLY=1 \
EVAL_ARTIFACT_DIR="$RUN/evaluations/$TAG" \
EVAL_LOG_DIR="$RUN/logs/$TAG" \
FINAL_RESULTS_FILE="$RUN/evaluations/$TAG/final_results.jsonl" \
EVAL_RUN_ID="solver_v1_$TAG" \
bash evaluation/evaluate.bash "$MODEL"
```

四卡编号是 allocation 内可见编号；有特殊 CUDA_VISIBLE_DEVICES 映射时相应调整。
同一时间这四张卡需要可供本次评估使用。流程是：

1. 原有 solver workers 生成七个数学数据集的回答并本地评分。
2. 等待这些 workers 全部退出，再启动一个 TP=4 的 BF16 Qwen3-32B judge。
3. 本机随机端口、只监听 127.0.0.1、每次运行独立服务名称和临时访问 key；验证服务就绪后复核。
4. 所有复核请求带 `chat_template_kwargs={"enable_thinking": false}`、`temperature=0` 和 `max_tokens=32`。
5. 仅复核本地 score < 0.5 的题；写出汇总后终止本次创建的 judge 进程组并释放 GPU。

`EVAL_MATH_ONLY=1` 仍包含本地复核，只跳过 SuperGPQA/BBEH/MMLU-Pro。
`EVAL_TASKS=math,gsm8k` 可仅生成及复核所选数学数据集。
旧的 `RECHECK_JUDGE_MODEL=gpt-...`、`RECHECK_REASONING_EFFORT=none` 不控制本地 judge。
`RECHECK_MAX_COMPLETION_TOKENS` 在本地模式也会生效；原来的 8 可覆盖新默认 32，建议显式设为 32。

完整生成阶段仍保留原有对 tokens.json 的读取（例如既有项目认证配置）；
**本地 judge 不读取其中的 openai 字段，也不读取 OPENAI_API_KEY/OPENAI_BASE_URL**。
无需修改或删除任何旧密钥文件。

## 3. 已有生成结果：仅重新复核，不重新跑 solver

输入沿用原路径：`$STORAGE_PATH/evaluation/${MODEL//\//_}/results_数据集.json`。
这一路径由生成时完整 MODEL 字符串决定；如果移动了 checkpoint 或更改了挂载路径，
模型列表需使用生成时的原字符串，才能定位旧结果。

先准备一个模型列表（这里不覆盖已有文件，使用新建目录）：

```bash
RECHECK_DIR="$STORAGE_PATH/local_rechecks/qwen3_32b_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RECHECK_DIR"
# MODEL_V1、MODEL_V2、MODEL_V5 用你之前评估时的完整 solver 路径。
printf '%s\n' "$MODEL_V1" "$MODEL_V2" "$MODEL_V5" > "$RECHECK_DIR/models.txt"

export RECHECK_LOCAL_MODEL=Qwen/Qwen3-32B
export RECHECK_GPU_IDS=0,1,2,3
export RECHECK_TENSOR_PARALLEL_SIZE=4
export RECHECK_CONCURRENCY=8
export RECHECK_MAX_COMPLETION_TOKENS=32
export EVAL_LOG_DIR="$RECHECK_DIR/logs"

# 只检查输入和打印计划，不启动 GPU 或请求。
python evaluation/run_local_recheck.py \
  --models_file "$RECHECK_DIR/models.txt" \
  --output_file "$RECHECK_DIR/final_results.jsonl" --dry_run

# 正式复核；一个 judge 服务供列表中的全部 solver 使用。
python evaluation/run_local_recheck.py \
  --models_file "$RECHECK_DIR/models.txt" \
  --output_file "$RECHECK_DIR/final_results.jsonl"
```

`run_local_recheck.py` 自身总是选择 local，无需额外设置 RECHECK_BACKEND。
中断后使用同一个 RECHECK_DIR 重跑最后一条命令，可跳过同一 judge 配置已完成的 model/dataset。
本地结果包含 `recheck` 元数据，旧 API 记录或不同 judge 配置不会被当作已完成。
请为本地 judge 使用独立结果文件，避免同一个 model/dataset 的多种评分被下游脚本混用。
如果原始逐题结果改变了，也应使用新结果文件；恢复逻辑不对输入结果做内容哈希。

## 4. 失败和结果解释

- HTTP 错误、连接超时、输出截断、空回答或非严格 Yes/No 都会报错并令命令失败。
- 失败的数据集不会写入成功汇总；此前已经完成的数据集保留，原始逐题文件不会修改。
- Yes/No 允许大小写、空白和末尾句号/感叹号，不再用“包含 yes”判定正确；非空 thinking 文本会报错。
- 服务日志保留在 EVAL_LOG_DIR 下的 `local_judge_*.log`。端口被抢占、加载失败或启动超时不会接管其他服务。
- Judge 每次启动会新建 `/tmp/rzero-judge-*`，在子进程中覆盖 TMPDIR/TMP/TEMP、TORCHINDUCTOR_CACHE_DIR、TRITON_CACHE_DIR 和 VLLM_CACHE_ROOT，避免在 `/engrfs` 共享缓存上执行编译文件替换时遇到 `Device or resource busy`。模型 HF 缓存仍在原路径，编译缓存目录保留，不自动删除。可用 `RECHECK_LOCAL_TMP_ROOT` 指向其他有足够空间的节点本地磁盘；不要指向共享文件系统。
- 程序正常结束、请求失败、Ctrl-C 或 SIGTERM 时只清理自己创建的服务/客户端进程组；不删除日志和结果文件。
- SIGKILL/节点故障无法执行 Python 清理，由 allocation/调度系统回收资源。

可调整参数：

| 参数 | 默认 | 用途 |
|---|---|---|
| RECHECK_LOCAL_MODEL | Qwen/Qwen3-32B | 模型 ID 或本地目录 |
| RECHECK_LOCAL_REVISION | 未固定 | 可选模型 commit |
| RECHECK_GPU_IDS | CUDA_VISIBLE_DEVICES / EVAL_GPU_IDS / 0,1,2,3 | 服务使用的可见 GPU；完整评估优先沿用 EVAL_GPU_IDS |
| RECHECK_TENSOR_PARALLEL_SIZE | GPU 数量 | 四卡示例为 4 |
| RECHECK_MAX_MODEL_LEN | 8192 | 输入和输出总上下文上限，过长请求报错，不静默截断 |
| RECHECK_GPU_MEMORY_UTILIZATION | 0.85 | vLLM 显存比例 |
| RECHECK_MAX_NUM_SEQS | 16 | 服务最大同时调度序列数 |
| RECHECK_CONCURRENCY | wrapper 默认 8 | 请求线程数；直接调用旧入口仍默认 32 |
| RECHECK_MAX_COMPLETION_TOKENS | 本地默认 32 | 请求 max_tokens |
| RECHECK_LOCAL_TIMEOUT | 120 秒 | 单次请求超时 |
| RECHECK_STARTUP_TIMEOUT | 900 秒 | 等待模型服务启动；首次下载慢时可增加 |
| RECHECK_LOCAL_PYTHON | 当前 Python | 可选独立 judge 环境解释器 |
| RECHECK_LOCAL_TMP_ROOT | /tmp | 独立运行目录的父路径，必须选择节点本地磁盘 |

模型更换会改变评估器，不能假定与旧 GPT 分数完全等价。先用同一批人工核对样本检查误判，
然后在各 solver 之间固定相同模型版本和参数。本地 CPU 测试验证了程序协议，未证明模型判分准确率。

## 开发验证

```bash
python -m unittest discover -s evaluation/tests -v
bash -n evaluation/evaluate.bash
```

测试依赖 requests、tqdm；真实 HTTP 集成测试仅启动模拟服务器，不加载 vLLM 或模型权重。

参考：[Qwen3-32B 模型卡](https://huggingface.co/Qwen/Qwen3-32B)、
[vLLM thinking 参数说明](https://docs.vllm.ai/en/v0.14.1/features/reasoning_outputs/)。
