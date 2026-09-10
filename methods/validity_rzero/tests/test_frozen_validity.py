"""CPU contracts for the fixed judge; GPU inference is mocked."""
import ast
from contextlib import contextmanager
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from methods.validity_rzero import frozen_validity as frozen
from methods.validity_rzero import service_handoff
from methods.validity_rzero.prepare_solver_dataset import build_mixed_rows

ROOT = Path(__file__).parents[3]


def envelope(model, question="q", invalid=5):
    return {"model": str(model.resolve()), "question": question,
            "responses": [r"\boxed{INVALID}"] * invalid + [r"\boxed{12}"] * (9 - invalid)}


@pytest.mark.parametrize("invalid", [4, 5, 9])
def test_fixed_gate_uses_unchanged_nine_vote_parser(tmp_path, monkeypatch, invalid):
    monkeypatch.setenv("VALIDITY_RZERO_VALIDITY_JUDGE_MODEL", str(tmp_path))
    row = {"question": "q", frozen.GATE_KEY: envelope(tmp_path, invalid=invalid)}
    gate = frozen.checked_gate(row)
    assert gate["validity_decision"] == ("INVALID" if invalid >= 5 else "VALID")
    assert gate["validity_penalty"] == (0.5 - invalid / 9 if invalid >= 5 else 0)
    assert gate["validity_judge_model"] == str(tmp_path.resolve())
    with pytest.raises(ValueError, match="mismatch"):
        frozen.checked_gate({**row, "question": "different"})
    with pytest.raises(KeyError):
        frozen.checked_gate({"question": "q"})


def test_phase_a_handoff_restores_current_solver_and_preserves_indices(tmp_path, monkeypatch):
    config = SimpleNamespace(gpu_ids=("2", "3"), model_path="current-round-solver")
    events = []

    @contextmanager
    def handoff(actual):
        assert actual.model_path == "current-round-solver"
        events.append("stop_current")
        try:
            yield
        finally:
            events.append("restore_current")

    def workers(rows, gpu_ids, phase):
        assert gpu_ids == ["2", "3"] and phase == "a"
        events.append("fixed_judge")
        return [{**r, frozen.GATE_KEY: envelope(tmp_path, r["question"])} for r in rows]

    monkeypatch.setattr(service_handoff.SolverServiceConfig, "from_environment", lambda: config)
    monkeypatch.setattr(service_handoff, "semantic_gpu_handoff", handoff)
    monkeypatch.setattr(frozen, "run_workers", workers)
    rows = [{"question": "q", "answer": "a"}, {"question": "", "answer": ""}, {"question": "q", "answer": "a"}]
    output = frozen.annotate_phase_a(rows)
    assert events == ["stop_current", "fixed_judge", "restore_current"]
    assert output[1] == rows[1]
    assert frozen.GATE_KEY in output[0] and frozen.GATE_KEY in output[2]
    assert all(frozen.GATE_KEY not in r for r in rows)
    def fail(*args):
        raise RuntimeError("worker failed")
    monkeypatch.setattr(frozen, "run_workers", fail)
    with pytest.raises(RuntimeError, match="worker failed"):
        frozen.annotate_phase_a(rows)
    assert events[-2:] == ["stop_current", "restore_current"]


def test_both_math_paths_skip_current_solver_validity_in_frozen_mode(tmp_path, monkeypatch):
    monkeypatch.setenv("VALIDITY_RZERO_VALIDITY_JUDGE_MODEL", str(tmp_path))
    row = {"question": "q", frozen.GATE_KEY: envelope(tmp_path)}
    for filename in ("vllm_service_init/start_vllm_server.py", "question_evaluate/evaluate.py"):
        tree = ast.parse((ROOT / filename).read_text())
        branch = next(n for n in ast.walk(tree) if isinstance(n, ast.If)
                      and "VALIDITY_RZERO_VALIDITY_JUDGE_MODE" in ast.unparse(n.test))
        def unexpected(*args, **kwargs):
            raise AssertionError("current Solver must not generate validity votes")
        namespace = {"os": os, "data": [row], "valid_indices": [0], "correct_data": [row],
                     "generate": unexpected, "model": SimpleNamespace(generate=unexpected)}
        with patch.dict(os.environ, {"VALIDITY_RZERO_VALIDITY_JUDGE_MODE": "frozen"}):
            exec(compile(ast.Module(body=[branch], type_ignores=[]), filename, "exec"), namespace)
        assert namespace["gates"][0]["invalid_votes"] == 5


def test_no_replay_does_not_iterate_terra_and_keeps_all_filtered_math():
    class NeverRead:
        def __iter__(self):
            raise AssertionError("zero replay must never load/read Terra")
    rows = [{"question": f"q{i}", "answer": "1", "score": .5} for i in range(20)]
    rows += [{"question": "invalid", "answer": "1", "score": .5, "discarded_by_validity": True}]
    result, stats = build_mixed_rows(rows, NeverRead(), .3, .8, 0, 1)
    assert len(result) == 20 and {r["source"] for r in result} == {"rzero"}
    assert stats["terra_replay_sample_count"] == stats["actual_replay_ratio"] == 0
    assert stats["discarded_by_validity_count"] == 1


def test_phase_b_prepass_preserves_shards_and_non_evaluated_rows(tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_PATH", str(tmp_path))
    monkeypatch.setenv("QUESTION_GPU_IDS", "0,1")
    root = tmp_path / "generated_question"
    root.mkdir()
    for shard in range(2):
        (root / f"run_{shard}.json").write_text(json.dumps([
            {"question": f"q{shard}", "score": 0}, {"question": "skip", "score": 1}]))
    def workers(rows, gpus, phase):
        assert gpus == ["0", "1"] and phase == "b"
        return [{**r, frozen.GATE_KEY: envelope(tmp_path, r["question"])} for r in rows]
    monkeypatch.setattr(frozen, "run_workers", workers)
    frozen.phase_b_prepass("run")
    for shard in range(2):
        rows = json.loads((root / f"run_{shard}.json").read_text())
        assert rows[0]["question"] == f"q{shard}" and frozen.GATE_KEY in rows[0]
        assert rows[1] == {"question": "skip", "score": 1}


@pytest.mark.parametrize("failure", [False, True])
def test_worker_supervisor_releases_gpus_and_clears_pids(tmp_path, monkeypatch, failure):
    from methods.validity_rzero import semantic_mc_gpu
    monkeypatch.setenv("STORAGE_PATH", str(tmp_path))
    monkeypatch.setenv("VALIDITY_RZERO_VALIDITY_JUDGE_MODEL", str(tmp_path))
    pidfile = tmp_path / "pids"
    monkeypatch.setenv("VALIDITY_RZERO_FROZEN_PID_FILE", str(pidfile))
    events = []
    def popen(command, **kwargs):
        source = Path(command[command.index("--worker-input") + 1])
        target = Path(command[command.index("--worker-output") + 1])
        rows = json.loads(source.read_text())
        assert kwargs["start_new_session"]
        assert command[command.index("--model") + 1] == str(tmp_path.resolve())
        target.write_text(json.dumps([{**envelope(tmp_path, r["question"]), "index": r["index"]} for r in rows]))
        return SimpleNamespace(pid=123, returncode=1 if failure else 0, poll=lambda: 1 if failure else 0)
    monkeypatch.setattr(frozen.subprocess, "Popen", popen)
    monkeypatch.setattr(semantic_mc_gpu, "terminate_process_groups", lambda p: events.append("terminate"))
    monkeypatch.setattr(service_handoff, "wait_gpus_released", lambda *a: events.append("released"))
    if failure:
        with pytest.raises(RuntimeError, match="failed"):
            frozen.run_workers([{"question": "q"}], ["2", "3"], "a")
    else:
        result = frozen.run_workers([{"question": "q"}], ["2", "3"], "a")
        assert frozen.checked_gate(result[0])["invalid_votes"] == 5
    assert pidfile.read_text() == ""
    assert events == ["terminate", "released"]


@pytest.mark.parametrize("phase", ["a", "b"])
def test_worker_uses_fixed_model_original_validity_prompt_and_sampling(tmp_path, monkeypatch, phase):
    source, output = tmp_path / "input.json", tmp_path / "output.json"
    source.write_text(json.dumps([{"index": 0, "question": "test problem"}]))
    captured = {}
    class Tokenizer:
        chat_template = None
        eos_token_id = 17
    def load(path):
        assert path == str(tmp_path)
        return Tokenizer()
    class Model:
        def __init__(self, **kwargs):
            captured["model"] = kwargs
        def generate(self, prompts, sampling_params, use_tqdm):
            captured["prompts"] = prompts
            captured["sampling"] = sampling_params
            return [SimpleNamespace(outputs=[SimpleNamespace(text=r"\boxed{INVALID}")] * 9)]
    monkeypatch.setitem(sys.modules, "vllm", SimpleNamespace(LLM=Model, SamplingParams=lambda **kw: kw))
    monkeypatch.setitem(sys.modules, "transformers", SimpleNamespace(AutoTokenizer=SimpleNamespace(from_pretrained=load)))
    for key in ("VALIDITY_RZERO_PROMPT", "VLLM_SERVER_MAX_TOKENS", "VLLM_SERVER_BATCH_SIZE"):
        monkeypatch.delenv(key, raising=False)
    frozen.worker(SimpleNamespace(worker_input=str(source), worker_output=str(output),
                                  model=str(tmp_path), phase=phase, seed=1))
    assert captured["model"]["model"] == str(tmp_path)
    assert captured["sampling"] == dict(n=9, max_tokens=4096, temperature=1.0,
                                         top_p=1.0, top_k=40, stop_token_ids=[17])
    from jinja2 import Template
    template = Template((ROOT / "methods/validity_rl/validity_solver.jinja").read_text().strip())
    assert captured["prompts"] == ["user: " + template.render(content="test problem").strip()]
    assert len(json.loads(output.read_text())[0]["responses"]) == 9


def test_zero_replay_cli_does_not_load_dataset():
    tree = ast.parse((ROOT / "methods/validity_rzero/prepare_solver_dataset.py").read_text())
    assignment = next(n for n in ast.walk(tree) if isinstance(n, ast.Assign)
                      and any(isinstance(t, ast.Name) and t.id == "terra_train" for t in n.targets))
    def forbidden(*args, **kwargs):
        raise AssertionError("must not contact Terra for zero replay")
    namespace = {"args": SimpleNamespace(replay_ratio=0), "load_dataset": forbidden}
    exec(compile(ast.Module(body=[assignment], type_ignores=[]), "dataset", "exec"), namespace)
    assert namespace["terra_train"] == []


def test_frozen_fingerprint_and_zero_replay_resume_isolation(tmp_path):
    from methods.validity_rzero.tests.test_novelty_invalid_reward import pipeline_init
    model = tmp_path / "fixed_model"
    model.mkdir()
    (model / "config.json").write_text("{}")
    (model / "model.safetensors").write_bytes(b"CPU-test-placeholder")
    env = {"VALIDITY_RZERO_VALIDITY_JUDGE_MODE": "frozen",
           "VALIDITY_RZERO_VALIDITY_JUDGE_MODEL": str(model), "TERRA_REPLAY_RATIO": "0"}
    result, state = pipeline_init(tmp_path, env)
    assert result.returncode == 0, result.stderr
    assert state["configuration"]["validity_judge_model"] == str(model.resolve())
    assert state["configuration"]["terra_replay_ratio"] == "0"
    assert state["configuration"]["terra_replay_dataset"] == ""
    result, resumed = pipeline_init(tmp_path, env, resume=True)
    assert result.returncode == 0 and resumed == state
    result, _ = pipeline_init(tmp_path, {**env, "VALIDITY_RZERO_VALIDITY_JUDGE_MODE": "current_solver"}, resume=True)
    assert result.returncode != 0 and "run configuration changed" in result.stderr


def test_disabled_baseline_ignores_frozen_judge_flag(monkeypatch):
    from methods.validity_rzero.tests.test_questioner_diversity import _run_compute_score
    def forbidden(*args):
        raise AssertionError("disabled baseline must not run frozen judge")
    monkeypatch.setattr(frozen, "annotate_phase_a", forbidden)
    rows = [{"question": "q", "score": .4}]
    baseline, _ = _run_compute_score(rows, [.1], {"VALIDITY_RZERO_ENABLED": "0"})
    actual, _ = _run_compute_score(rows, [.1], {
        "VALIDITY_RZERO_ENABLED": "0", "VALIDITY_RZERO_VALIDITY_JUDGE_MODE": "frozen"})
    assert actual == baseline


def test_ablation_launcher_pins_original_k8_without_leaking_to_parent(tmp_path):
    method = tmp_path / "methods/validity_rzero"
    method.mkdir(parents=True)
    (method / "run_frozen_validity_k8.sh").write_text((ROOT / "methods/validity_rzero/run_frozen_validity_k8.sh").read_text())
    (method / "run.sh").write_text('env\n')
    environment = {"PATH": os.defpath, "STORAGE_PATH": str(tmp_path),
                   "VALIDITY_RZERO_NOVELTY_K": "16", "VALIDITY_RZERO_NOVELTY_SCOPE": "parent_domain",
                   "VALIDITY_RZERO_DOMAIN_MODE": "balanced_v1", "TERRA_REPLAY_RATIO": ".1"}
    result = subprocess.run(["bash", str(method / "run_frozen_validity_k8.sh")],
                            env=environment, check=True, capture_output=True, text=True)
    values = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
    for key, expected in {"VALIDITY_RZERO_NOVELTY_K": "8", "VALIDITY_RZERO_NOVELTY_SCOPE": "global",
                          "VALIDITY_RZERO_DOMAIN_MODE": "none", "TERRA_REPLAY_RATIO": "0",
                          "VALIDITY_RZERO_VALIDITY_JUDGE_MODE": "frozen",
                          "VALIDITY_RZERO_NOVELTY_INVALID_REWARD": "legacy"}.items():
        assert values[key] == expected
    assert values["VALIDITY_RZERO_INITIAL_SOLVER"] == values["VALIDITY_RZERO_VALIDITY_JUDGE_MODEL"]
    assert environment["VALIDITY_RZERO_NOVELTY_K"] == "16"
