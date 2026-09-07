"""CPU regression for the opt-in INVALID=0 Questioner ablation."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from methods.validity_rzero.gating import evaluate_validity_responses
from methods.validity_rzero.tests.test_questioner_diversity import _run_compute_score


ROOT = Path(__file__).resolve().parents[3]
FLAG = "VALIDITY_RZERO_NOVELTY_INVALID_REWARD"


def vote_result(invalid_votes):
    gate = evaluate_validity_responses(
        [r"\boxed{INVALID}"] * invalid_votes
        + [r"\boxed{12}"] * (9 - invalid_votes)
    )
    frontier = 0.4 if gate["validity_decision"] == "VALID" else 0.0
    return dict(
        gate,
        question="question",
        math_frontier_score=frontier,
        questioner_base_reward=gate["validity_penalty"] or frontier,
    )


def novelty_stats(novelty):
    return dict(novelty=novelty, same_count=1 - novelty,
                compared_count=8, parse_failure_count=0)


@pytest.mark.parametrize("policy", [None, "legacy", "zero"])
@pytest.mark.parametrize("votes", [4, 5, 9])
@pytest.mark.parametrize("novelty", [0, 1])
def test_nine_vote_boundary_and_final_reward(policy, votes, novelty):
    row = vote_result(votes)
    original_row = row.copy()
    environment = {"VALIDITY_RZERO_ENABLED": "1",
                   "VALIDITY_RZERO_DIVERSITY_MODE": "semantic_novelty_gate"}
    if policy is not None:
        environment[FLAG] = policy
    scores, logs = _run_compute_score(
        [row], None, environment, novelty_stats=[novelty_stats(novelty)],
    )
    assert row == original_row  # Do not rewrite the gate/base-reward audit data.
    assert row["total_votes"] == 9
    assert row["validity_decision"] == ("VALID" if votes == 4 else "INVALID")
    expected = novelty * 0.4 if votes == 4 else (0.0 if policy == "zero" else 0.5 - votes / 9)
    assert scores[0]["overall"] == pytest.approx(expected)
    assert scores[0]["validity_penalty"] == row["validity_penalty"]
    assert scores[0]["novelty_invalid_reward_zero"] == float(policy == "zero")
    assert f'"novelty_invalid_reward": "{policy or "legacy"}"' in logs


@pytest.mark.parametrize("policy", [None, "legacy", "zero"])
def test_malformed_questioner_output_still_gets_minus_one(policy):
    environment = {"VALIDITY_RZERO_ENABLED": "1",
                   "VALIDITY_RZERO_DIVERSITY_MODE": "semantic_novelty_gate"}
    if policy is not None:
        environment[FLAG] = policy
    parsed = []
    scores, _ = _run_compute_score(
        [{"question": "", "answer": ""}], None, environment,
        novelty_stats=[novelty_stats(1)], predictions=["no question tags"],
        parsed_inputs=parsed,
    )
    assert parsed == [{"question": "", "answer": ""}]
    assert scores[0]["overall"] == -1.0
    assert scores[0]["format"] == 0


@pytest.mark.parametrize("mode", ["baseline", "bleu_legacy", "bleu_lambda5", "semantic_mc"])
@pytest.mark.parametrize("unused_value", ["zero", "legacy", "invalid-unused-value"])
def test_other_reward_modes_ignore_new_environment_variable(mode, unused_value):
    environment = {"VALIDITY_RZERO_ENABLED": "0" if mode == "baseline" else "1",
                   "VALIDITY_RZERO_DIVERSITY_MODE": mode}
    rows = ([{"question": "question", "score": 0.3}] if mode == "baseline"
            else [vote_result(4), vote_result(5)])
    semantic = [dict(same_count=1, compared_count=4, parse_failure_count=0,
                     semantic_penalty=0.25)] * len(rows)
    before, _ = _run_compute_score(rows, [0.1] * len(rows), environment, semantic_stats=semantic)
    after, _ = _run_compute_score(rows, [0.1] * len(rows), dict(environment, **{FLAG: unused_value}),
                                  semantic_stats=semantic)
    assert before == after


def test_novelty_reward_rejects_typo_in_flag():
    with pytest.raises(ValueError, match="must be legacy or zero"):
        _run_compute_score([vote_result(5)], None, {
            "VALIDITY_RZERO_ENABLED": "1",
            "VALIDITY_RZERO_DIVERSITY_MODE": "semantic_novelty_gate", FLAG: "zeros",
        })


def pipeline_init(directory, environment, resume=False):
    """Execute the real shell setup/state init, stopping before any GPU stages."""
    scripts = directory / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    main = (ROOT / "scripts/main.sh").read_text()
    preamble, separator, _ = main.partition("\nmarker() {")
    assert separator, "test must stop before stage execution"
    (scripts / "main.sh").write_text(preamble + "\nexit 0\n")
    for name in ("rzero_pipeline_state.py", "validate_hf_checkpoint.py"):
        shutil.copyfile(ROOT / "scripts" / name, scripts / name)
    model = directory / "initial_solver"
    model.mkdir(exist_ok=True)
    (model / "config.json").write_text("{}")
    (model / "model.safetensors").write_bytes(b"CPU-test-placeholder")
    env = {
        "PATH": str(Path(sys.executable).parent) + os.pathsep + os.defpath,
        "STORAGE_PATH": str(directory / "storage"),
        "HUGGINGFACENAME": "test-user",
        "VALIDITY_RZERO_ENABLED": "1",
        "VALIDITY_RZERO_INITIAL_SOLVER": str(model),
        "TERRA_REPLAY_DATASET": "test/terra",
        "TERRA_REPLAY_RATIO": "0.1",
        "VALIDITY_RZERO_DIVERSITY_MODE": "semantic_novelty_gate",
        "SOLVER_GENERATE_SAMPLES": "2500",
        **environment,
    }
    command = ["bash", str(scripts / "main.sh")]
    if resume:
        command.append("--resume")
    result = subprocess.run(command + ["test/base", "test-run"], env=env,
                            capture_output=True, text=True, timeout=20)
    state = directory / "storage/rzero_runs/test-run/state/run_state.json"
    return result, json.loads(state.read_text()) if state.exists() else None


@pytest.mark.parametrize("k,hits", [(8, 1), (16, 1), (16, 2)])
def test_legacy_fingerprint_matches_pre_ablation_fixture_and_resumes(tmp_path, k, hits):
    env = {"VALIDITY_RZERO_NOVELTY_K": str(k), "VALIDITY_RZERO_NOVELTY_MIN_SAME_HITS": str(hits)}
    result, state = pipeline_init(tmp_path, env)
    assert result.returncode == 0, result.stderr
    # Captured by executing main.sh at pre-ablation commit c5031d3; only the
    # temporary initial-model path is normalized in the checked-in fixture.
    expected = json.loads((Path(__file__).with_name("legacy_novelty_configuration.json")).read_text())
    expected["initial_solver"] = str(tmp_path / "initial_solver")
    expected["semantic_novelty_k"] = str(k)
    if hits != 1:
        expected["semantic_novelty_min_same_hits"] = str(hits)
        expected["semantic_novelty_treatment"] = "minimum_same_hits_hard_gate_v1"
    assert state["configuration"] == expected
    result, resumed = pipeline_init(tmp_path, dict(env, **{FLAG: "legacy"}), resume=True)
    assert result.returncode == 0, result.stderr
    assert resumed == state
    result, unchanged = pipeline_init(tmp_path, dict(env, **{FLAG: "zero"}), resume=True)
    assert result.returncode != 0
    assert "run configuration changed" in result.stderr
    assert unchanged == state


def test_zero_fingerprint_records_ablation_resumes_and_rejects_legacy(tmp_path):
    result, state = pipeline_init(tmp_path, {FLAG: "zero"})
    assert result.returncode == 0, result.stderr
    assert state["configuration"]["semantic_novelty_invalid_reward"] == "zero"
    result, resumed = pipeline_init(tmp_path, {FLAG: "zero"}, resume=True)
    assert result.returncode == 0, result.stderr
    assert resumed == state
    result, unchanged = pipeline_init(tmp_path, {}, resume=True)
    assert result.returncode != 0
    assert "run configuration changed" in result.stderr
    assert unchanged == state


@pytest.mark.parametrize("mode", ["baseline", "bleu_legacy", "bleu_lambda5", "semantic_mc"])
def test_other_pipeline_fingerprints_ignore_flag(tmp_path, mode):
    env = {"VALIDITY_RZERO_DIVERSITY_MODE": mode,
           "VALIDITY_RZERO_ENABLED": "0" if mode == "baseline" else "1"}
    result, state = pipeline_init(tmp_path, env)
    if mode == "baseline" and "FINGERPRINT_EXTRA[@]: unbound variable" in result.stderr:
        pytest.skip("unchanged pipeline needs Bash >=4.4 for empty arrays under set -u; macOS ships 3.2")
    assert result.returncode == 0, result.stderr
    result, resumed = pipeline_init(tmp_path, dict(env, **{FLAG: "zero"}), resume=True)
    assert result.returncode == 0, result.stderr
    assert resumed == state


def test_pipeline_rejects_unknown_reward_policy_before_state_creation(tmp_path):
    result, state = pipeline_init(tmp_path, {FLAG: "zeros"})
    assert result.returncode == 2
    assert "must be legacy or zero" in result.stderr
    assert state is None
