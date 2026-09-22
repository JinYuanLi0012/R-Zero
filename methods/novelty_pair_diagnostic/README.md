# R-Zero novelty 题对诊断

比较 whitespace BLEU、**Qwen3-4B-Base 本身**的 mean-pooled final hidden states、同一 frozen base 的 SAME_TYPE/DIFFERENT judge。无训练、无 validity 筛选、无 K=8 gate；此处不预设任何方法胜负。正类为 SAME_TYPE（同一个具体练习的变体）。

## 数据来源与固定协议

首选原始 `analysis_results/validity_rl_terra_dataset_v1/sampled_questions.jsonl`（也支持 `.jsonl.gz`），只选其 `split == "train"`。它包含 2,300 条中的 **2,000 条 train：v1–v5 各 400 条**；其余 300 validation 不使用。

原始准备代码是 `methods/validity_rl_terra_dataset/prepare.py`：从 `jinyuan222/qwen3_4b_fullrun_authorsettings_solver_v1` … `v5` 的**实际 Solver 训练集**抽样，不是未过滤候选池。原字段为 `problem`，导出字段为 `id/question/round/split/source_row_index/question_hash`。上游固定 seed=42，先全局去重（删除 30 个重复出现记录），每轮抽 460 条，分成 400 train + 60 validation。原始来源 revision 见本目录 `source_provenance.json`。

本次在 Mac 找到旧发布归档 `hf_dataset_publish/audit/sampled_questions.jsonl.gz`，确认五轮各 400 train；后来的 1,993 条题面与该归档全部一致。此前少的 7 条是在答案核验时被排除，本实验使用原始归档，因此保留它们。不使用 1,943 clean、1,546 修复配对、1,273 Solver 标签版本，也不拼入 validation。代码不读取 validity/答案字段。

若服务器原始文件缺失，可从旧 HF 数据集 `jinyuan222/rzero-validity-rl-terra-v1` 的 `audit/sampled_questions.jsonl.gz` 取回原始审计归档，或上传本次随交付提供的同名归档。不要重新从变化后的上游数据抽样来冒充原样本。只有确实仅有 1,993 原始题时，另设 config 的 `expected_questions=1993` 和 `source_kind="solver_training_sample_after_7_answer_verification_exclusions"`，并指向旧 `train.jsonl`；manifest 会报告实际数目，不能称为完整 2,000 题。

1. 每轮在所有不同原始 ID 的无序对中，以固定种子均匀无放回抽 200 对；总目标 1,000 对。不自配、不跨轮、不重复 ID 对。本实验不再按相同题面去重；相同文本的不同记录仍有各自来源。
2. **先随机抽全部题对，再拆分**。将每个抽样边连接的题目及全局空白归一化后相同文本合并成连接分量，固定 seed 打乱分量后贪心接近 20% calibration，其余 test。无需标签/分数，ID 和相同文本不跨 split；分量不能拆开，所以不是精确 200/800，也不保证逐轮比例。其他语义近似文本仍可能跨 split，这不是全语义去重。
3. 原始数据实测为 **201 calibration + 799 test**；逐轮 calibration/test 为 v1 28/172、v2 54/146、v3 51/149、v4 32/168、v5 36/164。manifest 记录实际数量、源文件 SHA256、采样种子、方向和组件大小。
4. API 独立参考默认沿用 `methods/validity_repair/pipeline.py` 的 Responses API 约定：`gpt-5.6-sol`、high、16,384 output tokens、严格 JSON schema。只传题目，不传 ID/轮次/validity/三种方法结果。要求共同数学设定、任务比较和理由；同学科、措辞相近或都无效不够。UNCERTAIN、解析失败、请求失败均保存，不转换成 DIFFERENT。参考标签也不是已人工确认的真值。
5. 两个阈值分别仅在 calibration 最大化 F1，分数 `>= threshold` 判正；并列选更高阈值。要求校准标签和对应分数完整、两类都有、至少 5 个正例（预设可配置）；不满足则停止校准并报告不足，**不从 test 补样或调阈值**。阈值写入后冻结。自然随机样本若同型太少，应报告不足，未来另立新协议，而非暗加困难/正例。
6. test 报告整体和逐轮混淆矩阵、FNR、FPR、precision、recall、F1、正负例和覆盖数。失败不是负类。缺项时仅报告明确标记的观测子集，不能做完整结论；不同方法缺项不同，子集也可能不同。分母为零记 NA，少于 20 个 test 正例提示不稳定。题对共享题目，不宣称独立同分布，也不提供独立样本假设的置信区间。

## 三种方法的准确含义

- **BLEU**：复现 `examples/reward_function/caller_penalty.py::_bleu_distance_matrix`（也与 `methods/ocnr/bleu.py` 一致）的单个非对角分数：`sentence_bleu([B.split()], A.split(), smoothing_function=SmoothingFunction().method1)`，NLTK 默认 1–4 gram 等权、brevity penalty，空白分词、不小写、不额外切数学符号。BLEU 原本有方向性；固定按原始 ID 升序令 A 为 hypothesis、B 为 reference，不平均两方向。原代码把这个方向复制到对称矩阵。本诊断保留相同题面的两个记录（短句 BLEU 也不强制为 1）。这里学习的是**题对分数阈值**，不是训练 batch 的 average-linkage 聚类或 cluster share 惩罚。
- **Embedding**：`AutoModel` 加载同一个 base checkpoint，冻结参数/eval；原题无 chat template、无添加特殊 token。用 final `last_hidden_state` 在 attention mask=1 处 float32 均值池化，L2 normalize，再做 cosine。每个被抽中题目的向量缓存，不下载 Qwen Embedding 模型。批量 padding 不参与平均；长题超过配置/模型上下文直接报错，不无声截断。记录 token 数、tokenizer revision、pooling、dtype 和模型身份。
- **Base judge**：直接导入仓库 `run_pair_judge_v2.build_prompt` 和 v3 的 `parse_response_v3/sampling_options`；使用原始文本 prompt，不套 chat template。默认 temperature=.6、top_p=.95、top_k=20、presence_penalty=1.5、max_tokens=1024、seed=42、boxed-label stop 并保留 stop 字符串。保存原始回答、finish_reason、解析错误。固定同一 A/B 方向；本诊断没有做双方向平均或随机参考面板。原 prompt 的“不明确选 DIFFERENT”措辞原样保留；独立 API 参考则允许 UNCERTAIN，这一差异是评估对象的一部分。

所有源码及导入协议文件有 SHA256；运行 manifest、数据、配置、模型身份变化会拒绝复用。Hub 模型在运行时解析成 commit SHA，embedding/judge 必须一致；建议提前固定 `base.revision`。本地 checkpoint 对权重及配置做文件哈希（会有读取成本）。运行版本记录在各 stage manifest。API 服务模型别名不能保证永远不变，保留服务原始响应中的模型字段供追溯。

## Linux 启动

使用现有 R-Zero Python/GPU 环境（包含支持 Qwen3 的 transformers、torch、vLLM、nltk、openai、huggingface_hub）。不要为此覆盖已有 CUDA/torch 环境；CPU 数据准备不需要模型包。先在仓库根目录运行：

```bash
cd /storage1/jiaxinh/Active/jinyuan/R-zero
git pull --ff-only origin main
export STORAGE_PATH=/storage1/jiaxinh/Active/jinyuan/R-zero-storage
export RZERO_SOURCE="$PWD/analysis_results/validity_rl_terra_dataset_v1/sampled_questions.jsonl"
# 若用恢复的压缩归档：export RZERO_SOURCE=/path/to/sampled_questions.jsonl.gz
export NOVELTY_CONFIG="$STORAGE_PATH/novelty_pairs_config.json"
mkdir -p "$STORAGE_PATH"
cp methods/novelty_pair_diagnostic/config.example.json "$NOVELTY_CONFIG"
# OPENAI_API_KEY 使用已有环境配置，不写入 config 或仓库。
python -m methods.novelty_pair_diagnostic.pipeline prepare --config "$NOVELTY_CONFIG"
```

`input/output` 支持环境变量；输入不能位于输出目录内。可在 config 添加 `source_manifest` 指向旧 `prepare_manifest.json`，完整嵌入上游来源信息。模型本地路径可改 `base.model`；embedding 和 judge 共用这个字段。所有结果写入 `$STORAGE_PATH/novelty_pairs_v1`。修改协议/参数时使用新输出目录，不能在已有结果上改配置。

准备阶段确认 2,000 题、1,000 对及 split 后，在 GPU allocation/tmux 中：

```bash
bash methods/novelty_pair_diagnostic/run.sh "$NOVELTY_CONFIG"
cat "$STORAGE_PATH/novelty_pairs_v1/report.md"
```

这个入口会调用付费 API 并运行真实模型。阶段顺序是 prepare → BLEU → reference → embedding → judge → calibrate → report；默认一个可见 GPU，judge 可在 config 设置 TP。要分阶段运行：

```bash
python -m methods.novelty_pair_diagnostic.pipeline bleu --config "$NOVELTY_CONFIG"
python -m methods.novelty_pair_diagnostic.pipeline reference --config "$NOVELTY_CONFIG"
python -m methods.novelty_pair_diagnostic.pipeline review-export --config "$NOVELTY_CONFIG"
python -m methods.novelty_pair_diagnostic.pipeline embedding --config "$NOVELTY_CONFIG"
python -m methods.novelty_pair_diagnostic.pipeline judge --config "$NOVELTY_CONFIG"
python -m methods.novelty_pair_diagnostic.pipeline calibrate --config "$NOVELTY_CONFIG"
python -m methods.novelty_pair_diagnostic.pipeline report --config "$NOVELTY_CONFIG"
```

重复同一命令会复用完整缓存。`reference` / `judge` 加 `--retry-failed` 才重新尝试不完整项（包括 UNCERTAIN），保存历史；API SDK 对传输错误另有最多两次自动重试。首次诊断建议保留失败率，再决定是否重试；若重试，所有失败项遵循同一规则，不挑着重标。GPU 执行错误/上下文溢出会停止，已保存的批次不丢失。不要并发写同一输出目录。

校准失败时一键入口仍生成 INCOMPLETE 报告并返回非零。`report` 随时可用以检查缺项；它不会自动调阈值。人工审核文件 `review.csv/jsonl` 不包含方法结果，有题目、参考理由和空白 human_label/human_reason 栏；默认只是审核导出，填写后不会自动覆盖 API 参考或冻结阈值，需明确另立人工 adjudication 版本。保留已有文件再重复 export，避免覆盖手工笔记。

主要输出：`manifest.json`、`questions.jsonl`、`pairs.jsonl`、各方法 `manifest.json/artifacts/`、`vectors/`、`review.csv/jsonl`、`thresholds.json`、`report.json/md`。不要提交这些输出、原始数据、凭据或权重。

## 检查范围

```bash
python -m unittest discover -s methods/novelty_pair_diagnostic/tests -v
```

测试包含真实 CPU PyTorch masked pooling、直接抽取原 BLEU 函数的数值回归、无重复/跨轮/自配对和 split 无泄漏、校准只能打开 calibration 标签、阈值冻结、指标/失败状态、API 请求盲化、缓存身份/篡改检查及 mock 报告。Mock 的完美指标只是合成测试断言，不是论文结果。Mac 不运行完整 GPU 或付费 API；Linux 仍需验证实际模型加载、显存、吞吐及服务模型访问权限。
