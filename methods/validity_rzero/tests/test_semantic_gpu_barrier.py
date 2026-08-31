import json
from pathlib import Path
import tempfile
import threading
import time
import unittest

from methods.validity_rzero.semantic_gpu_barrier import (
    cleanup_barrier,
    signal_abort,
    signal_ready,
    wait_until_ready,
)


def test_waiter_blocks_until_trainer_signals_ready():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "ready.json"
        result = []
        waiter = threading.Thread(target=lambda: result.append(wait_until_ready(str(path), 2)))
        waiter.start()
        time.sleep(0.15)
        assert waiter.is_alive()
        signal_ready(path)
        waiter.join(timeout=2)
        assert not waiter.is_alive()
        assert result[0] >= 0.1
        assert json.loads(path.read_text())["status"] == "ready"


def test_abort_prevents_semantic_gpu_start_and_cleanup_removes_marker():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "abort.json"
        signal_abort(path, "old log-prob failed")
        with unittest.TestCase().assertRaisesRegex(RuntimeError, "old log-prob failed"):
            wait_until_ready(str(path), 1)
        cleanup_barrier(path)
        assert not path.exists()


def test_missing_ready_signal_times_out_without_falling_through():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "missing.json"
        with unittest.TestCase().assertRaisesRegex(TimeoutError, "Questioner GPU handoff"):
            wait_until_ready(str(path), 0)
