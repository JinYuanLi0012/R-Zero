# Matched code evaluation (Qwen3-4B-Base / OctoThinker Hybrid)

Use `evaluation/code_batch/run_matched.sh` for the shared multi-GPU queue, or
`bash evaluation/matched_code_eval/run.sh --family qwen --model MODEL --output OUTPUT --datasets humaneval mbpp`.
Use `--family octo` for Octo. Single-model `--base-model` records provenance only;
Base and Solver always use the same input processing. Batch `--base-model ID`
additionally permits a Hugging Face ID instead of a local checkpoint.

## Protocol and training audit

`verl/utils/dataset.py::_build_messages` expands `solver_format` to system + user.
`scripts/solver_train.sh`, `methods/ocnr/run.py`, and `methods/r_diverse/run.py`
use that solver format. The new protocol replaces the math system instruction
(reasoning + boxed answer) with a shared programming instruction (reasoning +
complete Python solution in a fenced block), with the official problem as user.
It does not include boxed/INVALID/math requirements. Some validity/terra branches
use a different task-specific user-only prompt; this is one fixed cross-domain
code protocol, not a claim to reproduce every task-specific training prompt.

Both families receive exactly the same system/user text. Only the chat template
and tokenizer differ:

* Qwen: pinned tokenizer template from Qwen/Qwen3-4B-Base revision
  `906bfd4b4dc7f14ee4320094d8b41684abff8539`, saved as `qwen_training.jinja`.
  No BOS; final prefix `<|im_start|>assistant\n`; EOS `<|endoftext|>`.
* Octo: `methods/validity_rl/octothinker_chat.jinja`, as installed by the training
  tokenizer setup; one `<|begin_of_text|>`; final prefix `assistant:\n`;
  EOS `<|end_of_text|>`.

Like RLHFDataset, apply_chat_template has add_generation_prompt=True with no
`enable_thinking` argument. No artificial empty think block is inserted, and no
special reasoning prefill is added. Encode uses add_special_tokens=False;
vLLM receives prompt_token_ids, avoiding a second BOS. The same canonical template
is assigned in memory for Base/Solver if absent; a conflicting saved template or
unexpected BOS/EOS fails explicitly rather than silently changing protocol.
Merged checkpoint tokenizers must therefore retain the training special tokens.

Generation: greedy, one sample, 4096 output tokens, context 16384, BF16, seed 42,
no textual stop strings, tokenizer EOS, generation_config='vllm' to avoid checkpoint
sampling defaults. The legacy CPU worker prepares official data and scores outputs
using its shared chat extraction path for both families: EvalPlus sanitize + full
plus tests; LCB official chat extraction + pass@1. Hidden tests are never inputs.
Default single-model datasets include LCB; batch runs only HumanEval+ and MBPP+.

`rendered_tasks.json` records actual messages, rendered text and input token IDs;
`config.json` records template, system instruction and generation protocol.
`tasks.json` is the legacy prepared source, not the final model input. Templates
and implementation hashes protect resume. Use a new output directory when changing
protocol. Legacy entry points and their original defaults remain available.

Local verification compares actual Qwen/Octo tokenizer results with the training
API sequence and save/reloaded tokenizer results. It does not validate remote
checkpoint files, CUDA generation or Linux scoring.
