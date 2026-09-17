# OctoThinker pure R-Zero baseline

This uses the existing pure branch of `scripts/main.sh`, matching the historical
`qwen3_4b_rzero_8k_5round` schedule while replacing Qwen Base with
`OctoThinker/OctoThinker-3B-Hybrid-Base`. Both Questioner and Solver start from
the original base snapshot, then follow their separate evolving trajectories.
Do not point `OCTO_BASE_MODEL` at a validity, SFT judge or evolved checkpoint.

```bash
source env_rzero.sh
# Optional: original cached HF snapshot (not a trained checkpoint).
export OCTO_BASE_MODEL=/path/to/OctoThinker-3B-Hybrid-Base/snapshot
bash scripts/run_octothinker_base.sh
# Same experiment after interruption:
bash scripts/run_octothinker_base.sh --resume
```

Default name: `octothinker_3b_hybrid_base_rzero_8k_5round_v1` (override with
`OCTO_BASE_RZERO_NAME`). Fresh launches refuse existing outputs. Resume requires
existing state and the normal pipeline fingerprint/checkpoint validation.

- Five rounds, Questioner 5 steps and Solver 15 steps each.
- Questioner training GPUs 0/1, Solver feedback GPUs 2/3; generation and Solver
  training use all four GPUs. Candidate generation: 2000/GPU = 8000 per round.
- 4096 response tokens, original BLEU/frontier Questioner reward, original math
  Solver reward and 0.3–0.8 pseudo-label confidence filter.
- No validity gating, Terra replay, semantic novelty, SFT judge, negative-only,
  dynamic voting, token masking, domain curriculum or borrowed reward GPUs.
- The misleadingly named `VALIDITY_RZERO_MODEL_FAMILY=octothinker` enables only
  the already-implemented template/BOS adaptation across training and inference.
- W&B online for both training roles. Benchmark evaluation is separate; this
  entry passes `--no-eval` (training's required pseudo-label annotation remains).
- Checkpoint recovery and Solver internal-port isolation are engineering fixes,
  not changes to the original algorithm. Existing Compute2 Ray-temp and annotation
  worker port patches must also be retained in an isolated deployment snapshot.

The wrapper clears inherited training/method overrides; it keeps auth, scheduler,
HTTP/internal transport settings and annotation timeout settings. It neither
submits Slurm jobs nor stops other experiments. Queue on the requested node
through the normal Compute2 launcher, not directly on a login node.

The completed Octo validity experiment used 10000 candidates/round; this baseline
uses the historical Qwen budget of 8000. Report this distinction in comparisons.
