import os
from pathlib import Path
import subprocess


SMOKE = Path(__file__).with_name("gpu_smoke.sh")


def test_smoke_only_shortens_round_steps_and_candidate_count():
    text = SMOKE.read_text(encoding="utf-8")
    for required in (
        "RZERO_NUM_ROUNDS=1",
        "QUESTIONER_MAX_STEPS=1",
        "QUESTIONER_MERGE_STEP=1",
        "SOLVER_MAX_STEPS=1",
        "SOLVER_MERGE_STEP=1",
        "SOLVER_GENERATE_SAMPLES",
    ):
        assert required in text
    for forbidden in (
        "ROLLOUT_N=",
        "GLOBAL_BATCH_SIZE=",
        "MICRO_BATCH",
        "MAX_RESPONSE_LENGTH=",
        "TEMPERATURE=",
        "TOP_P=",
        "TOP_K=",
        "KL_",
        "LEARNING_RATE=",
        "TERRA_REPLAY_RATIO=",
        "GPU_IDS=",
    ):
        assert forbidden not in text


def test_validity_runner_disables_pipeline_evaluation_hooks():
    run_script = SMOKE.parent.parent / "run.sh"
    assert "scripts/main.sh --no-eval" in run_script.read_text(encoding="utf-8")


def test_disabled_feature_ignores_initial_validity_solver():
    main_script = SMOKE.parents[3] / "scripts" / "main.sh"
    text = main_script.read_text(encoding="utf-8")
    selection = text.split("# BEGIN initial model selection\n", 1)[1].split(
        "# END initial model selection", 1
    )[0]
    command = selection + '\nprintf "%s\\n" "$CURRENT_SOLVER"\n'
    env = {
        **os.environ,
        "BASE_MODEL": "baseline-model",
        "VALIDITY_RZERO_ENABLED": "0",
        "VALIDITY_RZERO_INITIAL_SOLVER": "validity-model-that-must-be-ignored",
    }

    result = subprocess.run(
        ["bash", "-eu", "-c", command],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.stdout.strip() == "baseline-model"
