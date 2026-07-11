# Task-Vector R-Zero：运行与排错手册

> 算法背景、与 R-Zero/RELEX 的关系请先看 [README.md](README.md)。本文只回答“如何配置、如何启动、产物在哪里、失败后怎么办”。

## 1. 运行前准备

在训练服务器进入 R-Zero 仓库：

```bash
cd /path/to/R-Zero
```

激活原 R-Zero 环境并设置存储：

```bash
source env_rzero.sh

export STORAGE_PATH=/data/jinyuan/rzero_storage
export HUGGINGFACENAME=jinyuan222
```

推荐通过环境变量提供令牌：

```bash
export HF_TOKEN=...
export WANDB_API_KEY=...
export OPENAI_API_KEY=...   # 完整评估中的 GPT recheck 需要
```

确认至少具备：

- 原 R-Zero 可用的 Python/verl/vLLM/CUDA 环境。
- `torch`、`transformers`、`safetensors`、`datasets`、`huggingface_hub`。
- 足够的 GPU 显存、CPU 内存和本地磁盘。
- Rank-1 模式比 Full-delta 多保留并合并 step 5/10/15 checkpoint，需要更多磁盘和合并时间。

## 2. 核心配置

默认配置文件：

```text
methods/task_vector_rzero/config.sh
```

最常修改的配置：

```bash
BASE_MODEL=Qwen/Qwen3-4B-Base
MODEL_ABBR=qwen3_4b
NUM_ROUNDS=5
TASK_VECTOR_SCALES=(1 1 1 1 1)

STORAGE_PATH=/data/jinyuan/rzero_storage
HUGGINGFACENAME=jinyuan222

QUESTIONER_TRAIN_GPU_IDS=0,1
VLLM_GPU_IDS=2,3
QUESTION_GPU_IDS=0,1,2,3

EVALUATE_EACH_ROUND=true
MIRROR_DATASETS=true
UPLOAD_MODELS=false
FULL_LOAD_VALIDATE=true
```

Rank-1 默认配置：

```bash
SOLVER_MAX_STEPS=20
SOLVER_SAVE_FREQ=5
SOLVER_MERGE_STEP=15
RANK1_HISTORY_STEPS=(5 10 15)
RANK1_TARGET_STEP=15
RANK1_PRODUCE_FULL_V1_SIDECAR=true
```

第一轮 bootstrap 默认配置：

```bash
BOOTSTRAP_ROUND1=true
BOOTSTRAP_QUESTIONER_MODEL=jinyuan222/qwen3_4b_fullrun_authorsettings_questioner_v1
BOOTSTRAP_DATASET=jinyuan222/qwen3_4b_fullrun_authorsettings_solver_v1
BOOTSTRAP_DATASET_CONFIG=qwen3_4b_fullrun_authorsettings_solver_v1
BOOTSTRAP_DATASET_SPLIT=train
```

在这个模式下，第一轮不会训练 Q1、不会重新出题和标注，而是把已有 Q1 固定为具体 HF snapshot，把已有 D1 保存为本地 `datasets/d1/train.parquet`，然后直接从 Base 训练 Solver1。Rank-1 训练仍保存和合并 step 5/10/15。第二轮 Q2 从该 Q1 初始化，并以新 Rank-1/Full Solver V1 为对手。

约束：

- `RANK1_HISTORY_STEPS` 至少包含两个 step。
- 所有 history step 必须由 `SOLVER_SAVE_FREQ` 实际保存。
- history step 不得超过 `SOLVER_MAX_STEPS`。
- `RANK1_TARGET_STEP` 必须属于 history，并与 `SOLVER_MERGE_STEP` 相同。

不要让 Full 和 Rank-1 使用同一个 `RUN_NAME`。两个官方入口默认会自动使用不同名称。

## 3. 启动 Full-delta 五轮实验

```bash
source env_rzero.sh

bash methods/task_vector_rzero/run_full_delta.sh \
  --config methods/task_vector_rzero/config.sh
```

默认 run 名称：

```text
qwen3_4b_full_delta
```

运行逻辑：

```text
每轮从 Base 训练 A_i
→ 使用完整 A_i - Base
→ 累计 Full Solver
→ Full Solver 进入下一轮
```

## 4. 启动 RELEX Rank-1 五轮实验

```bash
source env_rzero.sh

bash methods/task_vector_rzero/run_rank1.sh \
  --config methods/task_vector_rzero/config.sh
```

默认 run 名称：

```text
qwen3_4b_relex_rank1
```

运行逻辑：

```text
第一轮复用已有 Q1/D1，直接从 Base 训练 step 5/10/15
→ per-tensor RELEX rank-1 reconstruction
→ 累计 Rank-1 Solver
→ 第二轮开始由 Rank-1 Solver 驱动 Questioner 和数据闭环
```

第一轮还会生成同数据 Full-delta V1：

```text
$RUN_ROOT/comparisons/full_delta_v1_same_data/
```

它不会进入下一轮。

旁路 Full V1 只会被构造和加载验证，不会被五轮编排器自动评估；需要成对结果时，请对该目录另行运行评估。

## 5. 指定独立实验名称

推荐为日期、seed 或消融实验设置不同名称：

```bash
RUN_NAME=qwen3_4b_full_delta_seed1 \
bash methods/task_vector_rzero/run_full_delta.sh \
  --config methods/task_vector_rzero/config.sh
```

```bash
RUN_NAME=qwen3_4b_relex_rank1_seed1 \
bash methods/task_vector_rzero/run_rank1.sh \
  --config methods/task_vector_rzero/config.sh
```

已有 run 的算法或训练配置发生变化时，不要覆盖原目录；请使用新的 `RUN_NAME`。

## 6. 中断后恢复

Full-delta：

```bash
bash methods/task_vector_rzero/run_full_delta.sh \
  --config methods/task_vector_rzero/config.sh \
  --resume
```

Rank-1：

```bash
bash methods/task_vector_rzero/run_rank1.sh \
  --config methods/task_vector_rzero/config.sh \
  --resume
```

恢复规则：

- 只有配置 fingerprint 完全一致的 `_SUCCESS.json` 阶段会跳过。
- 正式 artifact 已原子移动但 marker 尚未来得及写入时，会重新验证并补写 marker。
- Base revision、文件集合或 SHA256 改变时拒绝恢复。
- 配置确实要改变时，应创建新 `RUN_NAME`。

## 7. Smoke test 和跳过评估

只想验证训练、组合和恢复链条时：

```bash
bash methods/task_vector_rzero/run_full_delta.sh \
  --config methods/task_vector_rzero/config.sh \
  --no-eval
```

Rank-1 同理：

```bash
bash methods/task_vector_rzero/run_rank1.sh \
  --config methods/task_vector_rzero/config.sh \
  --no-eval
```

也可以在独立配置中减少：

```bash
NUM_ROUNDS=1
SOLVER_GENERATE_SAMPLES=50
```

注意：Rank-1 仍要求训练产生配置中的所有 history checkpoint。若降低 `SOLVER_MAX_STEPS`，必须同步修改 `RANK1_HISTORY_STEPS`、`RANK1_TARGET_STEP` 和 `SOLVER_MERGE_STEP`。

## 8. 产物位置

统一根目录：

```bash
RUN_ROOT="$STORAGE_PATH/task_vector_rzero/$RUN_NAME"
```

主要目录：

```text
$RUN_ROOT/
  questioners/q1...qN/
  datasets/d1...dN/
  base_fits/a1...aN/
  rank1_fits/r1...rN/
  composed_solvers/v1...vN/
  comparisons/
  evaluations/v1...vN/
  logs/
  state/
```

最终 Solver：

```text
$RUN_ROOT/composed_solvers/vN/
```

Base-fit step 15：

```text
$RUN_ROOT/base_fits/aN/global_step_15/actor/huggingface/
```

Rank-1 当轮辅助模型：

```text
$RUN_ROOT/rank1_fits/rN/
```

本地训练数据：

```text
$RUN_ROOT/datasets/dN/train.parquet
```

## 9. 查看当前进度

查看阶段状态：

```bash
python3 -m json.tool "$RUN_ROOT/state/run_state.json" | less
```

查看完成标记：

```bash
find "$RUN_ROOT/state" -name '_SUCCESS.json' -print | sort
```

查看最近日志：

```bash
ls -lt "$RUN_ROOT/logs" | head
tail -f "$RUN_ROOT/logs/questioner_v1.log"
tail -f "$RUN_ROOT/logs/base_fit_v1.log"
tail -f "$RUN_ROOT/logs/compose_v1.log"
tail -f "$RUN_ROOT/logs/relex_rank1_v1.log"
```

Rank-1 诊断：

```bash
python3 -m json.tool \
  "$RUN_ROOT/rank1_fits/r1/relex_rank1_diagnostics.json" | less
```

重点字段：

- `mean_explained_variance`
- 每个 tensor 的 `explained_variance`
- `target_delta_norm`
- `rank1_delta_norm`

## 10. Hugging Face 行为

默认：

- 每轮数据保存本地 Parquet。
- 每轮数据镜像到 private HF dataset。
- Questioner、Base-fit、Rank-1 和组合 Solver 默认不上传。

开启模型上传：

```bash
export UPLOAD_MODELS=true
```

或在配置中设置：

```bash
UPLOAD_MODELS=true
HF_MODELS_PRIVATE=true
```

Full 和 Rank-1 的 HF repo 名称包含不同 variant，不会互相覆盖。

## 11. 单独运行组件

### 11.1 Full-delta composer

```bash
python3 methods/task_vector_rzero/compose_task_vectors.py \
  --base /path/to/base \
  --auxiliary /path/to/a1 --scale 1 \
  --auxiliary /path/to/a2 --scale 1 \
  --output /path/to/full_v2
```

### 11.2 RELEX Rank-1 reconstruction

```bash
python3 methods/task_vector_rzero/relex_rank1.py \
  --base /path/to/base \
  --checkpoint 5=/path/to/step5/huggingface \
  --checkpoint 10=/path/to/step10/huggingface \
  --checkpoint 15=/path/to/step15/huggingface \
  --target-step 15 \
  --output /path/to/rank1_model
```

### 11.3 验证 checkpoint

结构检查：

```bash
python3 methods/task_vector_rzero/validate_checkpoint.py /path/to/model
```

真实模型和 tokenizer 加载：

```bash
python3 methods/task_vector_rzero/validate_checkpoint.py \
  /path/to/model --full-load
```

### 11.4 已有 V1 的 Full-delta V2 验证

```bash
bash methods/task_vector_rzero/validate_existing_v2.sh \
  Qwen/Qwen3-4B-Base \
  jinyuan222/qwen3_4b_fullrun_authorsettings_solver_v1 \
  jinyuan222/SECOND_ROUND_DATASET@train \
  "$STORAGE_PATH/task_vector_rzero/existing_v2_validation"
```

这个脚本只验证 Full-delta 老师公式。旧 V1 没有完整 Base-fit 轨迹，因此不能用最终 V1 单点可靠恢复 RELEX Rank-1。

## 12. 自动测试

在训练环境运行：

```bash
python3 -m unittest discover \
  -s methods/task_vector_rzero/tests \
  -v
```

预期覆盖：Full-delta、Rank-1 SVD 数值、tied embeddings、真实微型 Qwen3 加载、Base 哈希和 pipeline state。

## 13. 常见错误

### `Run already exists ... Use --resume`

同一 `RUN_NAME` 已存在。配置未改变时加 `--resume`；配置改变时换新的 `RUN_NAME`。

### `Existing run state has fingerprint ...`

当前配置与旧实验不同。不要混用产物，创建新 run。

### `RANK1_TARGET_STEP must appear ...`

目标 step 没有写入 `RANK1_HISTORY_STEPS`。

### `Rank-1 history step ... is not emitted`

history step 不是 `SOLVER_SAVE_FREQ` 的倍数。同步修改保存频率或 history。

### `Expected merge checkpoint does not exist`

训练没有保存所需 step，或者 save limit 删除了 checkpoint。Rank-1 入口会自动将 `SOLVER_SAVE_LIMIT=-1`，但 history/save frequency 仍需匹配。

### `Immutable Base file changed`

Base snapshot 或本地目录在实验中途发生变化。不要继续混合任务向量；恢复原 Base，或者使用新 `RUN_NAME` 开始新实验。

### 模型结构正确但 vLLM 加载失败

先运行：

```bash
python3 methods/task_vector_rzero/validate_checkpoint.py \
  /path/to/model --full-load
```

再检查 Transformers、vLLM 与 CUDA 版本是否与原 R-Zero 环境一致。

### Rank-1 磁盘不足

Rank-1 会保留更多 FSDP checkpoint，并额外产生 step 5/10/15 的 HF 合并模型。运行前确认磁盘；实验完成后再依据 manifest 进行有计划的清理，不要在运行中删除轨迹 checkpoint。

## 14. 推荐正式实验顺序

1. 执行全部自动测试。
2. Full-delta 单轮 `--no-eval` smoke test。
3. Rank-1 单轮 `--no-eval` smoke test。
4. 验证 V1 Full 和 V1 Rank-1 均能完整加载。
5. 正式 Full-delta 五轮。
6. 正式 Rank-1 五轮。
7. 汇总每轮 benchmark、Rank-1 explained variance 和同数据 V1 对照。
