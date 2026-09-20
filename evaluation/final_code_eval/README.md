# code eval final (code-eval-final-v1)

Main-table code completion for Qwen3-4B-Base, OctoThinker-3B-Hybrid-Base, and all
of their Solver checkpoints. Use `evaluation/code_batch/run_final.sh` with
`evaluation/code_batch/manifests/qwen_octo_42_final.json`; see the batch README.

## Fixed shared protocol

- HumanEval+ v0.1.10 (164 tasks), MBPP+ v0.2.0 (378 tasks).
- The existing pinned EvalPlus commit, data preparation and scorer in code_eval
  are reused unchanged. Full base+extended tests; greedy pass@1, one sample/task.
- Official prompt stripped then one newline, directly continued; no system/user/
  assistant wrapper, no CoT instruction, no training chat template.
- Official per-benchmark direct-completion text stops, identical across families.
- Concatenate the official prompt and completion, then official sanitizer. No
  last-code-block heuristic and no selection based on hidden test outcomes.
- Defaults: BF16, temperature=0, top_p=1, seed=42, output=4096 tokens,
  context=16384, batch=32, TP=1. Same settings for all models in a batch.
- Native tokenizer with add_special_tokens=True; Qwen has no BOS, Octo must have
  exactly one leading Llama BOS. Unexpected special-token settings fail loudly.
  Native EOS is validated and supplied as a stop token. Inputs use explicit
  prompt_token_ids so the engine cannot add BOS a second time.
- `generation_config="vllm"` prevents checkpoint-specific generation defaults
  from changing the shared sampling settings.

The completion prompt, text stops and scoring match the first code evaluation
implementation. This is **not a promise of bit-identical old scores**: the old
Qwen run used TP=2, the queue uses TP=1, and final explicitly disables checkpoint
sampling defaults. Nor is this an exact reproduction of SmolLM3's Lighteval run.
The old and matched executables remain unchanged for historical reproduction.

## Provenance and resume

HF model IDs resolve to an immutable revision before loading; the revision is
saved and reused on resume. Local checkpoint identity records filenames, sizes
and modification times (not full weight hashes). Config includes the final
protocol, implementation hash and judge environment; rendered tasks include
actual input token IDs. A changed config cannot reuse existing outputs silently.
Remote HF revision resolution on the first run requires Hub access. The pinned
revision's model files may then be loaded from the normal HF cache.

Existing CPU scorer behavior and adaptive EvalPlus timeouts are preserved. The
`--timeout` worker argument is retained for interface compatibility; it is not
an override of EvalPlus's adaptive limits. No GPU generation was performed during
implementation testing; Linux inference is required to obtain the final scores.

## Tests

```bash
python -m unittest discover -s evaluation/final_code_eval/tests -v
python -m unittest discover -s evaluation/code_batch/tests -v
python -m unittest discover -s evaluation/code_eval/tests -v
```
