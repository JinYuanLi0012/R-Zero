# Code evaluation: HumanEval+, MBPP+, LiveCodeBench

Independent evaluation of any merged Hugging Face Solver checkpoint, including
Qwen3-4B-Base, original R-Zero, and OCNR. No training or math-evaluation changes.
Generation uses your existing R-Zero/vLLM environment. Official CPU scorers run
in a separate virtual environment; no judge model or API key is required.

## Linux: install once

From the repository root, with the working R-Zero environment activated:

```bash
git pull --ff-only origin main
export STORAGE_PATH=/your/storage
bash evaluation/code_eval/setup.sh
```

Setup needs Python 3.10+ (with current security patches), Git, and network access.
The first LiveCodeBench preparation downloads several GB of cached data/test cases;
allow disk space and time for this even though only 880 questions are generated.
In the local data check, the HF cache occupied about 8.3 GB and one prepared run
about 8.8 GB, mostly decoded judge inputs. Reserve at least 20 GB for the first
run, plus models and subsequent output directories. Preparation decodes one task
at a time; official scoring still needs enough RAM for the full judge-input list
and its worker processes.
It installs only the CPU import dependencies in `$STORAGE_PATH/code_eval_tools/venv`
and checks out both official tools at the commits in `versions.json`. It does not
pip-install their optional inference backends or modify your training environment.
Set `CODE_EVAL_SETUP_PYTHON=/path/to/python3.11` if necessary.
`CODE_EVAL_TOOLS=/another/path` overrides the tools directory everywhere.

## Evaluate all three

```bash
CUDA_VISIBLE_DEVICES=0 bash evaluation/code_eval/run.sh \
  --model /your/storage/models/solver_checkpoint/huggingface \
  --output "$STORAGE_PATH/code_eval/solver_checkpoint"
```

Use the **merged model directory containing weights**, not an FSDP shard directory.
An HF model ID also works, e.g. `--model Qwen/Qwen3-4B-Base`; use `--revision`
with a fixed HF commit when you want to pin the downloaded base model.
`CODE_EVAL_PYTHON=/path/to/rzero-env/bin/python` selects the GPU Python explicitly.

Defaults: all three datasets, one greedy completion per task, BF16, TP=1,
4096 output tokens, 16384 total context tokens, 32 questions per generation batch,
GPU memory utilization 0.85, seed 42, 8 CPU judge workers. LCB uses its official
6-second per-test timeout. EvalPlus keeps its official reference-time-based limits.
No silent question truncation: a prompt that cannot fit with the full output budget
stops the run and reports the required size. `length_limited_count` reports answers
that hit the output limit, so a short generation budget is visible in the results.

For two-GPU tensor parallel inference, for example:

```bash
CUDA_VISIBLE_DEVICES=0,1 bash evaluation/code_eval/run.sh \
  --model /path/to/merged_solver \
  --output "$STORAGE_PATH/code_eval/solver_tp2" \
  --tp 2 --max-model-len 16384 --max-new-tokens 4096
```

The launcher prepares data, loads the model once for the three datasets, releases
the GPU process, then scores the generated programs. Official judges execute Python
code; use an isolated Linux evaluation job/container without credentials or sensitive
mounts. A Python venv separates dependencies, not operating-system access.

## Exact evaluation protocol

| Dataset | Pinned data | Tasks | Reported result |
|---|---|---:|---|
| HumanEval+ | EvalPlus HumanEvalPlus v0.1.10 | 164 | pass@1 on base **and** extra tests |
| MBPP+ | EvalPlus MbppPlus v0.2.0 | 378 | pass@1 on base **and** extra tests |
| LiveCodeBench | `code_generation_lite`, `release_v5` | 880 | official code-generation pass@1 |

The runner requires these counts. It does not use `release_latest`, shortened
EvalPlus tests, retries after feedback, majority voting, or self-repair. One sample
per problem means pass@1 is the fraction of problems passing all required tests.
All three scores are reported separately; no math/code mixed average is invented.

**Default `--prompt-style base` is explicit and constant across checkpoints:**

- HumanEval+/MBPP+: official task-prompt completion with EvalPlus's base stopping
  strings. Prepend the task prompt to the completion, then use the official
  `sanitize(..., entrypoint=...)`. HumanEval is zero-shot; MBPP uses the prompt
  supplied by EvalPlus. No chat template is inferred from checkpoint metadata.
- LiveCodeBench: official `get_base_model_question_template_answer`, which includes
  **one provided example**, selected for function-based vs stdin/stdout questions.
  Stop at the next `### Question`; use official GenericBase code extraction.

Optional `--prompt-style chat` requires a tokenizer chat template. EvalPlus uses a
request for a self-contained Python script in a code block. LCB uses its official
generic chat content, preserving starter code or stdin/stdout instructions. Both
use `add_generation_prompt=True, enable_thinking=False`; the latter only has an
effect on templates supporting that option. LCB uses official chat code extraction.
This chat mode is an explicit alternative protocol, not the default Base protocol;
do not mix prompt modes when comparing checkpoints. Always preserve the raw answers.

OCNR reports greedy pass@1 for these datasets in its Absolute Zero experiments.
It does not disclose all prompt and generation-budget details. This implementation
uses the published datasets/official scoring with the explicit choices above;
it does not claim identical prompts or scores to the unpublished OCNR code.

## Results and resume

`--output` contains:

- `summary.json`, `summary.csv`: per-benchmark pass@1 in percent (0–100).
- `config.json`: checkpoint identity, protocol, official commits and environment.
- Each dataset directory: `tasks.json`, exact `rendered_tasks.json`, `raw.json`,
  official-format `samples.jsonl` or `samples.json`, `official_results.json`,
  `summary.json`, and dataset/config fingerprints.
- LCB `judge_inputs.jsonl` is for the CPU scorer only. Hidden tests are never passed
  to vLLM. EvalPlus canonical answers/tests are likewise not included in prompts.

Rerun the **same command** to resume. Each completed generation batch is saved
atomically; completed datasets/scoring are reused. Missing, duplicate, or unexpected
task IDs fail rather than reducing the denominator. A changed checkpoint, dataset,
implementation or configuration requires a new output directory; local checkpoint
identity uses filenames, sizes and mtimes (not a full weight-content hash).

Stages can also run separately using the same arguments and output directory:

```bash
# Append one of these to the original command:
--stage prepare   # CPU only: download/cache data and create prompts
--stage generate  # GPU only: requires prepare first
--stage score     # CPU only: requires complete generation
```

`--datasets humaneval mbpp` selects just EvalPlus; `--datasets livecodebench`
selects just LCB. Use a new output directory if changing this selection. Lower
`--workers` for a small CPU allocation. Re-evaluating a model with different
generation limits, prompting, or test timeout should also use a new directory.

## Local checks

```bash
python -m unittest discover -s evaluation/code_eval/tests -v
```

These check task alignment, interrupted generation recovery, and result/config
integrity without loading a model. GPU inference and full benchmark scores must be
run on Linux; Mac checks do not establish model quality or Linux GPU compatibility.

Official sources:
[EvalPlus](https://github.com/evalplus/evalplus),
[LiveCodeBench](https://github.com/LiveCodeBench/LiveCodeBench).
