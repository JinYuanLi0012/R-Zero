"""CPU launch/resume checks; no models, services or GPU stages are started."""

import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from methods.validity_rzero.tests.test_novelty_invalid_reward import pipeline_init


ROOT = Path(__file__).resolve().parents[3]
FLAG = "SOLVER_NEGATIVE_ONLY"
POLICY = "negative_only_zero_agree_skip_full_kl_v1"


@pytest.mark.parametrize("enabled", ["0", "1"])
def test_resume_accepts_same_policy_and_rejects_switching(tmp_path, enabled):
    result, state = pipeline_init(tmp_path, {FLAG: enabled})
    assert result.returncode == 0, result.stderr
    assert state["configuration"].get("solver_gradient_policy") == (POLICY if enabled == "1" else None)
    result, resumed = pipeline_init(tmp_path, {FLAG: enabled}, resume=True)
    assert result.returncode == 0, result.stderr
    assert resumed == state
    result, unchanged = pipeline_init(tmp_path, {FLAG: "0" if enabled == "1" else "1"}, resume=True)
    assert result.returncode != 0
    assert "run configuration changed" in result.stderr
    assert unchanged == state


@pytest.mark.parametrize("environment", [{FLAG: "true"}, {FLAG: "1", "VALIDITY_RZERO_ENABLED": "0"}])
def test_launch_rejects_invalid_mode_before_creating_state(tmp_path, environment):
    result, state = pipeline_init(tmp_path, environment)
    assert result.returncode == 2
    assert FLAG in result.stderr
    assert state is None


@pytest.mark.parametrize("enabled", ["0", "1"])
def test_solver_shell_passes_flag_only_when_enabled(tmp_path, enabled):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    shutil.copyfile(ROOT / "scripts/solver_train.sh", scripts / "solver_train.sh")
    binaries = tmp_path / "bin"
    binaries.mkdir()
    # Capture the real trainer argv without launching Ray; bypass the fixed
    # post-training sleep and the generation/merge/evaluation phases.
    for name, body in {"python3": 'printf "ARG:%s\\n" "$@"', "sleep": "exit 0"}.items():
        path = binaries / name
        path.write_text("#!/bin/bash\n" + body + "\n")
        path.chmod(0o755)
    env = {
        "PATH": str(binaries) + os.pathsep + os.defpath,
        "STORAGE_PATH": str(tmp_path / "storage"), "HUGGINGFACENAME": "test-user",
        "VALIDITY_RZERO_ENABLED": "1", FLAG: enabled,
        "SOLVER_DATASET_READY": "1", "SOLVER_SKIP_MERGE": "1", "SOLVER_SKIP_FINAL_EVAL": "1",
    }
    result = subprocess.run(["bash", str(scripts / "solver_train.sh"), "solver", "questioner", "test-run"],
                            cwd=tmp_path, env=env, capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    assert ("ARG:algorithm.solver_negative_only=true" in result.stdout) == (enabled == "1")
    assert "ARG:worker.reward.reward_function=./methods/validity_rzero/mixed_reward.py:compute_score" in result.stdout
    assert "ARG:worker.reward.reward_function_data_keys=[source]" in result.stdout


def test_formal_launcher_pins_original_k8_even_with_other_experiment_environment(tmp_path):
    method = tmp_path / "methods/validity_rzero"
    method.mkdir(parents=True)
    shutil.copyfile(ROOT / "methods/validity_rzero/run_solver_negative_k8.sh", method / "run_solver_negative_k8.sh")
    (method / "run.sh").write_text('#!/bin/bash\nenv\nprintf "FORWARDED:%s\\n" "$@"\n')
    env = {
        "PATH": str(Path(sys.executable).parent) + os.pathsep + os.defpath,
        "VALIDITY_RZERO_NOVELTY_INVALID_REWARD": "zero", "VALIDITY_RZERO_NOVELTY_K": "16",
        "VALIDITY_RZERO_DOMAIN_MODE": "balanced_v1", "VALIDITY_RZERO_NOVELTY_SCOPE": "parent_domain",
        "VALIDITY_RZERO_VALIDITY_JUDGE_MODE": "frozen", "RZERO_QUESTION_BOX_FILTER": "latex_only",
        "MODEL_ABBR": "old-run", "SOLVER_LOAD_CHECKPOINT": "/old/checkpoint",
    }
    result = subprocess.run(["bash", str(method / "run_solver_negative_k8.sh"), "--resume"],
                            env=env, capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    values = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
    expected = {
        FLAG: "1", "VALIDITY_RZERO_NOVELTY_K": "8", "VALIDITY_RZERO_NOVELTY_MIN_SAME_HITS": "1",
        "VALIDITY_RZERO_NOVELTY_INVALID_REWARD": "legacy", "VALIDITY_RZERO_NOVELTY_SCOPE": "global",
        "VALIDITY_RZERO_DOMAIN_MODE": "none", "VALIDITY_RZERO_VALIDITY_JUDGE_MODE": "current_solver",
        "RZERO_QUESTION_BOX_FILTER": "legacy", "QUESTIONER_ROLLOUT_BATCH_SIZE": "512",
        "QUESTIONER_ROLLOUT_N": "4", "TERRA_REPLAY_RATIO": "0.1",
    }
    assert {key: values[key] for key in expected} == expected
    assert values["MODEL_ABBR"] == "qwen3_4b_validity_rzero_semantic_novelty_gate_k8_solver_negative_4gpu_v1"
    assert "SOLVER_LOAD_CHECKPOINT" not in values
    assert "FORWARDED:--resume" in result.stdout
