# OctoThinker Hybrid Base: four-GPU validity R-Zero

This is the original semantic-novelty-gate K8 / one-hit-rejection experiment,
with **all three roles** switched from Qwen to OctoThinker:

- Questioner: `OctoThinker/OctoThinker-3B-Hybrid-Base`, updated each round.
- Solver: OctoThinker validity GRPO `global_step_10`, updated each round.
- Semantic judge: frozen `OctoThinker/OctoThinker-3B-Hybrid-Base`, not the
  validity-trained checkpoint. Its existing plain-completion prompt, sampling,
  parser, retries, and GPU handoff remain unchanged. Model-native BOS/EOS apply.

Default: five new rounds, Questioner 5 updates / Solver 15 updates each round.
Nine validity votes, INVALID at >=5; fresh math votes 10 in Phase A / 9 in Phase B.
Questioner VALID reward is novelty * min(p, 1-p); INVALID retains the original
0.5 - invalid_votes/9 penalty. Novelty draws up to 8 other batch candidates and
rejects at one SAME_TYPE hit. Phase B generates 2500 candidates per GPU (10000
total), retains majority consistency 0.3–0.8, and mixes clean Terra **train**
rows at approximately 10% of the final dataset. Reward and task prompts are
unchanged; R-Zero math rows and Terra validity rows keep their separate prompts.
No negative-only, dynamic-vote, token-mask, domain curriculum, or automatic
benchmark evaluation is enabled.

## Run on Linux

In the original training environment, with four allocated A100s:

```bash
cd /storage1/jiaxinh/Active/jinyuan/R-zero
git pull --ff-only
git rev-parse --short HEAD
source env_rzero.sh
wandb login
bash methods/validity_rzero/run_octothinker.sh
```

GPU layout is unchanged: Questioner training 0,1; Solver services 2,3;
Phase-B generation and Solver training 0,1,2,3; frozen semantic workers
0,1,2,3 via the existing GPU handoff. W&B is explicitly online for both trainers.
The wrapper creates independent /tmp compile caches and clears known stale
Qwen/continuation/experimental settings. Use a fresh shell/environment for the run.

The entry automatically checks/merges step 10 into
`$STORAGE_PATH/models/octothinker_3b_hybrid_validity_rl_terra_clean_v1/evaluation_models/`
without modifying the original checkpoint. Completed evaluation merges can be reused.
This initializes **weights**, not the Terra optimizer/dataloader state.
Only trusted local checkpoints should be loaded. The base snapshot is resolved or
downloaded once; semantic workers then use that same local, frozen base snapshot.
HF credentials must permit base/dataset downloads and generated-dataset uploads
under `HUGGINGFACENAME`. This training loop does not require an OpenAI API judge.

Defaults / overrides (set before launching):

- `OCTO_VALIDITY_ROOT`: original validity training run directory.
- `OCTO_BASE_MODEL`: original Hybrid Base model ID or its full local snapshot.
- `OCTO_MODEL_ABBR`: fresh experiment name; default
  `octothinker_3b_hybrid_validity_rzero_semantic_novelty_gate_k8_4gpu_v1`.
- `OCTO_NUM_ROUNDS`: default 5; do not change it when resuming the same run.

Resume the **same new experiment** with the same overrides:

```bash
bash methods/validity_rzero/run_octothinker.sh --resume
```

This does not continue old Qwen Q5/S5. New checkpoints are named
`${MODEL_ABBR}_questioner_v1` / `${MODEL_ABBR}_solver_v1`, etc. Pipeline state is
under `$STORAGE_PATH/rzero_runs/$MODEL_ABBR`; training artifacts retain the
existing layout. Each round uploads its mixed dataset to Hugging Face.

## Compatibility boundary

`VALIDITY_RZERO_MODEL_FAMILY=octothinker` opts into the same chat wrapper used
for validity training. It is applied by the trainer and FSDP worker tokenizers,
so checkpoints save the template too. All three Questioner/Solver inference
entry points pass explicit prompt token IDs to vLLM, avoiding double BOS.
The frozen semantic judge intentionally continues using its native plain-text
completion interface, not the chat wrapper. The family and chat-template hash
are part of the pipeline resume fingerprint. Legacy Qwen launches without this
flag retain their previous tokenizer and generation behavior.

CPU tests cover tokenizer/template persistence, no double BOS, wrapper parameters,
and legacy behavior. They are not an A100 memory or end-to-end GPU training test.
