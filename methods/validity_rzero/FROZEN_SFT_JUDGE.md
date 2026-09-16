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

The new entry refuses resume and existing run/checkpoint directories. Default name:
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
