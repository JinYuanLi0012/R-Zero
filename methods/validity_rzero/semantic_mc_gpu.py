"""Launch evenly sharded single-GPU frozen-base semantic workers."""

from __future__ import annotations

import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from typing import Iterable

from .semantic_judge_offline.run_pair_judge import atomic_json, atomic_jsonl
from .semantic_mc import UniquePairTask


def shard_tasks_by_candidate(
    tasks: list[UniquePairTask], shard_count: int
) -> list[list[UniquePairTask]]:
    """Keep every candidate's references contiguous and on one worker."""
    if shard_count < 1:
        raise ValueError("shard_count must be positive")
    groups: list[list[UniquePairTask]] = []
    group_positions: dict[tuple[str, int], int] = {}
    for task_position, task in enumerate(tasks):
        group_key = (
            ("candidate", task.candidate_index)
            if task.candidate_index is not None
            else ("ungrouped", task_position)
        )
        if group_key not in group_positions:
            group_positions[group_key] = len(groups)
            groups.append([])
        groups[group_positions[group_key]].append(task)
    shards = [[] for _ in range(shard_count)]
    for group_position, group in enumerate(groups):
        shards[group_position % shard_count].extend(group)
    return shards


def aggregate_prefix_cache_metrics(workers: list[dict]) -> dict:
    request_count = sum(int(item.get("generated_request_count", 0)) for item in workers)
    observed_requests = sum(
        int(item.get("prefix_cache_observed_request_count", 0)) for item in workers
    )
    prompt_tokens = sum(
        int(item.get("prefix_cache_observed_prompt_tokens", 0)) for item in workers
    )
    cached_tokens = sum(
        int(item.get("prefix_cache_hit_tokens", 0)) for item in workers
    )
    vllm_versions = sorted({
        str(item["vllm_version"])
        for item in workers
        if item.get("vllm_version") is not None
    })
    engine_modes = sorted({
        str(item["vllm_use_v1"])
        for item in workers
        if item.get("vllm_use_v1") is not None
    })
    return {
        "enabled_explicitly": True,
        "vllm_versions": vllm_versions,
        "vllm_use_v1_values": engine_modes,
        "generated_request_count_including_retries": request_count,
        "observed_request_count": observed_requests,
        "metrics_available_for_all_generated_requests": (
            observed_requests == request_count if request_count else None
        ),
        "observed_prompt_tokens": prompt_tokens,
        "hit_tokens": cached_tokens,
        "token_hit_rate": cached_tokens / prompt_tokens if prompt_tokens else None,
    }


def aggregate_retry_metrics(workers: list[dict]) -> dict[str, int]:
    return {
        key: sum(int(item.get(key, 0)) for item in workers)
        for key in (
            "first_pass_batch_count",
            "first_pass_failure_count",
            "retry_batch_count",
            "retried_request_count",
        )
    }


def terminate_process_groups(processes: Iterable[subprocess.Popen]) -> None:
    processes = list(processes)
    for process in processes:
        if process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
    for process in processes:
        if process.poll() is None:
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait(timeout=10)


def tail_text(path: Path, max_bytes: int = 32_768, max_lines: int = 80) -> str:
    """Read a bounded UTF-8 tail for surfacing child-process diagnostics."""
    if not path.is_file():
        return "<missing>"
    with path.open("rb") as handle:
        size = handle.seek(0, os.SEEK_END)
        handle.seek(max(0, size - max_bytes))
        value = handle.read().decode("utf-8", errors="replace")
    return "\n".join(value.splitlines()[-max_lines:]) or "<empty>"


def worker_failure_message(workers: list[dict]) -> str:
    failed = [worker for worker in workers if worker.get("return_code") != 0]
    sections = []
    for worker in failed:
        sections.append(
            "\n".join((
                f"gpu={worker['gpu_id']} shard={worker['shard_index']} "
                f"pid={worker['pid']} tasks={worker['task_count']} "
                f"exit_code={worker['return_code']}",
                f"stdout={worker['stdout_path']}",
                tail_text(Path(worker["stdout_path"])),
                f"stderr={worker['stderr_path']}",
                tail_text(Path(worker["stderr_path"])),
            ))
        )
    return "semantic GPU worker failures:\n" + "\n---\n".join(sections)


def run_gpu_tasks(
    tasks: list[UniquePairTask],
    model: str,
    gpu_ids: list[str],
    work_dir: Path,
    max_tokens: int = 1024,
    seed: int = 42,
    gpu_memory_utilization: float = 0.85,
    batch_size: int = 8192,
) -> tuple[dict[str, dict], dict]:
    if not gpu_ids:
        raise ValueError("at least one semantic GPU is required")
    if not tasks:
        return {}, {
            "wall_seconds": 0.0,
            "workers": [],
            "prefix_cache": aggregate_prefix_cache_metrics([]),
            "retry": aggregate_retry_metrics([]),
        }
    work_dir.mkdir(parents=True, exist_ok=True)
    shards = shard_tasks_by_candidate(tasks, len(gpu_ids))
    processes: list[subprocess.Popen] = []
    log_handles = []
    workers: list[dict] = []
    pid_file_value = os.getenv("VALIDITY_RZERO_SEMANTIC_PID_FILE")
    pid_file = Path(pid_file_value) if pid_file_value else None
    output_paths: list[Path] = []
    metric_paths: list[Path] = []
    wall_start = time.perf_counter()
    try:
        for shard_index, (gpu_id, shard) in enumerate(zip(gpu_ids, shards)):
            input_path = work_dir / f"semantic_tasks_{shard_index}.jsonl"
            output_path = work_dir / f"semantic_results_{shard_index}.jsonl"
            metric_path = work_dir / f"semantic_metrics_{shard_index}.json"
            stdout_path = work_dir / f"semantic_worker_{shard_index}_gpu_{gpu_id}.stdout.log"
            stderr_path = work_dir / f"semantic_worker_{shard_index}_gpu_{gpu_id}.stderr.log"
            atomic_jsonl(input_path, (
                {
                    "cache_key": task.cache_key,
                    "candidate_index": task.candidate_index,
                    "panel_index": task.panel_index,
                    "prompt": task.prompt,
                }
                for task in shard
            ))
            env = os.environ.copy()
            env["CUDA_VISIBLE_DEVICES"] = str(gpu_id)
            command = [
                sys.executable, "-m", "methods.validity_rzero.semantic_mc_worker",
                "--input", str(input_path), "--output", str(output_path),
                "--metrics", str(metric_path), "--model", model,
                "--max-tokens", str(max_tokens), "--seed", str(seed),
                "--gpu-memory-utilization", str(gpu_memory_utilization),
                "--batch-size", str(batch_size),
            ]
            stdout_handle = stdout_path.open("w", encoding="utf-8")
            stderr_handle = stderr_path.open("w", encoding="utf-8")
            log_handles.extend((stdout_handle, stderr_handle))
            process = subprocess.Popen(
                command,
                env=env,
                start_new_session=True,
                stdout=stdout_handle,
                stderr=stderr_handle,
            )
            processes.append(process)
            workers.append({
                "shard_index": shard_index,
                "gpu_id": str(gpu_id),
                "pid": process.pid,
                "task_count": len(shard),
                "input_path": str(input_path),
                "output_path": str(output_path),
                "metric_path": str(metric_path),
                "stdout_path": str(stdout_path),
                "stderr_path": str(stderr_path),
                "return_code": None,
            })
            atomic_json(work_dir / "semantic_workers.json", {"workers": workers})
            print(
                "[validity_rzero][semantic_worker] "
                f"gpu={gpu_id} shard={shard_index} pid={process.pid} tasks={len(shard)} "
                f"stdout={stdout_path} stderr={stderr_path}",
                flush=True,
            )
            if pid_file is not None:
                pid_file.parent.mkdir(parents=True, exist_ok=True)
                pid_file.write_text(
                    "".join(f"{process.pid}\n" for process in processes), encoding="utf-8"
                )
            output_paths.append(output_path)
            metric_paths.append(metric_path)
        return_codes = [process.wait() for process in processes]
        for worker, return_code, stdout_handle, stderr_handle in zip(
            workers, return_codes, log_handles[::2], log_handles[1::2]
        ):
            worker["return_code"] = return_code
            stdout_handle.flush()
            stderr_handle.flush()
        atomic_json(work_dir / "semantic_workers.json", {"workers": workers})
        if any(code != 0 for code in return_codes):
            atomic_json(
                work_dir / "semantic_failure.json",
                {"return_codes": return_codes, "workers": workers},
            )
            raise RuntimeError(worker_failure_message(workers))
    except BaseException:
        terminate_process_groups(processes)
        if pid_file is not None:
            pid_file.write_text("", encoding="utf-8")
        raise
    finally:
        for handle in log_handles:
            handle.close()
    if pid_file is not None:
        pid_file.write_text("", encoding="utf-8")
    wall_seconds = time.perf_counter() - wall_start
    judgments: dict[str, dict] = {}
    worker_metrics = []
    for output_path, metric_path in zip(output_paths, metric_paths):
        with output_path.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    row = json.loads(line)
                    judgments[row["cache_key"]] = row
        worker_metrics.append(json.loads(metric_path.read_text(encoding="utf-8")))
    if len(judgments) != len(tasks):
        raise RuntimeError(f"semantic result coverage mismatch: {len(judgments)} vs {len(tasks)}")
    return judgments, {
        "wall_seconds": wall_seconds,
        "workers": worker_metrics,
        "prefix_cache": aggregate_prefix_cache_metrics(worker_metrics),
        "retry": aggregate_retry_metrics(worker_metrics),
    }
