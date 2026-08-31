# Frozen Questioner history-context prompt pilot

This is a generation-only matched P0/P1 pilot. It asks whether three negative
references from the lambda-1 Round-4 archive steer one frozen Questioner away
from historical templates before any training-path change is attempted.

The two conditions use the same model, group count, rollout count, sampling
settings, and per-group request seeds:

- `P0_fixed_prompt`: the original fixed Questioner prompt.
- `P1_history_context`: the same system prompt plus three row-uniform negative
  references, with an explicit instruction to change both the primary
  mathematical object and core solution method.

Each prompt group has four rollouts. All four P1 rollouts in a group see the
same three references. Reference rows must be non-empty, `VALID`, and
`passed_rzero_filter=true`. Multiplicity in the archive is retained; only the
three row indices inside one group must be distinct.

This pilot does not train a model and does not call the semantic-MC treatment,
a validity judge, Solver frontier scoring, or Phase-B filtering.

## Linux command

After pulling the delivered commit and sourcing the normal environment:

```bash
python methods/validity_rzero/incontext_pilot/run_prompt_pilot.py \
  --output-dir /engrfs/project/jiaxinh/jinyuan/R-zero-storage/rzero_runs/incontext_prompt_pilot_r4_k3_512x4_v1 \
  --local-files-only
```

The checked-in defaults are the supplied paths:

```text
Questioner:
/engrfs/project/jiaxinh/jinyuan/R-zero-storage/models/qwen3_4b_validity_rzero_clean_formal_r10_initstep15_divlambda5_v1_questioner_v4/global_step_5/actor/huggingface

Archive:
/engrfs/project/jiaxinh/jinyuan/R-zero-storage/rzero_runs/qwen3_4b_validity_rzero_clean_formal_r10_initstep15_v1/datasets/round_4_phase_b.jsonl
```

The default archive row count is checked as 9,633. Use `--gpu-id` to select a
different single GPU. The default output is 512 prompt groups times four
rollouts, or 2,048 completions per condition and 4,096 total.

## Artifacts and checks

- `pilot_manifest.json`: immutable inputs, hashes, versions, settings, counts,
  runtime, and aggregate metrics.
- `pilot_groups.jsonl`: exact reference row indices/questions and paired prompt
  hashes/token counts for all 512 groups.
- `pilot_generations.jsonl`: all raw completions and parsed questions.
- `pilot_review_sample.jsonl`: 32 deterministically sampled groups with the
  three references and all four paired P0/P1 questions for compact manual QA.
- `pilot_report.md`: compact P0/P1 surface diagnostics and top template
  families.

Verify that the manifest reports:

```text
group_count = 512
rollouts_per_prompt = 4
expected_completions_per_condition = 2048
total_completions = 4096
paired_request_seeds = true
```

The normalized-template and 4-gram measurements are deliberately transparent
surface diagnostics. Inspect the raw paired generations before deciding
whether to run a validity/Solver-scored follow-up.
