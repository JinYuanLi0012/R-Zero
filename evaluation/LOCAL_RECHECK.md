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
