# Frozen Base 两层数学 scope 树

独立的离线 pilot。一个 frozen `Qwen/Qwen3-4B-Base`、一个单卡 vLLM 实例完成
`PROPOSE → AUDIT → REPAIR`。不训练模型，不调用外部 API，不接入或改变任何
Questioner/Solver reward、prompt、训练数据或正式 R-Zero 实验。

## 第一版协议

- Root 固定为 `Self-contained mathematical reasoning problems with well-defined, checkable answers.`
- 全局要求涵盖 mathematical objects、structures、representations、reasoning demands、abstraction。
- 深度固定为 2：L1 是宽领域；L2 是可直接分配给 Questioner 的具体出题范围。
- **宽度自适应，没有 5–8、2–4、总 leaf 数量等配额。** 模型选择紧凑、粒度合适且
  没有明显重大缺口的划分；不追求穷尽数学，也不为增加数量细分。
- 每个 parent 先生成共同的 `partition_principle`，再生成 children。
- 每次 sibling audit 检查全部 children，以及每个 unordered pair。
- 正常数学交叉不等于失败；只处理会导致大量重复生成的明显 overlap、nesting、near-duplicate。
- 修复保持 KEEP 节点原样，只改 REVISE/REMOVE 节点；有明确结构缺口时才允许补充节点。
- 如果共同划分原则本身失败，audit 必须拒绝全部 siblings，才允许整体更换原则。
- 每个 parent 默认最多 **2 次 semantic repair、3 次 audit**。原样返回或精确循环
  标为 `stalled`；修复预算耗尽标为 `repair_budget_exhausted`，不会假装通过。
- L1 通过后才展开 L2；各 L2 均通过后才做全树 leaf audit。
- Global audit 只报告高置信跨分支问题；最多一次 global repair sweep，只改被指认的 leaves。
  随后重新审查受影响的 sibling sets 和所有跨分支 leaves，不再扩展深度或无限修复。
- 每个节点保留 `id / depth / name / scope / distinguishing_feature / parent_id / children`；
  非叶 parent 另有 `partition_principle`。诊断状态放在单独文件，不塞进节点 schema。

Same-Base audit 是模型自身判断，不能当作独立证据证明分类完整或下游多样性提高。
树生成完成后仍需单独进行冻结 Questioner 的生成效果实验；本工具不启动该实验。

## 先分析，再输出可解析的 JSON

三个动作都明确要求模型先生成非空分析，然后输出唯一 final JSON：

```text
<analysis>
模型对当前任务的分析
</analysis>
<final_json>
{"partition_principle": "...", "children": [...]}
</final_json>
```

不同动作的 JSON schema 不同；`prompts.py` 中完整定义。使用 XML 风格边界包住 JSON，
避免 LaTeX `boxed` 与嵌套 JSON 大括号冲突。vLLM 在 `</final_json>` 停止并保留结束标记。
无隐藏 scratch-pad：实际生成的分析和最终文本均保留在 `raw_completion` 中。

严格检查标记、JSON 语法、重复 key、字段类型、节点 ID、全部 sibling pair 覆盖、
审查结论一致性和不可修改的 accepted siblings。解析/结构失败默认 **额外 retry 2 次**，
即每个请求最多 3 次。每次使用新的、可复现的 seed，并告知具体格式错误；重试不会
减少 children、截断 sibling set 或静默接受缺项。所有失败原文照样保存。

格式 retry 与语义 repair 是两个独立预算。总 inference attempts 默认上限 128，
包括 retry；这只是防止无限调用的预算，不是宽度或叶子数目标。

## Linux 运行

在一张空闲 GPU 上运行即可，不需要四卡或 Solver 服务。第一次试验使用新输出目录：

```bash
cd /storage1/jiaxinh/Active/jinyuan/R-zero
git pull --ff-only
source env_rzero.sh

python -m methods.validity_rzero.scope_tree.run \
  --model Qwen/Qwen3-4B-Base \
  --gpu-id 0 \
  --local-files-only \
  --output-dir /engrfs/project/jiaxinh/jinyuan/R-zero-storage/rzero_runs/scope_tree_base_v1
```

`--model` 也可以传同一个 Qwen3-4B-Base 的本地 Hugging Face snapshot 目录。
`--local-files-only` 要求模型已缓存；未缓存则报错，不会替换模型。
需要下载模型时去掉该参数，或先将 Base snapshot 准备好。

默认采样：`temperature=0.6, top_p=0.95, top_k=20, n=1, seed=42`；
每个请求最多生成 4096 tokens，模型上下文预算 16384 tokens；显存比例 0.80。
一个模型实例贯穿所有动作，不为每次审查重新加载。

### 中断后恢复

同一命令、同一参数，附加 `--resume`。程序校验模型/源码/prompt/采样/预算 fingerprint，
从已保存请求重建树，并复用成功结果，不重复调用已成功的请求。
中断或失败的 inference attempt 占用一次预算；重启后仅使用该请求剩余的 retry 次数。

如果是解析次数耗尽、semantic repair 耗尽、stalled 或总预算耗尽，`--resume` **不会重置预算**。
查看原文后，要改变 `--max-new-tokens`、`--max-model-len`、seed 或其他设置，请使用新输出目录。
本工具不会自动覆盖或删除旧结果。两个进程不能同时写同一输出目录。

### 结果和退出状态

| 文件 | 内容 |
|---|---|
| `tree.json` | **仅全部审查通过时产生**，最终两层树 |
| `tree.md` | 易读树，含 accepted/unresolved/failed 状态 |
| `partial_tree.json` | 每阶段保存的树，可能不完整或仍有问题 |
| `status.json` | 每个 parent 与 global audit 的停止状态 |
| `manifest.json` | 模型 snapshot、配置、代码 fingerprint、版本、节点数、调用量和错误 |
| `requests/<hash>/request.json` | 请求 label、system prompt、任务输入 |
| `requests/<hash>/attempt_N.json` | 每次实际尝试的 prompt、seed、原始分析和输出、解析结果或错误、耗时 |

模型接受整棵树时退出码为 `0`；审查未解决为 `2`；加载、解析重试耗尽、上下文/总调用
预算或运行故障为非零，并在 manifest 中记录 `failed`。失败后可能只有部分产物。
输入若超过上下文预算，明确报错；不会静默丢弃 leaves 来完成 global audit。

检查结果：

```bash
cat /engrfs/project/jiaxinh/jinyuan/R-zero-storage/rzero_runs/scope_tree_base_v1/manifest.json
cat /engrfs/project/jiaxinh/jinyuan/R-zero-storage/rzero_runs/scope_tree_base_v1/status.json
cat /engrfs/project/jiaxinh/jinyuan/R-zero-storage/rzero_runs/scope_tree_base_v1/tree.md
```

重试排障时，根据控制台的 `root/propose`、`1/audit/0`、`global/audit/1` 等 label，
找到对应 `request.json`，查看同目录 `attempt_N.json` 的 `raw_completion` 和 `error`。
这可以区分模型未闭合 JSON、遗漏 pair、输出被长度截断和语义修复未收敛。

## CPU 验证

无需 torch、vLLM、GPU 或外部 API：

```bash
python -m unittest discover -s methods/validity_rzero/scope_tree/tests -v
python -m methods.validity_rzero.scope_tree.run --help
```

测试覆盖真实状态机和结构化调用路径，包括解析 retry、持久化、缓存恢复、预算限制、
最后一次 repair 后的 audit、gap 驱动增补、accepted 节点不可变、global repair 后的
local/global re-audit。测试中的脚本化模型输出仅验证控制流程，**不是 4B 模型效果结果**。
