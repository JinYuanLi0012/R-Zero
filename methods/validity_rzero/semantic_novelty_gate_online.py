"""Online per-candidate semantic novelty gate using the frozen judge."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import tempfile

from .semantic_gpu_barrier import wait_until_ready
from .semantic_judge_offline.semantic_pair_prompt_formal import (
    PROMPT_TEMPLATE,
    PROMPT_VERSION,
    build_prompt,
)
from .semantic_mc import cache_context
from .semantic_mc_gpu import run_gpu_tasks
from .semantic_mc_online import _semantic_gpu_ids, resolve_frozen_model
from .semantic_novelty_gate import aggregate_novelty, build_novelty_pair_plan
from .service_handoff import SolverServiceConfig, semantic_gpu_handoff


def compute_online_novelty(
    questions: list[str], gpu_ready_file: str | None = None
) -> list[dict[str, int]]:
    candidate_indices = [index for index, question in enumerate(questions) if question]
    output = [
        {"same_count": 0, "compared_count": 0, "parse_failure_count": 0, "novelty": 1}
        for _ in questions
    ]
    if not candidate_indices:
        print("[validity_rzero][semantic_novelty_gate][WARNING] no valid questions; novelty=1")
        return output
    novelty_k = int(os.getenv("VALIDITY_RZERO_NOVELTY_K", "8"))
    min_same_hits = int(os.getenv("VALIDITY_RZERO_NOVELTY_MIN_SAME_HITS", "1"))
    novelty_seed = int(os.getenv("VALIDITY_RZERO_NOVELTY_SEED", "43"))
    if novelty_k < 0:
        raise ValueError("VALIDITY_RZERO_NOVELTY_K must be nonnegative")
    if not 1 <= min_same_hits <= novelty_k:
        raise ValueError(
            "VALIDITY_RZERO_NOVELTY_MIN_SAME_HITS must be between 1 and "
            "VALIDITY_RZERO_NOVELTY_K"
        )
    resolved_model, _ = resolve_frozen_model()
    context = cache_context(
        resolved_model,
        1024,
        42,
        prompt_version=PROMPT_VERSION,
        prompt_template=PROMPT_TEMPLATE,
        orientation="candidate_then_reference_v1",
    )
    question_map = {index: questions[index] for index in candidate_indices}
    references, instances, tasks = build_novelty_pair_plan(
        question_map,
        candidate_indices,
        novelty_k,
        novelty_seed,
        context,
        prompt_builder=build_prompt,
    )
    service = SolverServiceConfig.from_environment()
    semantic_gpu_ids = _semantic_gpu_ids(service)
    temp_root = Path(os.environ["STORAGE_PATH"]) / "temp_results"
    temp_root.mkdir(parents=True, exist_ok=True)
    work_dir = Path(tempfile.mkdtemp(prefix="semantic_novelty_gate_online_", dir=temp_root))
    completed = False
    try:
        barrier_wait_seconds = 0.0
        if gpu_ready_file:
            barrier_wait_seconds = wait_until_ready(gpu_ready_file)
            print(
                "[validity_rzero][semantic_novelty_gate] Questioner GPU barrier ready "
                f"after {barrier_wait_seconds:.3f}s; semantic_gpus={','.join(semantic_gpu_ids)}"
            )
        with semantic_gpu_handoff(service):
            judgments, runtime = run_gpu_tasks(
                list(tasks.values()),
                resolved_model,
                semantic_gpu_ids,
                work_dir,
                max_tokens=1024,
                seed=42,
                gpu_memory_utilization=float(
                    os.getenv("VALIDITY_RZERO_SEMANTIC_GPU_MEMORY_UTILIZATION", "0.80")
                ),
                batch_size=int(
                    os.getenv("VALIDITY_RZERO_SEMANTIC_WORKER_BATCH_SIZE", "8192")
                ),
            )
        aggregates = aggregate_novelty(
            candidate_indices,
            instances,
            judgments,
            min_same_hits=min_same_hits,
        )
        compared = sum(int(item["compared_count"]) for item in aggregates.values())
        failures = sum(int(item["parse_failure_count"]) for item in aggregates.values())
        total = compared + failures
        retry = runtime["retry"]
        prefix_cache = runtime["prefix_cache"]
        prefix_hit_rate = prefix_cache["token_hit_rate"]
        sampled_counts = [len(references[index]) for index in candidate_indices]
        print(
            "[validity_rzero][semantic_novelty_gate] "
            f"prompt_version={PROMPT_VERSION} novelty_k={novelty_k} "
            f"novelty_min_same_hits={min_same_hits} novelty_seed={novelty_seed} "
            f"references_per_candidate_min={min(sampled_counts)} "
            f"references_per_candidate_max={max(sampled_counts)} "
            f"semantic_gpus={','.join(semantic_gpu_ids)} "
            f"barrier_wait_seconds={barrier_wait_seconds:.3f} "
            f"pair_instances={len(instances)} unique_pairs={len(tasks)} "
            f"cache_hits={len(instances) - len(tasks)} "
            f"vllm_wall_seconds={runtime['wall_seconds']:.3f} "
            f"parse_success_after_retry={(compared / total if total else 1.0):.6f} "
            f"parse_failure_after_retry={(failures / total if total else 0.0):.6f}"
        )
        print(
            "[validity_rzero][semantic_novelty_gate][efficiency] "
            f"first_pass_batches={retry['first_pass_batch_count']} "
            f"first_pass_parse_failures={retry['first_pass_failure_count']} "
            f"deferred_retry_batches={retry['retry_batch_count']} "
            f"retried_requests={retry['retried_request_count']} "
            f"prefix_cache_enabled={prefix_cache['enabled_explicitly']} "
            f"prefix_cache_token_hit_rate="
            f"{(f'{prefix_hit_rate:.6f}' if prefix_hit_rate is not None else 'unavailable')}"
        )
        for index in candidate_indices:
            output[index] = aggregates[index]
        completed = True
        return output
    finally:
        if completed:
            shutil.rmtree(work_dir, ignore_errors=True)
        else:
            print(
                "[validity_rzero][semantic_novelty_gate][WARNING] "
                f"preserving failed semantic work directory: {work_dir}",
                flush=True,
            )
