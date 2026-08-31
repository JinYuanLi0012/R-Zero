import os
from pathlib import Path
import socket
import subprocess
import tempfile


def test_solver_start_refuses_to_reuse_an_existing_listener():
    repo_root = Path(__file__).parents[3]
    with socket.socket() as listener, tempfile.TemporaryDirectory() as directory:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        port = listener.getsockname()[1]
        env = os.environ.copy()
        env.update({
            "VLLM_GPU_IDS": "2",
            "VLLM_PORT_BASE": str(port),
            "VLLM_LOG_DIR": directory,
            "QUESTIONER_VLLM_PID_FILE": str(Path(directory) / "solver.pids"),
        })
        result = subprocess.run(
            ["bash", "vllm_service_init/start.sh", "/model", "new-run"],
            cwd=repo_root,
            env=env,
            capture_output=True,
            text=True,
        )
    assert result.returncode == 2
    assert f"port {port} is already owned by another process" in result.stderr
