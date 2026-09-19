# Octo Base/Solver code evaluation with matching training templates

This is a new, opt-in entry. Existing `evaluation/code_eval/` files and their
default Base-completion protocol are unchanged, including resume fingerprints.
The new entry reuses their data preparation, resume loop, code extraction and
official CPU scoring, but supplies Octo-specific prompt rendering and token inputs.

## Linux commands

Activate the working R-Zero/vLLM environment and run from the repository root:

```bash
git pull --ff-only origin main
export STORAGE_PATH=/your/storage
# Only needed if the official CPU evaluator has not already been installed:
bash evaluation/code_eval/setup.sh
```

Trained Octo Solver (complete merged Hugging Face checkpoint, including tokenizer):

```bash
CUDA_VISIBLE_DEVICES=0 bash evaluation/octo_code_eval/run.sh \
  --model /path/to/octo_solver/huggingface \
  --output "$STORAGE_PATH/code_eval/octo_solver_v1_chat"
```

Original Octo Base, using **exactly the same prompt template and decoding settings**:

```bash
CUDA_VISIBLE_DEVICES=0 bash evaluation/octo_code_eval/run.sh \
  --model OctoThinker/OctoThinker-3B-Hybrid-Base \
  --base-model \
  --output "$STORAGE_PATH/code_eval/octo_base_chat"
```

A local original Base snapshot also works with `--base-model`. For an HF ID,
`--revision COMMIT` can pin the snapshot. The flag only permits supplying the
training template when the original Base has none. It does not change sampling
or the benchmark prompts. Do not use it to conceal a Solver checkpoint missing
its tokenizer files. A saved conflicting template is rejected even with this flag.

## Shared protocol

- Both use the exact `methods/validity_rl/octothinker_chat.jinja` used in Octo
  training: one `<|begin_of_text|>`, plain `system:`/`user:` roles as applicable,
  and `assistant:` before generation. These are the repository's experiment
  conventions, not a claim of an official Octo chat format.
- Solver must have that exact template saved. Base receives it in memory;
  no checkpoint/tokenizer file is modified. No template or mode is silently guessed.
- Code benchmark instructions replace the mathematical task instructions, while
  keeping the training role wrapper. All three datasets use the existing **chat**
  preparation and extraction path. HumanEval+/MBPP+ request complete Python code;
  LCB uses its generic code-task instructions, including function vs stdin/stdout
  requirements. Neither model uses the old completion/one-shot Base path here.
- Render once, encode with `add_special_tokens=False`, require exactly one leading
  BOS, then pass `prompt_token_ids` to vLLM. Length accounting uses those same IDs.
- Both default to one greedy completion, 4096 output tokens, 16384 total context,
  seed 42, BF16, TP=1, batch size 32 and GPU memory utilization 0.85. EOS comes
  from the tokenizer. Per-checkpoint `generation_config` sampling overrides are
  disabled. The plain training template has no `enable_thinking` switch.
- Same official EvalPlus and LCB scoring and pinned data: 164 HumanEval+, 378
  MBPP+, 880 LiveCodeBench v5 tasks. No judge-model API is required.

Keep all CLI generation and scoring settings identical between Base and Solver.
`--tp 2` with `CUDA_VISIBLE_DEVICES=0,1` enables two-GPU inference. The old
code-completion results are a different protocol and should not be mixed into this
comparison. Give this new entry new output directories.

## Results, stages, and checks

Outputs include `summary.json`/`summary.csv`, raw answers, official scores,
`tokenizer_protocol.json`, and exact rendered prompts **and token IDs** per task.
`config.json` records the template content/hash and implementation fingerprint.
Changed templates or settings cannot silently resume an existing run.

The same command resumes completed batches and datasets. Optional
`--stage prepare`, `--stage generate`, `--stage score`, `--datasets humaneval mbpp`,
`--workers`, `--max-new-tokens` and `--max-model-len` work as in the old entry.
Data preparation runs on CPU; generation uses the active vLLM Python; official
program execution runs on Linux in the separate judge environment. See the
[shared setup and resource notes](../code_eval/README.md) for LCB disk/RAM costs.

```bash
python -m unittest discover -s evaluation/octo_code_eval/tests -v
```

The CPU tests verify matched Base/Solver inputs, single BOS, explicit-token
delivery to the inference interface, and rejection of conflicting templates or
context overflow. They do not establish GPU compatibility or benchmark scores.
