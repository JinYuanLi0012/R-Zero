"""Online shared-panel semantic reward with Solver/Frozen-Base GPU handoff."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import tempfile

from .semantic_judge_offline.run_pair_judge_v3_vllm import load_generation_config
from .semantic_mc import aggregate_semantic_penalties, build_pair_plan, cache_context
from .semantic_mc_gpu import run_gpu_tasks
from .service_handoff import SolverServiceConfig, semantic_gpu_handoff


_RESOLVED_MODEL: tuple[str, str | None] | None = None


def resolve_frozen_model() -> tuple[str, str | None]:
    global _RESOLVED_MODEL
    if _RESOLVED_MODEL is None:
        model = os.getenv("VALIDITY_RZERO_SEMANTIC_MODEL", "Qwen/Qwen3-4B-Base")
        local_only = os.getenv("VALIDITY_RZERO_SEMANTIC_LOCAL_FILES_ONLY", "1") == "1"
        _, _, resolved_path, revision = load_generation_config(model, None, local_only)
        _RESOLVED_MODEL = resolved_path, revision
        print(
            "[validity_rzero][semantic_mc] "
            f"resolved_frozen_snapshot={resolved_path} revision={revision}"
        )
    return _RESOLVED_MODEL


def compute_online_semantic_penalties(questions: list[str]) -> list[dict[str, int | float]]:
    valid_indices = [index for index, question in enumerate(questions) if question]
    output = [
        {"same_count": 0, "compared_count": 0, "parse_failure_count": 0, "semantic_penalty": 0.0}
        for _ in questions
    ]
    if not valid_indices:
        print("[validity_rzero][semantic_mc][WARNING] no valid questions; all penalties=0")
        return output
    panel_size = min(int(os.getenv("VALIDITY_RZERO_SEMANTIC_PANEL_SIZE", "128")), len(valid_indices))
    panel_seed = int(os.getenv("VALIDITY_RZERO_SEMANTIC_PANEL_SEED", "43"))
    import random
    panel_indices = random.Random(panel_seed).sample(valid_indices, panel_size)
    resolved_model, _ = resolve_frozen_model()
    context = cache_context(resolved_model, 1024, 42)
    question_map = {index: questions[index] for index in valid_indices}
    instances, tasks = build_pair_plan(question_map, valid_indices, panel_indices, context)
    service = SolverServiceConfig.from_environment()
    temp_root = Path(os.environ["STORAGE_PATH"]) / "temp_results"
    temp_root.mkdir(parents=True, exist_ok=True)
    work_dir = Path(tempfile.mkdtemp(prefix="semantic_mc_online_", dir=temp_root))
    try:
        with semantic_gpu_handoff(service):
            judgments, runtime = run_gpu_tasks(
                [tasks[key] for key in sorted(tasks)], resolved_model, list(service.gpu_ids), work_dir,
                max_tokens=1024, seed=42,
                gpu_memory_utilization=float(os.getenv("VALIDITY_RZERO_SEMANTIC_GPU_MEMORY_UTILIZATION", "0.85")),
                batch_size=int(os.getenv("VALIDITY_RZERO_SEMANTIC_WORKER_BATCH_SIZE", "512")),
            )
        warnings: list[str] = []
        aggregates = aggregate_semantic_penalties(valid_indices, instances, judgments, warn=warnings.append)
        for warning in warnings:
            print(warning)
        compared = sum(int(item["compared_count"]) for item in aggregates.values())
        failures = sum(int(item["parse_failure_count"]) for item in aggregates.values())
        total = compared + failures
        print(
            "[validity_rzero][semantic_mc] "
            f"pair_instances={len(instances)} unique_pairs={len(tasks)} "
            f"cache_hits={len(instances) - len(tasks)} vllm_wall_seconds={runtime['wall_seconds']:.3f} "
            f"parse_success_after_retry={(compared / total if total else 1.0):.6f} "
            f"parse_failure_after_retry={(failures / total if total else 0.0):.6f} "
            f"parse_failure_instances_after_retry={failures}"
        )
        for index in valid_indices:
            output[index] = aggregates[index]
        return output
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)
