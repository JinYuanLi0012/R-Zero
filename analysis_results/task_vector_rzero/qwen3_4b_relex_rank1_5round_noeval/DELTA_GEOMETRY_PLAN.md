# Task-Vector R-Zero Delta Geometry Analysis Plan

## 1. 目的与范围

本分析用于回答以下问题：

1. Questioner 从 iteration 1 到 5 的实际参数更新分别有多大？
2. Solver 从 iteration 1 到 5 实际使用的 RELEX rank-1 更新分别有多大？
3. Questioner 和 Solver 的逐轮更新方向如何变化：延续、转向、正交扩展，还是反向抵消？
4. RELEX rank-1 相比 Base-fit full delta 保留了多少强度和方向信息？
5. Solver 的参数空间变化与 Rank1 V1--V5 的评估趋势之间有哪些描述性关系？

本计划的基本原则是：

> Questioner 分析实际 full delta；Solver 主分析实际使用的 rank-1 delta；Solver full delta 作为 RELEX 前的对照组。

第一版不把参数几何关系解释为性能变化的因果证据，只做精确的参数空间测量和描述性对照。

## 2. Run 与输入模型

Run 根目录：

```text
/engrfs/project/jiaxinh/jinyuan/R-zero-storage/task_vector_rzero/
qwen3_4b_relex_rank1_5round_noeval
```

不可变 Base：

```text
Qwen/Qwen3-4B-Base
```

实现时必须优先从以下文件解析 Base 的本地 resolved path 和身份信息，不能依赖手写路径：

```text
state/run_state.json
state/base_manifest.json
```

### 2.1 Questioner checkpoints

```text
Q1: questioners/q1/huggingface
Q2: questioners/q2/global_step_5/actor/huggingface
Q3: questioners/q3/global_step_5/actor/huggingface
Q4: questioners/q4/global_step_5/actor/huggingface
Q5: questioners/q5/global_step_5/actor/huggingface
```

只使用 pipeline 实际选择的 step 5。目录中可能存在的 `global_step_1006` 不作为本分析输入。

### 2.2 Solver rank-1 checkpoints

```text
R1: rank1_fits/r1
R2: rank1_fits/r2
R3: rank1_fits/r3
R4: rank1_fits/r4
R5: rank1_fits/r5
```

### 2.3 Solver full-delta checkpoints

```text
A1: base_fits/a1/global_step_15/actor/huggingface
A2: base_fits/a2/global_step_15/actor/huggingface
A3: base_fits/a3/global_step_15/actor/huggingface
A4: base_fits/a4/global_step_15/actor/huggingface
A5: base_fits/a5/global_step_15/actor/huggingface
```

### 2.4 Composed Solver checkpoints

```text
V1: composed_solvers/v1
V2: composed_solvers/v2
V3: composed_solvers/v3
V4: composed_solvers/v4
V5: composed_solvers/v5
```

这些 checkpoint 主要用于验证 rank-1 delta 的累积公式和标记轨迹端点，不作为定义单轮 Solver delta 的来源。

## 3. Delta 的固定定义

令不可变 Base 参数为 \(B\)。

### 3.1 Questioner 实际 full delta

第一轮：

\[
\Delta_1^Q = Q_1 - B
\]

后续各轮：

\[
\Delta_i^Q = Q_i - Q_{i-1}, \qquad i=2,\ldots,5
\]

Questioner 的累计位移为：

\[
U_i^Q = \sum_{j=1}^{i}\Delta_j^Q = Q_i-B
\]

Q1 是 bootstrap Questioner。本地没有其训练前的独立 Questioner checkpoint，因此第一版统一以 Base 作为 Q1 baseline，并在报告中明确这一点。

### 3.2 Solver 实际 rank-1 delta

每轮实际进入 task-vector composition 的更新定义为：

\[
\Delta_i^{S,rank1} = R_i-B
\]

实际 Solver 的累积关系为：

\[
U_i^{S,rank1} = \sum_{j=1}^{i}\Delta_j^{S,rank1}
\]

\[
V_i \approx B + U_i^{S,rank1}
\]

这里的近似只来自最终 BF16 保存时的舍入。实现中应测量 composed checkpoint 与解析式累积结果之间的误差，验证它相对总更新足够小。

### 3.3 Solver full delta 对照

RELEX 前的 Base-fit full delta 定义为：

\[
\Delta_i^{S,full} = A_i^{step15}-B
\]

它用于分析 RELEX 的压缩和方向变化，不作为 Rank1 V1--V5 性能的直接主解释变量。

## 4. 输入验证与参数口径

计算前必须完成以下验证：

1. `run_state.json` 中 5 轮 Questioner、Base-fit、RELEX 和 compose stage 都有有效成功标记。
2. 所有 checkpoint 都存在完整的 config、权重分片和权重索引。
3. 模型 tensor keys、tensor shapes 和结构配置与 Base 一致。
4. 非浮点 tensor 必须完全一致；不参与 delta norm 和 cosine。
5. 对 tied embeddings 采用 canonical tensor，只计算一次，避免 `embed_tokens` 与 `lm_head` 重复计权。
6. 记录所有输入路径、文件大小、mtime、已有 manifest hash 和 Base identity。
7. 不重新计算所有大权重文件的 SHA256，除非显式开启严格校验模式。

主结果使用参数加权口径：每个参数元素等权，等价于 flatten 全模型后计算。

同时提供层均衡口径：先逐层计算指标，再让每层等权，避免大尺寸 MLP tensor 完全主导结论。

## 5. 分析一：Delta 的大小

对以下三组 delta 分别计算：

```text
Questioner full:      DeltaQ1--DeltaQ5
Solver rank-1:        DeltaS_rank1_1--DeltaS_rank1_5
Solver full control:  DeltaS_full_1--DeltaS_full_5
```

### 5.1 全局指标

全局 L2 norm：

\[
\|\Delta_i\|_2
\]

每参数 RMS：

\[
\frac{\|\Delta_i\|_2}{\sqrt{N}}
\]

相对更新强度：

\[
\frac{\|\Delta_i\|_2}{\|\theta_{start}\|_2}
\]

其中 Questioner 的 \(\theta_{start}\) 是该轮训练前的 Questioner；Solver full/rank-1 的共同参考为 Base。

### 5.2 层与模块指标

逐层和逐模块聚合以下指标：

- delta L2 norm；
- delta RMS；
- 相对起点权重 norm；
- 占全模型 delta norm squared 的比例。

模块分类至少包括：

- embedding / lm_head；
- attention q_proj；
- attention k_proj；
- attention v_proj；
- attention o_proj；
- MLP gate_proj；
- MLP up_proj；
- MLP down_proj；
- input/post-attention/final normalization；
- 其他参数。

### 5.3 主要产物

- Questioner full-delta norm 折线图；
- Solver rank-1/full norm 双折线图；
- Rank1/Full norm ratio 图；
- Round x Layer norm 热力图；
- Round x Module Type stacked bar；
- 全局和逐层 CSV/Parquet 表格。

## 6. 分析二：逐轮方向

### 6.1 Cosine matrices

方向相似度定义为：

\[
C_{ij}=\frac{\langle\Delta_i,\Delta_j\rangle}
{\|\Delta_i\|_2\|\Delta_j\|_2}
\]

生成：

1. Questioner full delta 5x5 cosine matrix；
2. Solver rank-1 delta 5x5 cosine matrix；
3. Solver full delta 5x5 cosine matrix；
4. Questioner full x Solver rank-1 5x5 cross-cosine matrix；
5. Solver rank-1 x Solver full 5x5 cross-cosine matrix。

### 6.2 相邻轮转角

\[
\alpha_i=\arccos\left(\cos(\Delta_i,\Delta_{i-1})\right)
\]

分别输出 Questioner full、Solver rank-1 和 Solver full 的逐轮转角。

解释约定：

- 接近 0 度：继续沿相同方向；
- 接近 90 度：引入近似正交的新方向；
- 大于 90 度：开始抵消此前更新；
- 接近 180 度：方向基本相反。

### 6.3 与历史累计方向的对齐

令：

\[
U_{i-1}=\sum_{j<i}\Delta_j
\]

计算：

\[
h_i=\cos(\Delta_i,U_{i-1})
\]

并将新 delta 分解为：

\[
\Delta_i=\Delta_i^{parallel}+\Delta_i^{orthogonal}
\]

报告：

- parallel signed coefficient；
- parallel norm；
- orthogonal norm；
- orthogonal ratio；
- 与历史方向的夹角。

该指标是解释 Solver 在 V2 达峰后是否发生转向或抵消的重点指标。

### 6.4 层均衡方向

除全局参数加权 cosine 外，额外计算：

- 每层 cosine；
- 每层相邻轮转角；
- 各层等权平均 cosine；
- cosine 为负的层比例。

## 7. 分析三：RELEX Full-to-Rank1 对照

每轮比较：

\[
\Delta_i^{S,full}
\quad\text{与}\quad
\Delta_i^{S,rank1}
\]

### 7.1 强度保留

\[
r_i=\frac{\|\Delta_i^{S,rank1}\|_2}
{\|\Delta_i^{S,full}\|_2}
\]

### 7.2 方向保留

\[
c_i=\cos(\Delta_i^{S,rank1},\Delta_i^{S,full})
\]

### 7.3 相对重建误差

\[
e_i=\frac{\|\Delta_i^{S,full}-\Delta_i^{S,rank1}\|_2}
{\|\Delta_i^{S,full}\|_2}
\]

### 7.4 Rank1 相对 Full 的分解

\[
\Delta_i^{S,rank1}
=\Delta_{i,parallel}^{S,rank1}
+\Delta_{i,orthogonal}^{S,rank1}
\]

报告全局和逐层：

- norm retention；
- cosine retention；
- relative reconstruction error；
- parallel/orthogonal fraction；
- RELEX diagnostics 中已有的 explained variance。

注意：RELEX 是 per-tensor rank-1 trajectory reconstruction，因此报告不能把它误写成“对整个模型 delta 做一次全局 rank-1 SVD”。

## 8. PCA/SVD 与轨迹可视化

仅有 5--15 个向量，因此不采用 t-SNE/UMAP。主方案使用由精确 Gram matrix 得到的 PCA/uncentered SVD。

### 8.1 联合方向平面

对以下 10 个 delta 先做单位归一化，再联合执行 uncentered SVD：

```text
Questioner full Delta 1--5
Solver rank-1 Delta 1--5
```

二维图中：

- 所有箭头从原点出发；
- Questioner 使用橙色；
- Solver 使用蓝色；
- 每个箭头标记 family 和 round；
- 标注前两个分量解释的能量比例。

该图只表达方向，不表达原始 delta 大小。

### 8.2 Solver Rank1-vs-Full 配对平面

对 Solver rank-1/full 的 10 个 delta 在同一基底投影：

- full delta 使用虚线；
- rank-1 delta 使用实线；
- 同轮端点用辅助线连接；
- 图例同时展示 norm ratio 和 cosine。

### 8.3 累积模型轨迹

Questioner 轨迹：

\[
B \rightarrow Q_1 \rightarrow Q_2 \rightarrow \cdots \rightarrow Q_5
\]

Solver 轨迹：

\[
B \rightarrow V_1 \rightarrow V_2 \rightarrow \cdots \rightarrow V_5
\]

使用累计位移的 Gram matrix 生成共同二维投影：

- Base 固定为原点；
- 用箭头连接相邻轮；
- 点颜色表示 round；
- Solver 点使用 Avg7 或选定 benchmark 着色；
- 报告二维投影保留的总能量，避免把二维图当作完整高维几何。

### 8.4 精确 Gram 方法

不把几十亿维 delta flatten 到内存。逐 tensor、逐 chunk 计算：

\[
G_{ij}=\langle\Delta_i,\Delta_j\rangle
\]

再对小型 Gram matrix 做 eigendecomposition/SVD。该方法与直接对完整参数向量做线性 PCA/SVD 等价，不使用随机抽样近似。

## 9. 评估结果联合分析

评估输入必须保存为结构化 CSV，字段至少包括：

```text
model,Avg7,MATH,GSM8K,AMC,Minerva,Olympiad,AIME24,AIME25
```

已知当前评估对象是：

```text
Qwen3-4B-Base
Rank1 V1
Rank1 V2
Rank1 V3
Rank1 V4
Rank1 V5
```

主要图表：

1. 原始 benchmark score heatmap；
2. 相对 Base 的 score delta heatmap；
3. Avg7 折线；
4. 累积 Solver 轨迹按 Avg7 着色；
5. 每轮性能增量与以下几何指标并排：
   - rank-1 delta norm；
   - 与历史累计方向 cosine；
   - orthogonal ratio；
   - rank1/full cosine；
   - rank1/full norm ratio。

只有 5 轮样本，因此相关系数只作为描述性参考，不进行显著性或因果结论。

## 10. 实现架构

建议源码位置：

```text
methods/task_vector_rzero/analysis/
├── analyze_delta_geometry.py
├── checkpoint_layout.py
├── delta_definitions.py
├── plot_delta_geometry.py
├── build_report.py
├── README.md
└── tests/
```

### 10.1 `checkpoint_layout.py`

职责：

- 解析 safetensors index 和单文件 checkpoint；
- 统一 tensor keys、shards、shapes 和 dtype；
- 检查模型兼容性；
- 流式读取 tensor chunk；
- 正确处理 tied embeddings。

应优先复用 `compose_task_vectors.py` 中已经验证过的 `ModelLayout`、chunk 读取和兼容性检查逻辑，避免产生两套不一致的 checkpoint 解析实现。

### 10.2 `delta_definitions.py`

职责：

- 从 run state 解析 B/Q/A/R/V 路径；
- 明确定义三个 delta family；
- 提供 family、round、start、end、reference 等元数据；
- 生成稳定且可审计的 delta ID。

建议 delta ID：

```text
questioner_full_r1
...
questioner_full_r5
solver_rank1_r1
...
solver_rank1_r5
solver_full_r1
...
solver_full_r5
```

### 10.3 `analyze_delta_geometry.py`

职责：

- 输入验证；
- 流式计算 delta；
- 全局、逐层和逐 tensor norm；
- Gram/cosine matrices；
- 历史方向和 parallel/orthogonal 分解；
- RELEX retention；
- 保存可恢复的中间 cache。

建议 CLI：

```bash
python -m methods.task_vector_rzero.analysis.analyze_delta_geometry \
  --run-root /path/to/run \
  --output /path/to/run/analysis/delta_geometry_v1 \
  --device cuda \
  --chunk-elements 1000000 \
  --evaluation-csv /path/to/evaluation_scores.csv \
  --resume
```

### 10.4 `plot_delta_geometry.py`

职责：

- 只读取已完成的 CSV/Parquet/NPZ；
- 不重新读取模型权重；
- 生成 PNG 和 PDF；
- 所有颜色、坐标范围和标签保持一致；
- 允许单独重画图而不重新执行大模型计算。

### 10.5 `build_report.py`

职责：

- 汇总指标和图片；
- 生成 `report.md`；
- 可选生成自包含或可移植的 `report.html`；
- 自动记录主要数值发现，但不自动生成因果结论。

## 11. 计算与数值实现

### 11.1 流式计算

不保存完整 delta checkpoint。对每个 tensor：

1. 从所需 start/end checkpoint 读取同一 chunk；
2. 转为 float32；
3. 计算 delta；
4. 对 delta block 计算小型 Gram update；
5. 将 chunk 结果以 float64 累计到 CPU；
6. 更新逐 tensor、逐层和全局统计；
7. 释放 chunk。

### 11.2 CPU/CUDA

支持：

```text
--device cpu
--device cuda
```

CUDA 模式：

- CPU 负责 safetensors I/O；
- GPU 负责 chunk delta 和小矩阵乘法；
- Gram chunk 使用 float32 计算；
- CPU 使用 float64 跨 chunk 累计；
- 默认关闭 TF32；
- 选取部分 tensor 用 CPU float64 复核误差。

CPU 模式作为可靠 fallback，但预计明显更慢。

### 11.3 断点恢复与原子落盘

大模型扫描应按 shard 或 tensor 建立进度：

```text
cache/progress.json
cache/partial_gram.npz
cache/partial_layer_metrics.*
```

要求：

- 每个完成单元原子更新进度；
- `--resume` 只能复用输入 fingerprint 完全一致的 cache；
- 输入路径、文件大小、mtime 或 manifest identity 变化时拒绝复用；
- 最终产物先写临时文件，再原子 rename。

## 12. 产物目录

本次分析根目录：

```text
analysis/delta_geometry_v1/
```

完整结构：

```text
delta_geometry_v1/
├── manifest.json
├── report.md
├── report.html
├── cache/
│   ├── gram_matrices.npz
│   └── progress.json
├── metrics/
│   ├── global_norms.csv
│   ├── direction_metrics.csv
│   ├── relex_retention.csv
│   ├── per_layer_metrics.parquet
│   └── per_tensor_norms.parquet
├── matrices/
│   ├── questioner_cosine.csv
│   ├── solver_rank1_cosine.csv
│   ├── solver_full_cosine.csv
│   ├── questioner_solver_cross_cosine.csv
│   └── rank1_full_cross_cosine.csv
├── embeddings/
│   ├── direction_svd.csv
│   └── cumulative_trajectory.csv
├── figures/
│   ├── global_delta_norms.png
│   ├── questioner_cosine.png
│   ├── solver_rank1_cosine.png
│   ├── solver_full_cosine.png
│   ├── questioner_solver_cross.png
│   ├── adjacent_angles.png
│   ├── historical_alignment.png
│   ├── relex_retention.png
│   ├── direction_plane.png
│   ├── rank1_vs_full_plane.png
│   ├── cumulative_trajectory.png
│   ├── layer_norm_heatmap.png
│   └── evaluation_geometry.png
└── logs/
```

分析源码进入代码仓库；所有 run-specific cache、表格、图片和报告进入 storage 中对应 run 的 `analysis/`，不污染 checkpoint 目录。

## 13. 测试计划

### 13.1 Synthetic checkpoint tests

构造小型 safetensors checkpoints，覆盖：

- 已知 norm；
- 同向、正交、反向 delta；
- 已知 Gram/cosine matrix；
- rank/full 已知缩放和旋转；
- tied embeddings；
- non-floating tensor；
- 多 shard checkpoint；
- resume 后结果与一次性计算一致。

### 13.2 真实模型数值复核

- 随机选择若干 tensor/chunk；
- 使用 CPU float64 手工计算 norm 和 dot；
- 与主计算结果比较；
- 记录最大绝对误差和相对误差；
- 验证 Gram matrix 对称性和 positive-semidefinite 数值容差；
- 验证 cosine 对角线接近 1，所有值位于 `[-1, 1]` 容差范围内。

### 13.3 Pipeline consistency

- 验证 `V_i-B` 与 `sum_j<=i(R_j-B)` 的相对误差；
- 验证 Questioner telescoping：`sum_j<=i DeltaQ_j` 与 `Q_i-B`；
- 验证全局 norm squared 等于各层 norm squared 之和；
- 验证每层指标聚合到全局指标；
- 验证报告引用的数值均来自落盘表格，而非绘图脚本重复计算。

## 14. 实施阶段

### Phase 1：输入发现与验证

- 实现 run state/path 解析；
- 建立模型兼容性验证；
- 生成输入 manifest；
- 完成 synthetic layout tests。

### Phase 2：核心几何计算

- 实现流式 delta；
- 实现全局/per-tensor/per-layer norm；
- 实现 Gram/cosine；
- 实现 checkpoint/resume cache；
- 完成 synthetic numerical tests。

### Phase 3：方向与 RELEX 指标

- 相邻轮角度；
- 历史累计方向；
- parallel/orthogonal 分解；
- rank1/full retention；
- composed/checkpoint consistency validation。

### Phase 4：可视化

- norm 和 heatmap；
- direction plane；
- Rank1-vs-Full paired plane；
- cumulative trajectory；
- 统一配色和图例；
- PNG/PDF 双格式。

### Phase 5：评估整合与报告

- 接入评估 CSV；
- 生成 benchmark 图；
- 将 Avg7 映射到 Solver trajectory；
- 输出 Markdown/HTML 报告；
- 添加限制和解释边界。

## 15. Review 验收清单

后续实现 review 时逐项确认。

### 定义对齐

- [ ] Questioner R1 使用 `Q1-Base`。
- [ ] Questioner R2--R5 使用 `Qi-Q(i-1)`。
- [ ] Solver 主分析使用 `Ri-Base`。
- [ ] Solver full 对照使用 `Ai_step15-Base`。
- [ ] 没有错误地使用 composed `Vi-V(i-1)` 替代单轮 RELEX task vector。
- [ ] 报告明确区分实际 Rank1 轨迹和 full-delta 对照。

### 输入与数值

- [ ] 所有 checkpoint keys/shapes/config 均验证一致。
- [ ] tied embeddings 没有重复计权。
- [ ] 非浮点 tensor 已验证且未参与 norm/cosine。
- [ ] delta 在 float32 或更高精度中计算。
- [ ] 跨 chunk 使用 float64 累计。
- [ ] TF32 默认关闭或明确记录。
- [ ] 输入 fingerprint 和 resume cache 绑定。

### 指标完整性

- [ ] 三组 delta 都有 global norm/RMS/relative norm。
- [ ] 三组 delta 都有 5x5 cosine matrix。
- [ ] 有 Questioner x Solver rank-1 cross-cosine。
- [ ] 有相邻轮角度。
- [ ] 有历史累计方向 alignment。
- [ ] 有 parallel/orthogonal 分解。
- [ ] 有 Rank1/Full norm ratio、cosine 和 reconstruction error。
- [ ] 有 per-layer 和 per-module 统计。

### PCA/SVD 与图形

- [ ] PCA/SVD 来自精确 Gram，而非不透明的随机抽样。
- [ ] 方向图使用单位 delta，避免 norm 污染方向比较。
- [ ] 轨迹图使用累计位移并保留 Base 原点。
- [ ] 图中报告二维投影解释能量。
- [ ] 没有使用不适合少量样本的 t-SNE/UMAP。
- [ ] 所有图片同时有可复现的坐标 CSV。

### 正确性验证

- [ ] Synthetic tests 覆盖同向、正交和反向向量。
- [ ] Questioner telescoping identity 通过。
- [ ] Solver composition consistency 通过。
- [ ] Gram 对称性和 PSD 容差通过。
- [ ] 层级聚合与全局结果一致。
- [ ] 真实模型抽样 float64 复核通过。

### 报告与解释

- [ ] 参数几何与评估结果只做描述性联系。
- [ ] 没有将相关性表述为因果关系。
- [ ] 明确 Q1 是 bootstrap 且以 Base 为 baseline。
- [ ] 明确 RELEX 是 per-tensor rank-1 reconstruction。
- [ ] 所有报告数值可追溯到 CSV/Parquet/NPZ。
- [ ] run-specific 产物全部位于 storage 的 `analysis/delta_geometry_v1/`。

## 16. 最终报告结构

最终报告固定分为：

```text
A. Questioner：真实 full-delta 演化
B. Solver：真实 rank-1-delta 演化
C. RELEX：full delta 到 rank-1 delta 改变了什么
D. Questioner 与 Solver 的跨模型方向关系
E. 参数几何与 Rank1 V1--V5 评估趋势
F. 数值验证、限制与后续工作
```

该结构用于保证实现和解释始终与实际训练流程及实际评估对象对齐。
