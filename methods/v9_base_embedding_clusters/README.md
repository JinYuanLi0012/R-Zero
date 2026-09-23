# V9 固定63题：Qwen3-4B-Base hidden-state embedding 聚类

只用 **Qwen/Qwen3-4B-Base**，不加载 Qwen3-Embedding、不训练、不调用 API、不重新抽样。

沿用 `methods/novelty_pair_diagnostic/backends.py` 的提取约定：原题无 chat template、无提示词、`add_special_tokens=False`；`AutoModel.last_hidden_state` 的有效 token 做 float32 masked mean，L2 normalize。Base 模型的此种特征不是专门训练的 embedding 模型输出。

## Linux 一次运行

在仓库根目录，用 Python 3.10+ 和可用 NVIDIA CUDA 环境：

```bash
python -m venv .venv-v9-base
source .venv-v9-base/bin/activate
python -m pip install -r methods/v9_base_embedding_clusters/requirements.txt
python methods/v9_base_embedding_clusters/run.py \
  --output methods/v9_base_embedding_clusters/results_d050 \
  --distance-threshold 0.5 \
  --device cuda --dtype bfloat16 --batch-size 4
```

默认下载的模型名固定为 `Qwen/Qwen3-4B-Base`；运行前将 HF revision 解析为 commit，并用同一 commit 加载 tokenizer 和模型。可通过 `--revision COMMIT` 固定复跑版本。若服务器已有这个 Base checkpoint：

```bash
python methods/v9_base_embedding_clusters/run.py \
  --model-path /path/to/Qwen3-4B-Base \
  --output methods/v9_base_embedding_clusters/results_local \
  --distance-threshold 0.5 --batch-size 4
```

本地 checkpoint 记录配置、分词器和权重的 SHA256；检查 Qwen3 4B 架构，但模型训练身份需由本地目录提供者保证。不得换成 instruct 或 embedding checkpoint。

若已有训练环境，可直接在该环境安装缺少的依赖，无需重装 PyTorch。默认使用 SDPA，无需 flash-attn。CUDA/PyTorch 安装需与服务器匹配。显存不足先用 `--batch-size 1`；不支持 BF16 的 GPU 用 `--dtype float16`。CPU 可用 `--device cpu --dtype float32 --batch-size 1`，需要足够内存且较慢。输入超过8192 token或模型上下文会报错，不静默截断；63题原文保持不变。

## 如何得出簇数

余弦距离 `1 - cosine`，average-linkage agglomerative clustering，`n_clusters=None`；阈值决定簇数，没有指定必须是几个簇。默认距离阈值0.5只是未校准的诊断设置，并非 Base embedding 的已验证语义阈值，也不与 BLEU 0.5 等价。距离阈值越小，划分通常越细；不能以簇数少就断言更正确。

程序打印 `N`、`K`、最大簇数量/占比和已有 BLEU 的22簇基线。每次使用新输出目录，防止覆盖结果。

保存向量后，可不加载模型、不联网，只改变聚类阈值：

```bash
python methods/v9_base_embedding_clusters/run.py \
  --reuse-embeddings methods/v9_base_embedding_clusters/results_d050 \
  --output methods/v9_base_embedding_clusters/results_d020 \
  --distance-threshold 0.2
```

复用前检查样本、模型、pooling、向量文件哈希。改变阈值的结果需明确报告阈值，不按理想簇数挑选后声称预先设定。

## 输出

- `summary.json`：簇数、每簇数量/占比与成员ID。
- `cluster_sizes.csv`：每簇数量/占比表。
- `clusters_original_questions.txt`：逐簇完整原题，正文保持空格、换行、公式不变，仅增加展示标题。
- `mapping.jsonl`：每题 embedding 簇、已有BLEU簇、原始行号、完整原文。
- `embeddings.npy`、`cosine_distance.npy`：63条向量及距离矩阵，输入顺序按原始行号升序。
- `manifest.json`：真实模型版本、依赖版本、pooling、长度、设备、精度、样本/代码/向量哈希。

## 固定数据和限制

`data/sample_63.jsonl` 与已完成的63题BLEU诊断逐字节一致，SHA256 `ce1a220b41a221d27a68efb0786e7d56f8ddad8654c72d10d29cd654da42a17f`。

它来自用户指定 `v9_top5_original_questions.txt` 第1簇“贪心递推：下一项取满足条件的最小整数”的1,874条成员；对应完整数据5,922条中的200条比例，`round(200*1874/5922)=63`。Python `random.Random(20260922).sample(range(1874),63)` 无放回；按原始行号升序，未去重或改题。完整源文件不需要传到Linux；输入原题已随代码提交。来源文件哈希见 `data/source_manifest.json`，其中Mac路径仅为历史来源，不是运行依赖。V9称谓来自文件名/用户标注。

这是只在63题上聚类，且原骨架内含互素、平方和、整除等不同约束，不能把整个骨架视为同一具体练习的金标准，也不能仅以合并更多认定模型优于BLEU。结果不还原训练batch奖励。

## 验证

```bash
python -m unittest discover -s methods/v9_base_embedding_clusters -p 'test_*.py' -v
```

CPU测试覆盖固定样本、BLEU映射一致性、真实PyTorch池化/掩码/异常向量、余弦距离和阈值聚类、完整原文导出、缓存复用/篡改拒绝。合成向量用于测试，不是模型实验结果；完整4B权重与GPU运行由Linux执行。

官方模型：[Qwen3-4B-Base](https://huggingface.co/Qwen/Qwen3-4B-Base)。
