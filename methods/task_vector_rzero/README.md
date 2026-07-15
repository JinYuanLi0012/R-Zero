# Task-Vector R-Zero：算法与实施总览

> 本文用于会议讨论、实验复盘和新对话快速建立上下文。实际运行命令、配置、恢复和排错请看 [README_USAGE.md](README_USAGE.md)。

## 1. 一句话说明

我们保留了 R-Zero 原本的 Questioner–Solver 五轮自进化闭环，只改变每一轮 Solver 的获得方式：

- 原始 R-Zero：新 Solver 从上一轮 Solver 继续训练。
- Full-delta：新任务始终从同一个 Base 独立训练，再累计完整任务向量。
- RELEX Rank-1：新任务始终从同一个 Base 独立训练，再对训练轨迹做 per-tensor rank-1 SVD 去噪，累计去噪后的任务向量。

现在可以独立运行两组五轮实验：

```text
Full V1 → Full V2 → Full V3 → Full V4 → Full V5

Rank1 V1 → Rank1 V2 → Rank1 V3 → Rank1 V4 → Rank1 V5
```

两条链拥有各自的 Questioner、数据、Solver、评估和 Hugging Face 名称，不会交叉使用模型。

## 2. 为什么进行这个改动

原始 R-Zero 第 `i` 轮为：

\[
\pi_i=\operatorname{Tune}(\pi_{i-1},D_i)
\]

随着轮次增加，Solver 一直在已经偏移的模型上继续训练。老师提出的替代方案是让 Base 独立学习当轮数据：

\[
A_i=\operatorname{Tune}(Base,D_i)
\]

\[
\Delta_i=A_i-Base
\]

再把当轮能力增量加入已有能力：

\[
\pi_i=\pi_{i-1}+\Delta_i
\]

为避免反复读取和保存 BF16 组合模型造成累计舍入误差，工程上每轮从同一个不可变 Base 重新组合：

\[
\pi_i=Base+\sum_{k=1}^{i}\lambda_k\Delta_k
\]

精确数学下，这与递归相加等价；默认所有 \(\lambda_k=1\)。

## 3. R-Zero 中保持不变的部分

从第二轮开始，每轮 `i` 的前半段仍然遵循原始 R-Zero：

1. `Q_i` 从 `Q_(i-1)` 初始化。
2. `Q_i` 针对当前链条的 `pi_(i-1)` 训练。
3. `Q_i` 生成本轮问题。
4. 当前链条的 `pi_(i-1)` 解题、进行多数投票、生成伪标签并筛选难度。
5. Questioner 的奖励、训练模板、GRPO 设置、GPU 服务方式保持原实现。
6. Solver 的训练数据、模板、GRPO/KL 设置和正式选择的 step 15 保持原实现；Rank-1 模式在 step 15 停止，因为之后的 step 不参与目标 checkpoint 重建。

核心不变量是：

```text
feedback_solver = labeler_model = 当前链条上一轮的组合 Solver
train_init_model = 永远是同一个不可变 Base
```

### 固定复用原始实验的第一轮起点

当前 fork 默认不重新执行 `Q0 → Q1`，也不重新生成第一轮数据。两条任务向量实验共同复用原始 R-Zero 已上传到 Hugging Face 的：

```text
Q1 = jinyuan222/qwen3_4b_fullrun_authorsettings_questioner_v1
D1 = jinyuan222/qwen3_4b_fullrun_authorsettings_solver_v1
```

其中 D1 的 dataset config 也是 `qwen3_4b_fullrun_authorsettings_solver_v1`。第一轮状态机变为：

```text
固定并校验已有 Q1 revision
→ 下载已有、已标注和过滤的 D1 到本地 Parquet
→ 跳过 Questioner 训练、重新出题和重新标注
→ 直接从 Base 在 D1 上训练 Solver1
```

第二轮才恢复闭环：Q2 从已有 Q1 初始化，以新实验产生的组合 Solver V1 为对手；D2 由 Q2 生成，并由组合 Solver V1 标注。

这样 Full-delta 与 Rank-1 的第一轮数据完全相同，算法差异只来自 Solver 权重处理。若确实要从 Base 重跑 Q1/D1，可显式设置 `BOOTSTRAP_ROUND1=false`。

## 4. Full-delta 五轮链

第一轮固定使用已有 Q1/D1；以下 Questioner 和数据公式适用于 `i >= 2`，Solver 公式适用于所有轮次：

\[
Q_i=\operatorname{TrainQuestioner}(Q_{i-1},\pi_{i-1}^{full})
\]

\[
D_i=\operatorname{GenerateAndLabel}(Q_i,\pi_{i-1}^{full})
\]

\[
A_i=\operatorname{TrainSolver}(Base,D_i)
\]

使用完整任务向量：

\[
\Delta_i^{full}=A_i-Base
\]

累计得到：

\[
\pi_i^{full}=Base+\sum_{k=1}^{i}\lambda_k\Delta_k^{full}
\]

`pi_i_full` 会成为下一轮 Questioner 的对手和数据标注模型。

## 5. RELEX Rank-1 五轮链

Rank-1 模式同样先从 Base 独立训练当轮 Solver，但保留训练轨迹 checkpoint：

```text
Base → step 1 → step 2 → ... → step 15
```

对每个权重 tensor 独立计算绝对 delta：

\[
\Delta_t=\theta_t-\theta_{base}
\]

将同一 tensor 在多个 checkpoint 的 delta 展平并堆叠：

\[
M=
\begin{bmatrix}
\Delta_5\\
\Delta_{10}\\
\Delta_{15}
\end{bmatrix}
\]

按照 RELEX reconstruct 模式：

\[
G=MM^\top
\]

对 `G` 做特征分解，保留第一主方向：

\[
V_1=\frac{M^\top U_1}{S_1}
\]

设 `p(15)` 表示 step 15 在轨迹矩阵中的行位置。step 15 的 rank-1 系数与重建向量为：

\[
c_{15}=U_1[p(15)]S_1
\]

\[
\hat\Delta_{15}=c_{15}V_1^\top
\]

生成当轮去噪辅助模型：

\[
R_i=Base+\hat\Delta_i
\]

Rank-1 链累计：

\[
\pi_i^{rank1}=Base+\sum_{k=1}^{i}\lambda_k(R_k-Base)
\]

`pi_i_rank1` 会进入下一轮；原始 Base-fit 模型 `A_i` 和 Full-delta sidecar 都不会进入下一轮。

## 6. 与 RELEX 的对应关系

Rank-1 实现专门复现了 RELEX 的 `rank=1 + reconstruct` 路径：

| RELEX 行为 | 当前实现 |
|---|---|
| 每个 tensor 独立处理 | 一致 |
| checkpoint 相对 Base 的绝对 delta | 一致 |
| Base/checkpoint 转 FP16 后相减 | 一致 |
| FP32 Gram matrix | 一致 |
| `np.linalg.eigh` 并按特征值降序 | 一致 |
| `V=M^T U/S` | 一致 |
| 使用目标 checkpoint 的 `U[target] * S` | 一致 |
| rank-1 reconstruction | 一致 |
| Base FP32 加重建 delta | 一致 |
| BF16 checkpoint 输出 | 一致 |
| tied embedding 特殊处理 | 一致 |

存在两项不改变数学结果的工程差异：

1. RELEX 先将 FP16 delta 写入 mmap；这里按 tensor 分块即时计算相同的 FP16 delta，减少中间磁盘占用。
2. RELEX 最后通过完整 model state dict 保存；这里流式写 safetensors，随后真实执行 `AutoModelForCausalLM` 和 tokenizer 完整加载验证。

默认轨迹使用连续 step 1–15，与 RELEX 使用每个 optimizer step 构造轨迹的方式一致。Rank-1 模式因此设置 `SOLVER_SAVE_FREQ=1`，并以 step 15 为目标 checkpoint。

## 7. 两条实验链如何隔离

Full-delta：

```text
CURRENT_SOLVER = previous full-delta composed Solver
AUXILIARY_i    = Base-fit A_i
```

Rank-1：

```text
CURRENT_SOLVER = previous rank-1 composed Solver
AUXILIARY_i    = RELEX rank-1 model R_i
```

Rank-1 第一轮还会额外生成：

```text
comparisons/full_delta_v1_same_data/
```

它与 Rank-1 V1 使用完全相同的第一轮数据和 Base-fit 训练，用于成对比较；它只是旁路产物，不参与第二轮。

## 8. 不可变 Base 与数值安全

运行开始时：

- Hub Base 被解析为具体 commit snapshot。
- 本地 Base 被解析为绝对路径。
- 权重、配置、tokenizer 等文件写入 SHA256 manifest。
- 恢复运行时重新验证 Base 文件集合和哈希。

每轮组合时：

- 检查 config、tensor key 和 shape。
- 检查 NaN/Inf。
- Full-delta 在 FP32 中相减和累计。
- Rank-1 遵循 RELEX：FP16 delta、FP32 SVD、BF16 输出。
- Qwen3 tied embeddings 以 `model.embed_tokens.weight` 为唯一任务向量，`lm_head` 由模型加载时恢复绑定。
- 正式模式会真实加载组合后的模型和 tokenizer。

## 9. 工程组件

```text
methods/task_vector_rzero/
  run.sh                     # 两种模式共用的五轮编排器
  run_full_delta.sh          # Full-delta 一键入口
  run_rank1.sh               # RELEX Rank-1 一键入口
  train_base_fit.sh          # 永远从 Base 训练 Solver
  compose_task_vectors.py    # 累计完整/Rank-1 有效任务向量
  relex_rank1.py             # per-tensor SVD rank-1 reconstruction
  extrapolate_rank1.py       # 第一轮 Rank-1 delta 的纯缩放外推
  run_rank1_extrapolation.sh # Base + k * delta_1 一键入口
  prepare_dataset.py         # 生成本地 Parquet
  resolve_base.py            # 固定 Base revision 和哈希
  pipeline_state.py          # 阶段状态、fingerprint、恢复
  validate_checkpoint.py     # 结构及真实模型加载验证
  upload_dataset.py          # 私有 HF dataset 镜像
  upload_model.py            # 显式可选模型上传
  validate_existing_v2.sh    # 旧 V1 + 第二轮数据的 Full-delta V2 验证
  README.md                  # 本文：算法和实施总览
  README_USAGE.md            # 运行、恢复和排错手册
```

原始 `scripts/main.sh` 仍然保留，可继续运行原始 sequential R-Zero。

## 10. 产物布局

每个实验位于：

```text
$STORAGE_PATH/task_vector_rzero/$RUN_NAME/
  questioners/q1...qN/
  datasets/d1...dN/
  base_fits/a1...aN/
  rank1_fits/r1...rN/        # 仅 Rank-1 链有实际内容
  composed_solvers/v1...vN/
  comparisons/               # Rank-1 V1 的同数据 Full sidecar
  evaluations/v1...vN/
  state/base_manifest.json
  state/run_state.json
  state/round_N/.../_SUCCESS.json
  logs/
```

重要 manifest：

- `base_manifest.json`：不可变 Base 来源、revision 和文件哈希。
- `dataset_manifest.json`：样本数、过滤区间和 Parquet 哈希。
- `task_vector_manifest.json`：累计 Base、辅助模型、系数和输出分片。
- `task_vector_diagnostics.json`：任务向量范数、Gram matrix、cosine。
- `relex_rank1_manifest.json`：Rank-1 轨迹、目标 step 和输出哈希。
- `relex_rank1_diagnostics.json`：每个 tensor 的解释方差、奇异值和重建范数。

## 11. 相比原始 R-Zero 的非算法工程变化

- 本地 Parquet 是训练数据主副本，HF private dataset 是镜像。
- 原始问题评估结果被保留，不再立即删除。
- 增加阶段级 `_SUCCESS`、配置 fingerprint 和恢复。
- Rank-1 Base-fit 支持从最近完整 optimizer step 恢复；所有 step 的模型轨迹保留，但旧 optimizer/extra/dataloader 状态会在新 checkpoint 原子提交后清理。
- Full-delta Base-fit 使用相同恢复机制，但在新 checkpoint 原子提交后删除整个旧 checkpoint，只保留最新完整恢复点。
- 模型默认保存在本地；只有显式开启才上传 HF。
- 评估结果进入各自 run 目录，不污染仓库根目录。
- 原始 R-Zero 最后重复评估 Base；新流程不重复做这次 Base 评估。

这些变化不改变 Questioner、数据标注和 GRPO 目标。

## 12. 当前验证状态

自动测试套件包含原有 11 项、2 项 bootstrap artifact 测试和 4 项 Base-fit resume/retention 测试，覆盖：

- 多 shard Full-delta 组合。
- 非整数向量系数。
- tensor key、shape、config 不一致失败。
- Qwen3 tied embeddings。
- Base 内容篡改检测。
- pipeline fingerprint 和完成标记。
- Rank-1 数值结果与直接 NumPy SVD 对照。
- 真实微型 Qwen3 Full-delta checkpoint 完整加载。
- 真实微型 Qwen3 Rank-1 checkpoint 完整加载。

尚未完成的是大型 Qwen3 在训练服务器上的真实五轮运行。代码测试通过不等于已经获得实验结果。

## 13. 会议中最值得比较的实验

建议至少报告：

1. 原始 sequential R-Zero。
2. Base-independent Full-delta R-Zero。
3. Base-independent RELEX Rank-1 R-Zero。
4. 每轮 V1...VN 的 benchmark 曲线。
5. Rank-1 每层解释方差和重建范数。
6. Rank-1 V1 与同数据 Full V1 的直接比较。

这样才能区分性能变化来自：

- Base 独立训练；
- 完整任务向量累计；
- RELEX Rank-1 去噪；
- 或不同轮次数据分布。
