# Frozen Base scope tree v4：一次调用，一个答案

同一个 frozen Qwen3-4B-Base，单卡离线构建两层出题范围。不修改训练系统。

模型只输出分析和一个 `<box>`。程序只解析框内文本，不要求 JSON、字段记录、
完整 pair 表格或多个布尔值。分析原文保留，不严格校验分析标签，不宣称验证了 CoT 质量。

| 调用 | 框内答案 |
|---|---|
| 确定划分原则 | 一句原则 |
| 提议一个节点 | 一段简短的数学范围描述 |
| 检查候选是否适合 | YES 或 NO |
| 是否还有重大缺口 | NONE，或一段缺口描述 |
| 修复一个被拒候选 | 一段替代描述 |
| 全树最终验收 | YES 或 NO |

```text
<analysis>
分析当前范围、已有节点及区别……
</analysis>
<box>
一个节点的完整简短描述。
</box>
```

## 管线

1. 为 parent 单独生成一个划分原则。
2. 一次只提议一个候选；一次整体判断其父范围归属、共同划分轴、粒度、与所有已接受
   siblings 的区别，以及 L2 能否支持多种非平凡题。具体理由放在分析中，框内只有 YES/NO。
3. YES 才添加；NO 最多修复该候选两次，每次重审。修复获得上一判断的完整原文作为反馈。
   已接受节点不改动；重复候选先尝试修复，修复循环原样返回则 stalled。
4. 添加后独立判断覆盖。只有同一集合连续两次 NONE 才冻结；任一次描述缺口便新增一个候选。
   两次输入不包含前一次 verdict，使用不同请求/seed；不同采样不保证统计独立。
5. Root 完成后逐个展开 L1 的 L2，深度固定为 2。
6. 整树做一次整体验收，检查重大缺口、跨分支重复和出题能力。NO 时保存 unresolved，
   理由在该请求的原始分析中；不再追加多层全局修复、路由与重新优化循环。

候选通过后程序就拿回控制权。默认每个 parent 最多 16 个节点只是异常上限，
在开始下一次候选生成前检查，不是让模型凑够 16。达到上限但没有两次 NONE 则 unresolved。
局部 repair 默认每个候选最多 2 次；重复缺口/重复修复停止；总调用上限默认 256
（拆为单次判断后调用数增加，包括格式 retry）。宽度和最终 taxonomy 仍由模型决定。

保留竞赛数学任务定义、non-trivial/self-contained/checkable、原 Questioner 领域举例及
“fewer than 30% of advanced high-school students”的生成目标；后者不是已校准的测量。
初等对象不排除，但 routine-only 题型不适合；节点应覆盖父范围的真正子范围，不能复述全局任务。
同模型审查仍可能误判；简化协议并不保证树质量或下游多样性改善。

## Base 输入与解析

使用普通文本续写输入，末尾预填 `<analysis>`，不再依赖 tokenizer 的聊天模板。
共享任务定义、当前小任务和两段输出示意都在输入中，模型只需继续回答当前一个问题。
预填开头属于 `rendered_prompt`；`raw_completion` 始终只保存模型真实输出，不伪造思考。
在 `</box>` 或常见反斜线关闭形式处停止，保留关闭标记。默认生成上限仍为 8192，
上下文为 32768；不是靠增加单次长度解决不停枚举。

只有唯一完整非空的 box 才解析成功；YES/NO 判断不接受额外解释，描述任务不接受裸 verdict。
分析标签不规整不影响有效 box。缺失框、多个框或无效判定默认额外 retry 2 次，失败原文照存。
不继续维护旧 JSON/字段协议，源码及 prompt fingerprint 已更新，旧目录不能 resume。

程序建立 ID、父子关系和深度，节点的完整框内描述作为 `scope`（`name` 也直接用该描述），
不拆出或要求模型另填 distinguishing_feature。存储仍为 JSON：

| 文件 | 内容 |
|---|---|
| `tree.json` | 仅全部验收通过才发布 |
| `partial_tree.json`、`tree.md` | 中间树、可读范围与状态 |
| `status.json` | 各 parent 状态、连续 NONE 次数、全局状态 |
| `manifest.json` | 模型、版本、源码 fingerprint、预算、调用量、结果 |
| `requests/<hash>/request.json` | 本次小任务及公共上下文 |
| `requests/<hash>/attempt_N.json` | 真实完整输出、实际输入、seed、结束原因、box_answer 或错误 |

调用预算、节点上限、语义修复或验收未通过：unresolved，退出 2。模型加载或格式重试耗尽：
failed，非零退出。均不会发布最终 tree.json。相同代码/模型/参数可 --resume，复用成功的
同状态请求并保留已耗预算；更改参数或版本必须用新目录。

## Linux

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
  --output-dir /engrfs/project/jiaxinh/jinyuan/R-zero-storage/rzero_runs/scope_tree_base_v4
```

不要对 v3.1 目录使用 --resume。默认 temperature=0.6、top_p=0.95、top_k=20，单模型实例。
输入过长明确报错，不截断已有范围。

## 验证

```bash
python -m unittest discover -s methods/validity_rzero/scope_tree/tests -v
python -m methods.validity_rzero.scope_tree.run --help
```

测试集中验证 box 边界、单答案类型、增量添加、双 NONE 与重置、候选修复及已接受节点保护、
循环与预算、全局否决、原文保存和恢复，以及普通续写/停止标记。旧字段协议测试已随协议删除。
这些是 CPU 控制流测试，不是 v4 GPU 生成质量验证；历史失败 fixture 仅留作调查记录。
