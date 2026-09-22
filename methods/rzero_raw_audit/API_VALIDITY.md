# 为原始 1000 条记录追加 API validity

先完成原始采样与多数投票，得到 5 轮、每轮 200 条的 `all_rounds.jsonl`。
本入口读取全部记录，保留原字段与顺序，只追加 `api_*` 字段。不去重、不筛题、不修题，
也不重新生成题目或调用 Solver。无需 GPU。

复用 `methods/validity_rl_terra_dataset/annotate.py` 的
`rzero-validity-a-f-v1` prompt、schema、检查及 Responses API 调用，
与 validity repair 实验使用同一套题目判定标准；不执行 repair 或答案核验。
默认沿用该实验的 `gpt-5.6-sol`、high reasoning、16384 输出 token 上限、同步并发 16。
`--model` 等参数可以覆盖默认值，实际调用需要账户有该模型权限。

API 只接收匿名 ID 与题目，不接收轮次、checkpoint、Questioner 答案或多数投票结果。
`A → VALID`；`B–F → INVALID` 沿用历史严格二分类规则。
其中 F 是“无法可靠判断”，原始标签会保留并在汇总中单独计数，分析时可另行排除。
API 报错或未完整返回不会当作 INVALID，而是 `UNKNOWN`。

## 启动

在仓库及已有 Python 环境中执行；需要已安装支持 Responses API 的 `openai` 包。
`env_rzero.sh` 会在环境未设置 key 时读取已有 `tokens.json` 的 `openai` 字段。

```bash
cd /storage1/jiaxinh/Active/jinyuan/R-zero
git pull --ff-only
source env_rzero.sh

python -u -m methods.rzero_raw_audit.api_validity \
  --input /engrfs/project/jiaxinh/jinyuan/R-zero-storage/analysis_results/qwen3_4b_rzero_8k_5round_raw200_v1/all_rounds.jsonl \
  --output-dir /engrfs/project/jiaxinh/jinyuan/R-zero-storage/analysis_results/qwen3_4b_rzero_8k_5round_raw200_api_sol_v1 \
  --model gpt-5.6-sol \
  --reasoning-effort high \
  --concurrency 16
```

可先加 `--prepare-only` 检查条数并生成匿名输入，不调用 API；之后去掉该参数启动。
默认严格要求 5×200 条且 ID 唯一，输入不完整会在任何 API 调用前拒绝运行。
其他样本规模需明确指定 `--rounds` 和 `--per-round`。

中断或 API 失败后重复同一命令即可，已成功的判断从缓存读取，仅补未完成项。
每次运行默认每题最多尝试 3 次（SDK 自身可能另有重试），可用 `--max-attempts` 调整。
修改模型、输入、判定协议或代码后必须使用新输出目录；并发数可原地调整。
输出目录必须与输入目录分开。

## 输出与分析

- `round_1.jsonl` … `round_5.jsonl`：每轮 200 条，原多数投票字段全部保留。
- `all_rounds.jsonl`：全部 1000 条，附 `api_validity`、原始 `api_label`、
  `api_status`、`api_reason`、`api_confidence`、`api_invalid_type`、完整 `api_judgment`。
- `summary.json`、`report.md`：每轮 VALID / INVALID / UNKNOWN、valid 比例。
  JSON 另有 F 标签数、API 失败数、无法提取题目数。
- `unresolved.jsonl`：全部 UNKNOWN，便于排查。
- `artifacts/`：每题原始 API 返回、解析结果和历次错误，逐题落盘用于续跑。
- `manifest.json`、`blind_input.jsonl`、`id_mapping.json`：配置、实际判定输入及对应关系。

原生成解析失败但仍含完整 `<question>…</question>` 的记录可以继续做 validity，
实际判定文本保存在 `api_judged_question`，来源保存在 `api_question_source`。
若连题目文本也无法提取，仍保留该行，标记 `UNKNOWN / missing_question`，不编造题目。
因此文件始终有每轮 200 条，但成功获得 API 标签的条数可能更少。

`api_validity` 判断的是题目是否满足有效性要求，不代表多数投票答案已验证正确。
`valid_rate_among_judged` 的分母是 VALID+INVALID；`valid_fraction_all_rows` 的分母是该轮全部 200 条。

CPU 测试使用模拟 API，覆盖 1000 条合并、保留原多数票、重复题、缺题、失败重试、
不完整返回拒绝和缓存续跑；未在本地对这批真实题目调用付费 API。

```bash
python -m pytest -q methods/rzero_raw_audit/tests
```
