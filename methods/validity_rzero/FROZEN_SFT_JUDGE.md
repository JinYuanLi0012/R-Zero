# Fresh Octo five-round experiment with frozen SFT judge

Only semantic judging changes. Questioner starts from Octo Hybrid Base, Solver
from the original validity step10; current_solver validity voting remains intact.
K8/minSame1, Q5/S15 steps, four-GPU topology, .1 clean-Terra replay and W&B online
remain the original Octo experiment settings. No old round artifacts are reused.

Export once (CPU RAM required for a 3B BF16 model):

```bash
python -m methods.validity_rzero.export_frozen_judge \
  --model /path/to/original/base/snapshot \
  --adapter /path/to/judge_sft_v2_clear_3065291/epoch_3 \
  --output-dir "$STORAGE_PATH/models/octothinker_3b_hybrid_semantic_judge_sft_v2_clear_epoch3_frozen"
```

Export refuses overwrite, uses safe LoRA merge, retains the source adapter and
training provenance, writes checksums, verifies them, and publishes read-only
files via a sibling staging directory rename. Failed staging remains for diagnosis.
Read-only permissions prevent accidental edits, not modification by the owner.

```bash
export OCTO_FROZEN_JUDGE_MODEL="$STORAGE_PATH/models/octothinker_3b_hybrid_semantic_judge_sft_v2_clear_epoch3_frozen"
bash methods/validity_rzero/run_octothinker_sftjudge.sh
```

Without `--resume`, the entry refuses existing run/checkpoint directories. Default name:
octothinker_3b_hybrid_validity_rzero_semantic_novelty_gate_k8_4gpu_sftjudge_v1.
It verifies full checksums and includes the frozen manifest digest in the run
fingerprint. Workers detect judge_protocol.json: saved SFT system/chat template,
no few-shot, explicit token IDs to avoid double BOS, greedy with EOS termination,
256 output-token budget, no presence penalty. Legacy models without this file
continue using the original prompt and sampling. Reward aggregation, including
legacy parse-failure treatment and one retry, is unchanged.

Before production, use one tiny mixed SAME_TYPE/DIFFERENT check through the actual
semantic_mc_worker on the exported model. Never overwrite the original base or
SFT run. Server launch must preserve its existing Ray temp-directory and service
port isolation fixes. No jobs or model state from unrelated experiments should
be changed.

## Resume the same interrupted experiment

Keep the original environment, model paths, `OCTO_MODEL_ABBR`, frozen judge and
five-round budget; do not choose a new name or change `RZERO_FIRST_ROUND`.

```bash
export OCTO_MODEL_ABBR=octothinker_3b_hybrid_validity_rzero_semantic_novelty_gate_k8_4gpu_sftjudge_v1
export OCTO_FROZEN_JUDGE_MODEL="$STORAGE_PATH/models/octothinker_3b_hybrid_semantic_judge_sft_v2_clear_epoch3_frozen"
export RZERO_SOLVER_VLLM_PORT_BASE=12000
python3 scripts/find_resume_checkpoint.py \
  --root "$STORAGE_PATH/models/${OCTO_MODEL_ABBR}_questioner_v5" --world-size 2
bash methods/validity_rzero/run_octothinker_sftjudge.sh --resume
```

The wrapper requires existing pipeline state. The original pipeline checks the
same fingerprint, skips verified completed stages, and restores the latest
atomically committed checkpoint (including optimizer, RNG and dataloader), not
just HF weights. For the round-5 interruption with a complete tracked step 3,
this continues Questioner steps 4–5, then the remaining round-5 stages. Missing
or corrupt tracked checkpoint files fail validation rather than silently restart.

`vllm_service_init/start.sh` is shared by initial launch and every handoff restart.
Each numeric physical GPU gets an internal block of 256 ports starting at
`RZERO_SOLVER_VLLM_PORT_BASE + 256 * GPU_ID`; default GPUs 2/3 use 12512/12768.
The DP master starts 128 ports into its block. This overrides inherited
`VLLM_PORT`/`VLLM_DP_MASTER_PORT`, while leaving HTTP endpoints unchanged. Blocks
are checked before launching any process; occupied blocks fail without killing
their owners. These are transport settings, not experiment fingerprint fields.
Use a dedicated node/range: socket preflight is not an OS-level reservation and
cannot prevent unrelated processes racing to bind after the check. For Compute2,
12000-series Solver ports are separate from semantic 18000-series, annotation
16000-series, and HTTP 20000–29999. No model, reward or decoding settings change.
