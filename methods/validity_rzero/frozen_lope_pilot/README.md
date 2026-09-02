# Frozen Questioner LOPE perturbation test

This generation-only paired experiment tests whether a low-perplexity random
Lorem prefix broadens the output support of the frozen Semantic-MC Round-2
Questioner. It does not train, call the Solver, change rewards, or enter the
R-Zero pipeline.

## Fixed design

- Frozen checkpoint: `qwen3_4b_validity_rzero_semantic_mc_4gpu_v1_questioner_v2/global_step_5/actor/huggingface`.
- `fixed`: 8,000 requests with the original Questioner prompt.
- `lope`: 8,000 requests with an independent python-lorem-compatible prefix, the fixed
  boundary `Follow the task instruction below.`, then the original prompt.
- Each Lorem target length is sampled uniformly from 100 through 300 Qwen
  tokenizer tokens and is checked to have exactly that many tokens.
- Paired conditions use the same per-request generation seed and identical
  temperature, top-p, max-new-token, stop-token, chat-template, and parser
  settings.
- Primary metric: numeric-normalized repeated-template share.
- Secondary metrics: surface duplicate share, Top-5 normalized-template mass,
  and parsed-question success rate.

Duplicate metrics use successfully parsed questions as their denominator.
Surface normalization lowercases and collapses whitespace only. Numeric
template normalization additionally replaces `\d+(\.\d+)?` with `<NUM>`.
A family member counts as repeated when its normalized key occurs at least
twice.

## Linux command

After pulling the commit and sourcing `env_rzero.sh`:

```bash
python methods/validity_rzero/frozen_lope_pilot/run_frozen_lope_pilot.py \
  --output-dir /engrfs/project/jiaxinh/jinyuan/R-zero-storage/rzero_runs/frozen_questioner_lope_semantic_mc_r2_v1 \
  --local-files-only
```

The model path, 8,000 requests per condition, seeds, Lorem token range, and
decoding settings have experiment defaults. Use `--gpu-id` only to select the
single GPU used by this isolated offline generation.

The method vendors python-lorem 1.3.0.post3's exact 63-word pool and `get_word`
shuffle behavior, so the existing R-Zero environment needs no new package.

## Artifacts

- `pilot_generations.jsonl`: all 16,000 requests with condition, paired
  generation seed, perturbation seed/text/token count, raw completion, parsed
  question, prompt hash, token counts, and finish reason. Control perturbation
  fields are null.
- `pilot_manifest.json`: immutable model/prompt/config/version hashes and the
  aggregate metrics.
- `pilot_report.md`: the requested P0/PLOPE comparison table and Top-5
  normalized templates.
