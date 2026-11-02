# R-Zero with matched validity initialization and replay

This opt-in control starts the Solver from the same validity-RL step-15 checkpoint
as R-Quest and mixes the same Terra training data into every Solver round. It uses
the original R-Zero feedback: neither the validity gate nor the semantic novelty
gate runs. Original R-Zero difficulty filtering and BLEU penalty remain enabled.

Existing `methods/validity_rzero/run.sh` commands are unchanged. The new switch
`RZERO_INIT_REPLAY_ONLY` defaults to `0` and contributes no resume fingerprint
fields when disabled. Do not set it in the environment of a standard R-Quest run.

```bash
source env_rzero.sh
export VALIDITY_RZERO_INITIAL_SOLVER="$STORAGE_PATH/models/qwen3_4b_validity_rl_terra_clean_v1/global_step_15/actor/huggingface"
export MODEL_ABBR=qwen3_4b_rzero_initstep15_replay10_r10
export RZERO_NUM_ROUNDS=10
bash methods/validity_rzero/run_init_replay_only.sh
# Resume the same run with unchanged settings:
# bash methods/validity_rzero/run_init_replay_only.sh --resume
```

The entry point sets `RZERO_INIT_REPLAY_ONLY=1` and `VALIDITY_RZERO_ENABLED=0`.
It defaults to Qwen3-4B-Base for the Questioner, five Questioner steps, fifteen
Solver steps, 2,500 generated candidates per GPU, Terra replay ratio 0.1 and
replay seed 1. Each round starts from the previous round's models; step 15 is
used only as the initial Solver. Training seeds and other budget settings should
be matched explicitly to the R-Quest run being compared.

Replay is a fraction of the final mixed dataset: for N accepted R-Zero rows,
the mixer takes floor(N * 0.1 / 0.9) Terra rows. It retains the original
source-specific prompts and rewards (`rzero` math reward; `terra` validity
supervision), including INVALID targets. These supervised replay rewards are
independent of applying a validity gate to newly generated questions.

Use a fresh run name and output directory. The state fingerprint records the
control mode, initial checkpoint, replay dataset/config/ratio/seed; changing
these on resume is rejected. Per-round dataset receipts include counts,
actual replay ratio and the phase-B audit. No new gate model is started.

CPU regression checks:

```bash
python -m unittest scripts.tests.test_init_replay_control scripts.tests.test_rzero_resume
```
