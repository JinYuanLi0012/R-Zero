"""Borrow offloaded Questioner GPUs for unchanged phase-A Solver rewards."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import json
import os
from pathlib import Path
import tempfile
import time

import requests

from .semantic_gpu_barrier import wait_until_ready
from .service_handoff import (
    SolverServiceConfig, gpu_compute_pids, start_solver_services,
    terminate_recorded_process_groups, wait_gpus_released, wait_ports_closed,
)


def single_barrier(values) -> str:
    values = [values] if isinstance(values, str) else list(values or [])
    if not values or any(not value for value in values) or len(set(values)) != 1:
        raise RuntimeError("Borrowed reward GPUs require one Questioner-ready barrier per batch")
    return values[0]


def dispatch_reward_shards(data: list[dict], ports: tuple[int, ...], work_dir: Path) -> list[dict]:
    """One request per engine; restore input order despite out-of-order completion."""
    def run_shard(index, port, shard):
        if not shard:
            return []
        path = work_dir / f"shard_{index}.json"
        path.write_text(json.dumps(shard), encoding="utf-8")
        response = requests.get(
            f"http://127.0.0.1:{port}/hello", params={"name": str(path)},
            timeout=(10, int(os.getenv("VALIDITY_RZERO_REWARD_REQUEST_TIMEOUT", "21600"))),
        )
        response.raise_for_status()
        rows = json.loads(path.with_name(f"{path.stem}_results.json").read_text(encoding="utf-8"))
        if len(rows) != len(shard) or any(
            row.get("question") != source.get("question") for row, source in zip(rows, shard)
        ):
            raise RuntimeError(f"Reward shard {index} result coverage/order mismatch")
        return rows

    quotient, remainder = divmod(len(data), len(ports))
    shards = [data[i * quotient + min(i, remainder):(i + 1) * quotient + min(i + 1, remainder)]
              for i in range(len(ports))]
    # Only one outstanding call per offline vLLM engine: Flask itself is threaded.
    with ThreadPoolExecutor(max_workers=len(ports)) as executor:
        futures = [executor.submit(run_shard, i, port, shard)
                   for i, (port, shard) in enumerate(zip(ports, shards))]
        return [row for future in futures for row in future.result()]


def generate_with_borrowed_gpus(data, barrier_values, num_services, port_base):
    if os.getenv("VALIDITY_RZERO_VALIDITY_JUDGE_MODE", "current_solver") != "current_solver":
        raise ValueError("Borrowed reward GPUs currently require current_solver validity judging")
    barrier = single_barrier(barrier_values)
    service = SolverServiceConfig.from_environment()
    if num_services != len(service.gpu_ids) or port_base != service.port_base:
        raise ValueError("Reward endpoints disagree with the permanent Solver pool")
    borrowed_ids = tuple(part.strip() for part in os.environ["QUESTIONER_TRAIN_GPU_IDS"].split(",") if part.strip())
    if (not borrowed_ids or len(set(borrowed_ids)) != len(borrowed_ids)
            or set(borrowed_ids).intersection(service.gpu_ids)):
        raise ValueError("Borrowed GPUs must be distinct and disjoint from permanent Solver GPUs")
    extra = replace(
        service, gpu_ids=borrowed_ids, port_base=port_base + num_services,
        run_id=service.run_id + "_reward",
        pid_file=Path(os.environ["VALIDITY_RZERO_REWARD_PID_FILE"]),
    )
    if extra.pid_file == service.pid_file:
        raise ValueError("Borrowed Solver services require a separate PID file")
    waited = wait_until_ready(barrier)
    # Questioner Ray workers stay alive after offload. Wait only for additional
    # compute processes to disappear on release, never kill the trainer.
    baseline_pids = gpu_compute_pids(extra.gpu_ids)
    started = time.monotonic()
    print(f"[validity_rzero][reward_gpu_borrow] ready wait_seconds={waited:.3f} "
          f"solver_gpus={','.join(service.gpu_ids + extra.gpu_ids)}", flush=True)
    temp_root = Path(os.environ["STORAGE_PATH"]) / "temp_results"
    temp_root.mkdir(parents=True, exist_ok=True)
    work_dir = Path(tempfile.mkdtemp(prefix="reward_gpu_borrow_", dir=temp_root))
    complete = False
    try:
        start_solver_services(extra)
        ready = time.monotonic()
        rows = dispatch_reward_shards(data, service.ports + extra.ports, work_dir)
        print(f"[validity_rzero][reward_gpu_borrow] startup_seconds={ready - started:.3f} "
              f"reward_seconds={time.monotonic() - ready:.3f} rows={len(rows)}", flush=True)
        complete = True
        return rows
    finally:
        release_start = time.monotonic()
        # This also handles partially started pools. The shell EXIT trap owns
        # the same PID file if the Ray reward worker is forcibly cancelled.
        terminate_recorded_process_groups(extra.pid_file)
        wait_ports_closed(extra.ports, extra.release_timeout_seconds)
        wait_gpus_released(extra.gpu_ids, extra.release_timeout_seconds, allowed_pids=baseline_pids)
        print(f"[validity_rzero][reward_gpu_borrow] released "
              f"seconds={time.monotonic() - release_start:.3f}", flush=True)
        if complete:
            import shutil
            shutil.rmtree(work_dir)
        else:
            print(f"[validity_rzero][reward_gpu_borrow] failed batch retained: {work_dir}", flush=True)
