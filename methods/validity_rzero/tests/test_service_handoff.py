from dataclasses import replace
from pathlib import Path
import json
import os
import tempfile
import unittest
from unittest.mock import patch

from methods.validity_rzero.service_handoff import (
    SolverServiceConfig,
    semantic_gpu_handoff,
    start_solver_services,
    stop_solver_services,
    wait_services_healthy,
)
from methods.validity_rzero.semantic_mc import UniquePairTask
from methods.validity_rzero.semantic_mc_gpu import run_gpu_tasks


def config(tmp_path):
    return SolverServiceConfig(
        repo_root=tmp_path,
        model_path="solver-model",
        run_id="run-id",
        pid_file=tmp_path / "solver.pids",
        gpu_ids=("2", "3"),
        port_base=5000,
        health_timeout_seconds=7,
        release_timeout_seconds=9,
    )


def test_stop_waits_for_processes_ports_and_gpu_release():
    with tempfile.TemporaryDirectory() as directory:
        value = config(Path(directory))
        with patch("methods.validity_rzero.service_handoff.terminate_recorded_process_groups") as terminate, \
             patch("methods.validity_rzero.service_handoff.wait_ports_closed") as ports, \
             patch("methods.validity_rzero.service_handoff.wait_gpus_released") as gpus:
            stop_solver_services(value)
        terminate.assert_called_once_with(value.pid_file)
        ports.assert_called_once_with((5000, 5001), 9)
        gpus.assert_called_once_with(("2", "3"), 9)


def test_handoff_always_restarts_solver_after_semantic_body_failure():
    with tempfile.TemporaryDirectory() as directory:
        value = config(Path(directory))
        events = []
        with patch("methods.validity_rzero.service_handoff.stop_solver_services", side_effect=lambda _: events.append("stop")), \
             patch("methods.validity_rzero.service_handoff.wait_gpus_released", side_effect=lambda *_: events.append("judge_release")), \
             patch("methods.validity_rzero.service_handoff.start_solver_services", side_effect=lambda _: events.append("restart")):
            with unittest.TestCase().assertRaisesRegex(RuntimeError, "judge failed"):
                with semantic_gpu_handoff(value):
                    events.append("judge")
                    raise RuntimeError("judge failed")
        assert events == ["stop", "judge", "judge_release", "restart"]


def test_failed_solver_restart_cleans_partially_started_processes():
    with tempfile.TemporaryDirectory() as directory:
        value = config(Path(directory))
        with patch("methods.validity_rzero.service_handoff.subprocess.run"), \
             patch("methods.validity_rzero.service_handoff.wait_services_healthy", side_effect=RuntimeError("unhealthy")), \
             patch("methods.validity_rzero.service_handoff.terminate_recorded_process_groups") as cleanup:
            with unittest.TestCase().assertRaisesRegex(RuntimeError, "unhealthy"):
                start_solver_services(value)
        cleanup.assert_called_once_with(value.pid_file)


def test_solver_health_is_bound_to_recorded_run_id_and_pid():
    with tempfile.TemporaryDirectory() as directory:
        value = config(Path(directory))
        with patch("methods.validity_rzero.service_handoff.read_pids", return_value=[101, 102]), \
             patch(
                 "methods.validity_rzero.service_handoff.service_health",
                 side_effect=lambda port: {
                     "status": "ok",
                     "run_id": "run-id",
                     "pid": {5000: 101, 5001: 102}[port],
                 },
             ):
            wait_services_healthy(value)


def test_solver_health_rejects_incomplete_pid_coverage_immediately():
    with tempfile.TemporaryDirectory() as directory:
        value = config(Path(directory))
        with patch("methods.validity_rzero.service_handoff.read_pids", return_value=[101]):
            with unittest.TestCase().assertRaisesRegex(RuntimeError, "PID coverage mismatch"):
                wait_services_healthy(value)


def test_solver_health_rejects_a_stale_healthy_run():
    with tempfile.TemporaryDirectory() as directory:
        value = replace(config(Path(directory)), health_timeout_seconds=0)
        stale = {"status": "ok", "run_id": "old-run", "pid": 999}
        with patch("methods.validity_rzero.service_handoff.read_pids", return_value=[101, 102]), \
             patch("methods.validity_rzero.service_handoff.service_health", return_value=stale):
            with unittest.TestCase().assertRaisesRegex(RuntimeError, "expected run/PID identity"):
                wait_services_healthy(value)


def test_semantic_workers_are_evenly_sharded_and_failure_clears_supervisor_pids():
    class FailedProcess:
        next_pid = 100

        def __init__(self, *_args, **_kwargs):
            self.pid = FailedProcess.next_pid
            FailedProcess.next_pid += 1
            _kwargs["stdout"].write(f"stdout from pid {self.pid}\n")
            _kwargs["stderr"].write(f"traceback from pid {self.pid}\n")

        def wait(self, timeout=None):
            return 1

        def poll(self):
            return 1

    tasks = [UniquePairTask(str(index), "a", "b", f"prompt {index}") for index in range(5)]
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        pid_file = root / "semantic.pids"
        with patch.dict(os.environ, {"VALIDITY_RZERO_SEMANTIC_PID_FILE": str(pid_file)}), \
             patch("methods.validity_rzero.semantic_mc_gpu.subprocess.Popen", FailedProcess):
            with unittest.TestCase().assertRaisesRegex(RuntimeError, "worker failures") as error:
                run_gpu_tasks(tasks, "/model", ["2", "3"], root / "work")
        message = str(error.exception)
        assert "gpu=2 shard=0 pid=100 tasks=3 exit_code=1" in message
        assert "gpu=3 shard=1 pid=101 tasks=2 exit_code=1" in message
        assert "traceback from pid 100" in message
        shard_counts = []
        for index in range(2):
            rows = [
                json.loads(line)
                for line in (root / "work" / f"semantic_tasks_{index}.jsonl").read_text().splitlines()
            ]
            shard_counts.append(len(rows))
        assert shard_counts == [3, 2]
        assert pid_file.read_text() == ""
        failure = json.loads((root / "work" / "semantic_failure.json").read_text())
        assert failure["return_codes"] == [1, 1]
        assert [worker["gpu_id"] for worker in failure["workers"]] == ["2", "3"]
        assert (root / "work" / "semantic_worker_0_gpu_2.stdout.log").is_file()
        assert (root / "work" / "semantic_worker_0_gpu_2.stderr.log").is_file()


def test_semantic_worker_disables_per_request_tqdm_logging():
    source = (Path(__file__).parents[1] / "semantic_mc_worker.py").read_text(
        encoding="utf-8"
    )
    assert "model.generate(prompts, sampling_params=sampling, use_tqdm=False)" in source
