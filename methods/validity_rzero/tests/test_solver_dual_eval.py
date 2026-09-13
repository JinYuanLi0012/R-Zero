"""Run the actual round-evaluation shell block and batch evaluator on CPU.

Only the GPU benchmark subprocess is replaced with deterministic score output.
"""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from scripts.rzero_pipeline_state import init_state
from methods.validity_rzero.tests.test_novelty_invalid_reward import pipeline_init


ROOT = Path(__file__).resolve().parents[3]


def setup_pipeline(tmp_path):
    for directory in ("scripts", "evaluation"):
        (tmp_path / directory).mkdir()
    for name in ("evaluation/evaluate_models.py", "evaluation/judge_prompts.py", "scripts/rzero_pipeline_state.py"):
        shutil.copyfile(ROOT / name, tmp_path / name)
    main = (ROOT / "scripts/main.sh").read_text()
    functions = main[main.index("marker() {"):main.index("resolve_latest_checkpoint() {")]
    block = main[main.index('    if [ "$SOLVER_EVAL_DUAL" = "1" ]; then', main.index('    CURRENT_SOLVER=$SOLVER_HF')):]
    block = block[:block.index('\ndone\n')]
    (tmp_path / "run_eval.sh").write_text(
        'set -euo pipefail\n' + functions + '\n' + block + '\necho NEXT_ROUND\n')
    (tmp_path / "evaluation/evaluate.bash").write_text('exec python3 evaluation/fake_gpu.py "$@"\n')
    (tmp_path / "evaluation/fake_gpu.py").write_text('''
import json, os, sys
from pathlib import Path
from evaluate_models import DATASETS, JUDGE
from judge_prompts import prompt_metadata
mode = os.environ['RECHECK_JUDGE_PROMPT_MODE']
with Path('calls.jsonl').open('a') as stream:
    stream.write(json.dumps(dict(mode=mode, model=sys.argv[1], gpu=os.environ['EVAL_GPU_IDS'],
        tmp=os.environ['RECHECK_LOCAL_TMP_ROOT'], timeout=os.environ['RECHECK_STARTUP_TIMEOUT'])) + '\\n')
fail = Path('fail_corrected').exists() and mode == 'corrected'
judge = dict(JUDGE, **prompt_metadata(mode))
datasets = DATASETS[:1] if fail else DATASETS
Path(os.environ['FINAL_RESULTS_FILE']).write_text(''.join(json.dumps(dict(
    model=sys.argv[1], dataset=d, score=70, recheck=judge)) + '\\n' for d in datasets))
sys.exit(1 if fail else 0)
''')
    model = tmp_path / "solver/global_step_15/actor/huggingface"
    model.mkdir(parents=True)
    (model / "config.json").write_text("{}")
    run = tmp_path / "run"
    state = run / "state/run_state.json"
    signature = init_state(state, {"test": "dual-eval"})
    return dict(PATH=str(Path(sys.executable).parent) + os.pathsep + os.defpath,
                RUN_ROOT=str(run), STATE_DIR=str(state.parent), STATE_FILE=str(state), FINGERPRINT=signature,
                CURRENT_SOLVER=str(model), QUESTION_GPU_IDS="0,1,2,3", STORAGE_PATH=str(tmp_path / "storage"),
                SOLVER_EVAL_DUAL="1", NO_EVAL="1", round="1")


def run_eval(tmp_path, env):
    return subprocess.run(["bash", "run_eval.sh"], cwd=tmp_path, env=env,
                          capture_output=True, text=True, timeout=30)


def test_dual_eval_records_both_modes_then_skips_them_on_resume(tmp_path):
    env = setup_pipeline(tmp_path)
    result = run_eval(tmp_path, env)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "NEXT_ROUND" in result.stdout
    calls = [json.loads(line) for line in (tmp_path / "calls.jsonl").read_text().splitlines()]
    assert [call["mode"] for call in calls] == ["rzero-original", "corrected"]
    for call in calls:
        assert call["model"] == env["CURRENT_SOLVER"]
        assert (call["gpu"], call["tmp"], call["timeout"]) == ("0,1,2,3", "/tmp", "3600")
    for mode in ("rzero-original", "corrected"):
        directory = Path(env["RUN_ROOT"]) / "evaluations/solver_v1" / mode
        assert "complete" in (directory / "summary.csv").read_text()
        assert mode in (directory / "summary.md").read_text()
        manifest = json.loads(next(directory.glob("*/manifest.json")).read_text())
        assert manifest["judge"]["prompt_mode"] == mode
        assert Path(manifest["models"][0]["checkpoint_results_dir"]).is_dir()
    result = run_eval(tmp_path, env)
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.count("skip completed stage") == 2
    assert len((tmp_path / "calls.jsonl").read_text().splitlines()) == 2


def test_failed_second_mode_stops_and_resume_only_retries_that_mode(tmp_path):
    env = setup_pipeline(tmp_path)
    (tmp_path / "fail_corrected").touch()
    result = run_eval(tmp_path, env)
    assert result.returncode != 0
    assert "NEXT_ROUND" not in result.stdout
    (tmp_path / "fail_corrected").unlink()
    result = run_eval(tmp_path, env)
    assert result.returncode == 0, result.stdout + result.stderr
    calls = [json.loads(line)["mode"] for line in (tmp_path / "calls.jsonl").read_text().splitlines()]
    assert calls == ["rzero-original", "corrected", "corrected"]
    directory = Path(env["RUN_ROOT"]) / "evaluations/solver_v1/corrected"
    assert len(list(directory.glob("*/manifest.json"))) == 2  # Failed attempt retained.
    assert "complete" in (directory / "summary.csv").read_text()


def test_disabled_option_keeps_no_eval_behavior(tmp_path):
    env = setup_pipeline(tmp_path)
    result = run_eval(tmp_path, dict(env, SOLVER_EVAL_DUAL="0"))
    assert result.returncode == 0, result.stdout + result.stderr
    assert not (tmp_path / "calls.jsonl").exists()


def test_existing_training_can_enable_evaluation_on_resume(tmp_path):
    env = {"SOLVER_NEGATIVE_ONLY": "1"}
    result, state = pipeline_init(tmp_path, env)
    assert result.returncode == 0, result.stderr
    result, resumed = pipeline_init(tmp_path, dict(env, SOLVER_EVAL_DUAL="1"), resume=True)
    assert result.returncode == 0, result.stderr
    assert resumed == state
