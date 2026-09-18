# Nonmath batch evaluation

From the repository root in the activated evaluation environment:

```bash
export STORAGE_PATH=/engrfs/project/jiaxinh/jinyuan/R-zero-storage
python evaluation/evaluate_models.py --suite nonmath --gpu-ids 0,1,2,3 \
  /path/to/solver_v1 /path/to/solver_v2
```

Accepts any number of run directories or merged Hugging Face checkpoint directories.
Run directories select `global_step_15/actor/huggingface`, as in the math mode.
Add `--dry-run` to validate paths without launching models or writing outputs.

With exactly four GPU IDs (`--gpu-ids 0,1,2,3`), the first two GPUs run
independent TP=1 SuperGPQA replicas, each processing half the questions. The third
GPU runs BBEH and the fourth runs MMLU-Pro concurrently, also TP=1. Questions are
ordered by discipline then alternated across the two shards, balancing both total
question counts and the large Science/Engineering categories. This is data
parallel generation, not a TP=2 model. Prompts, token budgets, and scoring rules
stay unchanged; altered batching can still introduce normal numerical differences.
SuperGPQA's existing random fallback for unparseable answers also remains unchanged.

Shard records include question indices, counts, and a dataset fingerprint. Merging
requires matching fingerprints and complete, disjoint coverage, and computes
`100 * sum(correct) / sum(total)`, not the mean of rounded shard percentages.
A failed shard never produces a complete SuperGPQA score. Full responses are merged
in the original category/question order into `supergpqa_outputs.json`;
per-shard logs/responses are retained in `supergpqa_shard_0/` and
`supergpqa_shard_1/`. BBEH/MMLU-Pro retain their existing filenames.

With exactly three GPU IDs (for example `--gpu-ids 1,2,3`), each model runs
SuperGPQA on the first GPU, BBEH on the second, and MMLU-Pro on the third
concurrently, with TP=1 each. With GPU counts other than three or four, benchmarks run sequentially
using all selected GPUs for tensor parallelism. Models always run sequentially. This mode directly invokes the existing benchmark scripts;
it does not run the math evaluations or launch the Qwen3-32B judge.
The existing benchmark prompts and accuracy scoring are unchanged.

Results go to a new `$STORAGE_PATH/evaluation_batches/nonmath_<timestamp>` directory.
The terminal prints a summary table and locations of `summary.csv` and `summary.md`.
`ave_nonmath` is the unweighted mean of the three percentage scores, separate from
the seven-math-benchmark `ave`. Existing math batches remain intact.
Each completed model also receives scores and summaries under its exact checkpoint's
`evaluations/<batch-name>_<id>` directory. Raw responses and per-task logs remain in
the central batch directory; checkpoint metadata records their locations.

A failed task stops the batch after already-running tasks finish, preserves available scores/logs, and leaves the
average empty. Inspect the printed log path before starting another batch.
Compiler caches are isolated under `/tmp` by default (override with
`RECHECK_LOCAL_TMP_ROOT`); they are retained for diagnosis.

To display an existing batch summary without GPU work:

```bash
python evaluation/evaluate_models.py --summary-only /path/to/nonmath_batch
```

Omitting `--suite` preserves the original math-only behavior.

The new topology applies only to new launches. Do not pull/update code midway through
an older running batch: it starts fresh Python workers for subsequent checkpoints.
An existing three-GPU process does not automatically acquire the fourth GPU.
Start a new batch with four allocated, idle GPUs and only the checkpoints still needed.
