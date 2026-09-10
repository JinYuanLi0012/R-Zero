# Balanced domain Questioner (opt-in)

Enable `VALIDITY_RZERO_DOMAIN_MODE=balanced_v1` with
`VALIDITY_RZERO_DOMAIN_SEED=43`. Default `none` retains all existing paths and
resume fingerprints. Only validity-RZero reads the switch; pure R-Zero ignores it.
Use a new MODEL_ABBR. Mode and seed enter the run fingerprint, so old/new runs
cannot resume into each other.

The fixed outline has eight parent domains and 28 leaves (see core.py). Each
Questioner batch divides prompt slots equally across parents, then equally among
each parent's leaves. Remainders rotate each batch; a deterministic shuffle uses
the seed, round experiment name, and batch index. At 512 prompts, each parent has
64 prompts. Existing GRPO repeats each prompt four times with one uid, giving
256 questions per parent. We do not change grouping, advantages, reward, or KL.

The Questioner parquet schedule is written under its output directory as
`domain_prompts.parquet`, with one balanced batch per requested training step.
Sequential loading preserves the pre-shuffled batches and is checkpoint-resumable.
The same deterministic schedule is regenerated on resume. Prompt filtering is
disabled for this short fixed template so it cannot remove scheduled slots.
The original dummy math12k content was ignored by the Questioner template;
the new dataset contains domain paths instead, with unused empty answer labels.

Phase B builds one global plan for num_samples * QUESTION_NUM_SHARDS, then slices
it by shard index. Four shards of 2500 yield exactly 1250 requests per parent.
Both stages share the same system/user messages; only the original all-fields
sentence is replaced with a domain requirement. Output syntax and decoding stay
unchanged. Phase B stores `domain` even on malformed generations; evaluation and
mixed Solver data retain the label where the row survives. Questioner reward
logs emit domain, question, validity decision and final reward. Assigned domain
is metadata, not a verified classifier label.

Use the original K8/1 legacy reward, original initialization and 10% Terra replay
for the first comparison. Domain allocation applies to generated R-Zero questions,
not Terra. Filtering can change the domain proportions of the retained 90%; no
new filter, resampling, deduplication, domain judge, or reward is added. Novelty
references remain drawn from the whole batch, including other domains.

Start with `bash methods/validity_rzero/domain_curriculum/run_k8.sh` after sourcing
env_rzero.sh in a fresh shell. The script explicitly pins the original five-round
budget and initialization; it accepts `--resume` for this new run only.

## Matched box-filter comparison: global K8 versus parent-domain K4

Two new launchers preserve the original initialization, balanced prompts, five
rounds, Questioner 5 / Solver 15 steps, 10% Terra replay, legacy INVALID reward,
frontier, judge protocol and decoding:

```bash
# Control: independent global K8, one SAME_TYPE rejects
bash methods/validity_rzero/domain_curriculum/run_global_k8_latexonly.sh
# Treatment: independent parent-domain K4, one SAME_TYPE rejects
bash methods/validity_rzero/domain_curriculum/run_parent_k4_latexonly.sh
```

They use different MODEL_ABBR values. Run separately on the same four GPUs; append
`--resume` only when recovering that same new experiment.

`VALIDITY_RZERO_NOVELTY_SCOPE=global|parent_domain` defaults to global. In
parent_domain scope every candidate samples up to K nonself indices without
replacement from its assigned FIRST-LEVEL domain in the current generated batch.
The pool includes all parsed candidate questions of that parent across leaves
and GRPO groups, without text deduplication. It is not a shared panel. Like the
original global mode, malformed empty question rows are not comparison candidates.
Known full domain paths are required for every row, including malformed rows;
missing/misaligned/unknown metadata raises an error. The existing batch repeat,
reorder and reward metadata forwarding preserve alignment; scope uses assigned
metadata rather than classifying question text. Smaller pools use min(K, available).
Per-question domain logs include sampled_count, compared_count and same_count;
parse failures retain the existing retry/fail-open policy. Novelty still changes
only Questioner reward; no Phase B novelty filtering is added.

Both new launchers set `RZERO_QUESTION_BOX_FILTER=latex_only`. Its independent
default `legacy` preserves the old case-insensitive `box` substring rejection.
latex_only rejects a literal LaTeX `\boxed` command in the QUESTION (command
boundary required), while ordinary English box/boxes pass. The existing Chinese
proof-word and majority-answer `text` filters, and answer extraction, are unchanged.
`*_results.json.question_filter.json` records counts and every skipped question,
assigned domain, majority answer, consistency score and reason for these three
filters; it is not a full accounting of earlier parse/validity losses. The same
records are printed in evaluator logs. No new audit file is created in legacy mode.

Nondefault scope and box policy enter the pipeline fingerprint; global/legacy
contribute no new fields. Old runs (including the original domain global K8)
retain their old fingerprints. Changing either treatment on a run refuses resume.
The old run_k8.sh is unchanged. If setting flags manually, reset scope to global
and box filter to legacy before reproducing old experiments.
