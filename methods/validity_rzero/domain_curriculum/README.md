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
