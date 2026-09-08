# Frozen Base 两层数学 scope 树（v3.1 文本协议）

一个 frozen `Qwen/Qwen3-4B-Base`、一个单卡 vLLM 实例，离线构建数学出题范围。
不训练模型，不修改 Questioner/Solver 的训练、reward 或采样流程。

## v3 算法的问题空间

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

覆盖检查使用独立记录：

```text
HAS_MAJOR_GAP: NO
GAP: NONE
REASON: 当前范围没有重大遗漏的理由
```

YES 必须给出非空 structural gap；只有某个重大范围否则几乎分不到生成预算时才报告。
还能进一步细分不是缺口，也不要求 judge 命名要添加的 taxonomy。
同一状态下两次调用的输入相同、请求标签与 seed 不同，不把第一次结论传给第二次。
不同采样不保证 same-Base 判断在统计上独立，也不证明覆盖真实完整。

Repair 用 `PRINCIPLE` 和重复的 `REPLACE / ACTION` 记录；替换时附三个 family 字段，
删除时不附。增补只输出一次 `NAME / SCOPE / DISTINCTION`，每次恰好一个。已 KEEP 的节点受保护：后续候选
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

## 模型输出文本，程序保存 JSON

v3.1 不再要求 Base 生成嵌套 JSON。所有新 prompt 只要求：普通分析文字，然后一个
`<final>...</final>` 文本框。程序将字段记录映射为现有内部对象，再执行相同 schema
和语义流程校验，最终 `tree.json / manifest.json / attempt_N.json` 仍是标准 JSON。

PROPOSE 示例（占位符仅说明格式，不是预置 taxonomy）：

```text
模型先分析当前划分任务……
<final>
PRINCIPLE: 一个共同的划分原则
NAME: 第一个 family 名称
SCOPE: 这个 family 独有的数学对象、关系与约束
DISTINCTION: 沿该划分原则与兄弟节点的具体差别
NAME: 第二个 family 名称
SCOPE: 第二个 family 的数学范围
DISTINCTION: 第二个 family 的具体区别
</final>
```

| 动作 | 最终文本记录 |
|---|---|
| PROPOSE | `PRINCIPLE`，随后重复 `NAME / SCOPE / DISTINCTION` |
| SIBLING AUDIT | `PRINCIPLE_OK / PRINCIPLE_REASON`；每个节点 `CHILD / FIT / AXIS / BREADTH / READY（仅 L2） / ACTION / REASON`；每对 `PAIR / RELATION / REASON` |
| COVERAGE（局部/全局） | `HAS_MAJOR_GAP / GAP / REASON` |
| REPAIR | `PRINCIPLE`；每个目标 `REPLACE / ACTION`，ACTION=REPLACE 时附三个 family 字段，DELETE 时不附 |
| 局部增补 | 恰好一次 `NAME / SCOPE / DISTINCTION` |
| GLOBAL OVERLAP | 无问题用 `ISSUES: NONE`，否则重复 `PAIR / RELATION / REVISE / REASON` |
| 全局增补 | `PARENT` 选择目标父引用，随后一次三个 family 字段 |

标签按给定顺序顶格书写，每行 `LABEL: value`。布尔值严格为 YES/NO。
`PAIR` 的值恰好是两个用空格分隔的引用 ID。冒号、引号、竖线在普通字段值中保持原样；
需要换行时，每个续行缩进两个空格，续行中的 `NAME:` 等也只是内容。空行忽略，可分隔记录。
不猜测无缩进的续行、不接受重复字段或记录、不补造缺失原则、不静默删除额外字段或冲突 ID。
Coverage 为 NO 时 GAP 必须为 NONE；YES 必须给具体描述。所有完整 pair、readiness、
KEEP 一致性与接受节点保护继续生效。

输入也与存储对象解耦：用简洁的父范围、节点语义和必要引用 ID，不再把完整 parent 存储
对象摆在模型面前。完整竞赛要求保留在共享 system 上下文；root 的输入范围不再重复它。
`SCOPE` 不能照抄全局任务，`DISTINCTION` 不能重复 generic broad variation；judge 明确
检查实际范围描述，不能仅凭名字推断不存在的边界。这仍是模型审查，不保证识别所有语义退化。

模型原文始终完整保存，包括分析、草稿和失败结果。`has_nonempty_prefix` 仅记录最终框前
有无文字；前缀可能只是草稿 JSON，不代表验证了 CoT 的存在或质量。
vLLM 在 `</final>` 停止并保留标记。解析失败仍默认额外 retry 两次，不增加长度或次数。
错误指出文本行和缺失/重复字段；内部 schema 错误指出具体路径和 missing/extra 字段。

旧 `<final_json>` 和唯一 JSON code fence 仍可解析，保留旧回归兼容；新 prompt 不提供
协议选择。混用两类 final 框、损坏/重复边界和无边界裸 JSON 仍拒绝。
旧 JSON 中即使 `parent_id` 与上下文一致，也仍属于额外字段，不会自动删除。

| 文件 | 内容 |
|---|---|
| `tree.json` | 仅全部验收通过时输出的最终两层树 |
| `partial_tree.json` | 中途树，可能不完整或 unresolved |
| `tree.md` | 可读树与执行状态 |
| `status.json` | 局部状态、当前 partition 的连续 NO 次数、全局状态、停止原因 |
| `manifest.json` | 模型/源码/prompt/参数 fingerprint、调用数、版本与退出状态 |
| `requests/<hash>/request.json` | 请求 label、system 和 task 输入 |
| `requests/<hash>/attempt_N.json` | 完整实际 prompt、raw_completion（含思考）、seed、结束原因、token 数、程序组装的 parsed_json、错误及诊断 |

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
  --output-dir /engrfs/project/jiaxinh/jinyuan/R-zero-storage/rzero_runs/scope_tree_base_v3_1
```

模型也可以用同一 Base 的本地 snapshot 路径。默认采样为 temperature=0.6、top_p=0.95、
top_k=20、n=1、seed=42，显存比例 0.80。单个实例贯穿全程。
超出上下文预算会报错，不静默截断 sibling/leaf 输入。

**从 v1/v2/v3 更新到 v3.1 必须用新输出目录，不能对旧目录 --resume。**
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
`tests/fixtures/root_propose_v3.json` 保留第三版三次真实格式失败：缺少原则和额外字段
继续被拒绝。额外覆盖文本协议全动作、换行/分隔符、缺失与冲突字段、文本重试、完整流程
和兼容 JSON。测试中的文本重编码只是人工构造传输用例，不是新模型生成。
这些 CPU 测试与历史回放不是 v3.1 GPU 生成效果，更不是下游多样性提升的证据。
