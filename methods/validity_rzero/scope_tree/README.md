# Frozen Base 两层数学 scope 树（v3）

一个 frozen `Qwen/Qwen3-4B-Base`、一个单卡 vLLM 实例，离线构建数学出题范围。
不训练模型，不修改 Questioner/Solver 的训练、reward 或采样流程。

## v3 的问题空间

所有动作共享原 R-Zero Questioner 的目标：brand-new、non-trivial、self-contained、
checkable，competition-style or similarly challenging。保留其领域举例
`including but not limited to algebra, geometry, number theory, combinatorics,
prealgebra, probability, statistics, and calculus`。这些举例不是预置节点或覆盖配额。
`fewer than 30% of advanced high-school students` 只是生成目标，不是已测量或校准的难度。

避免主要产生教材套公式题、著名题复用，以及依赖外部数据、软件或开放建模的题型。
初等对象可以支持困难推理；自包含统计推理题也允许。不是按知识点所属年级过滤。

- L1：breadth/abstraction 可比的宽领域，每个能容纳多个结构不同的 L2。
- L2：最终叶子，可直接分配给 Questioner，能支持许多在结构与推理上不同的非平凡题。
- 每个 parent 选择一个 coherent dominant partition axis，不接受模糊的 OR-list。
- 不设置目标宽度、不提供参考 taxonomy、不用 embedding/clustering、不展开第三层。

## 状态机与停止条件

```text
PROPOSE 初始紧凑 sibling set
  → SIBLING AUDIT 合法性
  → 必要时定向 REPAIR（同一局部 build 累计最多 2 次）
  → COVERAGE CHECK A
  → COVERAGE CHECK B
  → 同一未变集合连续两次 NO-MAJOR-GAP：冻结
  → 任一次发现重大缺口：只增补一个 peer-level child
      → 全 sibling set 重新 audit
      → 清空覆盖确认，从头检查
```

Sibling audit **不再包含 gap**，严格检查 parent fit、单一划分轴、`comparable_breadth`、
全部 unordered sibling pairs；depth=2 还检查 `generation_ready`。
任何检查失败不得 KEEP；每对 OVERLAP/NESTED/NEAR_DUPLICATE 至少一个端点需要改动。
数学上的普通交叉不等于大量重复生成，但不能只凭名称不同就判 DISTINCT。

覆盖检查有独立 schema：

```json
{"has_major_gap": false, "gap_description": null, "reason": "..."}
```

YES 必须给出非空 structural gap；只有某个重大范围否则几乎分不到生成预算时才报告。
还能进一步细分不是缺口，也不要求 judge 命名要添加的 taxonomy。
同一状态下两次调用的输入相同、请求标签与 seed 不同，不把第一次结论传给第二次。
不同采样不保证 same-Base 判断在统计上独立，也不证明覆盖真实完整。

Repair 仅输出 `partition_principle / replacements`，不能夹带 additions。
增补使用独立的 `{"child": {...}}`，每次恰好一个。已 KEEP 的节点受保护：后续候选
若要求改动这些节点，标记 `protected_sibling_conflict`，不悄悄推翻已接受节点。
候选本身可在剩余 repair 预算内修复。所有变更后重置覆盖计数和请求阶段。

整树最后分别做 global overlap 和 global coverage（同样两次 NO 确认）：

- 最多一次 global repair/addition sweep：只修被指认的 leaves，并针对明确 gap 最多加一个 child。
- global addition 由 Base 选择现有 L1 或 root 作 parent；不能硬塞进预定领域。
- 新 L1 必须先通过 root sibling/coverage 复审，再完整执行普通 L2 build；不接受空分支。
- 受影响的 sibling set 必须重新通过 audit 和两次 coverage NO，然后重跑最终全局检查。
- 验证阶段不能开启第二次全局 sweep；仍有缺陷就是 unresolved。

## 有界但不按数量停止

默认 `--max-repairs 2`（一次局部 build 内累计，包括增补后的修复），
`--max-calls 128`（包括格式重试），`--max-children-per-parent 16`。
16 仅为异常循环的上限，不出现在模型的宽度目标里。达到上限且覆盖未完成时 unresolved；
初始 proposal 超过上限也 unresolved，不截断成 16。上限以内仍完全由合法性与两次 NO 决定停止。

精确 partition 循环、原样 repair，以及归一化后重复的 gap 描述会停止为 stalled。
无法检测所有语义改写循环，剩余宽度/调用预算为最终上限。调用预算耗尽退出 2，
不是 accepted。格式重试耗尽、加载错误等执行故障仍记录 failed。

## 输出格式与完整记录

每个动作先输出分析，再把唯一最终 JSON 放进 `<final_json>...</final_json>`。
分析可用普通文字、`<analysis>` 或 `<think>`；只检查结果前有非空文字，不声称验证了推理质量。
vLLM 在 `</final_json>` 停止且保留标记。

兼容 v2 的解析修复：指定 final box 优先于前面的草稿；没有 final 标签时，也接受
分析后的唯一完整 JSON code fence。损坏/重复的 final 标签、多份候选代码框或裸 JSON
不被猜测性提取。JSON 语法、重复 key、schema、id、pair 覆盖和修复权限仍严格校验。
失败默认额外 retry 2 次，用新 seed 并提供格式错误。思考与失败原文全部保存。

| 文件 | 内容 |
|---|---|
| `tree.json` | 仅全部验收通过时输出的最终两层树 |
| `partial_tree.json` | 中途树，可能不完整或 unresolved |
| `tree.md` | 可读树与执行状态 |
| `status.json` | 局部状态、当前 partition 的连续 NO 次数、全局状态、停止原因 |
| `manifest.json` | 模型/源码/prompt/参数 fingerprint、调用数、版本与退出状态 |
| `requests/<hash>/request.json` | 请求 label、system 和 task 输入 |
| `requests/<hash>/attempt_N.json` | 完整实际 prompt、raw_completion（含思考）、seed、结束原因、token 数、解析结果/错误及诊断 |

节点仍仅保留 `id / depth / name / scope / distinguishing_feature / parent_id / children`；
非叶节点另有 `partition_principle`。覆盖计数放在 status，不塞进 taxonomy。

## Linux 运行

```bash
cd /storage1/jiaxinh/Active/jinyuan/R-zero
git fetch origin
git switch main
git pull --ff-only
source env_rzero.sh

python -m methods.validity_rzero.scope_tree.run \
  --model Qwen/Qwen3-4B-Base \
  --gpu-id 0 \
  --local-files-only \
  --max-new-tokens 8192 \
  --max-model-len 32768 \
  --output-dir /engrfs/project/jiaxinh/jinyuan/R-zero-storage/rzero_runs/scope_tree_base_v3
```

模型也可以用同一 Base 的本地 snapshot 路径。默认采样为 temperature=0.6、top_p=0.95、
top_k=20、n=1、seed=42，显存比例 0.80。单个实例贯穿全程。
超出上下文预算会报错，不静默截断 sibling/leaf 输入。

**从 v1/v2 更新必须用新输出目录，不能对旧目录 --resume。**
同版本、同参数中断后可在同命令加 `--resume`；程序复核模型/源码/prompt/参数 fingerprint，
从历史请求重建树，复用同状态的成功结果。请求 epoch 和输入状态共同区分覆盖确认，
变更后的集合不能复用变更前的 NO。恢复不会重置已消耗的 retry、repair 或总调用预算。
改变参数（包括宽度上限）要用新目录。不会覆盖旧结果，也不允许多个进程同时写同目录。

## 验证范围

```bash
python -m unittest discover -s methods/validity_rzero/scope_tree/tests -v
python -m methods.validity_rzero.scope_tree.run --help
```

测试覆盖双 NO、NO/YES、增补后重置、粒度/readiness、接受节点保护、全 pair、预算、
stalled、全局修复/增补后的局部与全局复审、新 L1 展开、缓存恢复及原解析回归。
`tests/fixtures/root_propose_v1.json` 是真实历史 Base 原始输出；其余脚本化响应验证控制流。
这些 CPU 测试与历史回放不是 v3 GPU 生成效果，更不是下游多样性提升的证据。
