from contextlib import nullcontext
from io import StringIO
import os
import tempfile
from unittest.mock import patch

from methods.validity_rzero import semantic_novelty_gate_online
from methods.validity_rzero.semantic_judge_offline.semantic_pair_prompt_formal import (
    PROMPT_VERSION,
    build_prompt,
)


def test_online_novelty_uses_candidate_specific_k_and_existing_judge_protocol():
    captured = {}
    events = []

    class Service:
        gpu_ids = ("2", "3")

    def fake_gpu(tasks, model, gpu_ids, work_dir, **kwargs):
        events.append("workers")
        captured.update({
            "tasks": tasks,
            "model": model,
            "gpu_ids": gpu_ids,
            "work_dir": work_dir,
            "kwargs": kwargs,
        })
        return (
            {
                task.cache_key: {"parsed_label": "DIFFERENT", "attempts": 1}
                for task in tasks
            },
            {
                "wall_seconds": 2.5,
                "retry": {
                    "first_pass_batch_count": 1,
                    "first_pass_failure_count": 0,
                    "retry_batch_count": 0,
                    "retried_request_count": 0,
                },
                "prefix_cache": {
                    "enabled_explicitly": True,
                    "token_hit_rate": 0.5,
                },
            },
        )

    questions = [f"candidate {index}" for index in range(12)]
    with tempfile.TemporaryDirectory() as directory, \
         patch.dict(os.environ, {
             "STORAGE_PATH": directory,
             "VALIDITY_RZERO_NOVELTY_K": "8",
             "VALIDITY_RZERO_NOVELTY_SEED": "43",
             "VALIDITY_RZERO_SEMANTIC_PANEL_SIZE": "1",
             "VALIDITY_RZERO_SEMANTIC_WORKER_BATCH_SIZE": "8192",
             "VALIDITY_RZERO_SEMANTIC_GPU_IDS": "0,1,2,3",
             "VALIDITY_RZERO_SEMANTIC_GPU_MEMORY_UTILIZATION": "0.80",
         }, clear=True), \
         patch.object(
             semantic_novelty_gate_online,
             "resolve_frozen_model",
             return_value=("/frozen/base", "rev"),
         ), \
         patch.object(
             semantic_novelty_gate_online.SolverServiceConfig,
             "from_environment",
             return_value=Service(),
         ), \
         patch.object(
             semantic_novelty_gate_online,
             "semantic_gpu_handoff",
             return_value=nullcontext(),
         ), \
         patch.object(
             semantic_novelty_gate_online,
             "wait_until_ready",
             side_effect=lambda path: events.append(f"barrier:{path}") or 1.25,
         ), \
         patch.object(
             semantic_novelty_gate_online,
             "run_gpu_tasks",
             side_effect=fake_gpu,
         ), \
         patch.object(
             semantic_novelty_gate_online.shutil,
             "rmtree",
         ) as cleanup, \
         patch("sys.stdout", new_callable=StringIO) as output:
        novelty = semantic_novelty_gate_online.compute_online_novelty(
            questions,
            gpu_ready_file="/barriers/step.json",
        )

    assert all(item["novelty"] == 1 for item in novelty)
    assert all(item["compared_count"] == 8 for item in novelty)
    assert captured["model"] == "/frozen/base"
    assert captured["gpu_ids"] == ["0", "1", "2", "3"]
    assert captured["kwargs"] == {
        "max_tokens": 1024,
        "seed": 42,
        "gpu_memory_utilization": 0.80,
        "batch_size": 8192,
    }
    assert events == ["barrier:/barriers/step.json", "workers"]
    tasks = captured["tasks"]
    assert len(tasks) == 12 * 8
    assert all(task.candidate_index != task.panel_index for task in tasks)
    assert all(task.question_a == questions[task.candidate_index] for task in tasks)
    assert all(task.question_b == questions[task.panel_index] for task in tasks)
    assert all(task.prompt == build_prompt(task.question_a, task.question_b) for task in tasks)
    reference_sets = {
        candidate: tuple(
            task.panel_index for task in tasks if task.candidate_index == candidate
        )
        for candidate in range(len(questions))
    }
    assert all(len(references) == 8 for references in reference_sets.values())
    assert len(set(reference_sets.values())) > 1
    log = output.getvalue()
    assert f"prompt_version={PROMPT_VERSION}" in log
    assert "novelty_k=8" in log
    assert "novelty_seed=43" in log
    assert "semantic_gpus=0,1,2,3" in log
    assert "parse_failure_after_retry=0.000000" in log
    assert "prefix_cache_token_hit_rate=0.500000" in log
    cleanup.assert_called_once_with(captured["work_dir"], ignore_errors=True)


def test_online_novelty_preserves_worker_artifacts_on_failure():
    captured = {}

    class Service:
        gpu_ids = ("2", "3")

    def failed_gpu(_tasks, _model, _gpu_ids, work_dir, **_kwargs):
        captured["work_dir"] = work_dir
        (work_dir / "semantic_failure.json").write_text("failure\n", encoding="utf-8")
        raise RuntimeError("gpu 0 failed")

    with tempfile.TemporaryDirectory() as directory, \
         patch.dict(os.environ, {
             "STORAGE_PATH": directory,
             "VALIDITY_RZERO_NOVELTY_K": "1",
             "VALIDITY_RZERO_NOVELTY_SEED": "43",
             "VALIDITY_RZERO_SEMANTIC_GPU_IDS": "0,1,2,3",
         }, clear=True), \
         patch.object(
             semantic_novelty_gate_online,
             "resolve_frozen_model",
             return_value=("/frozen/base", "rev"),
         ), \
         patch.object(
             semantic_novelty_gate_online.SolverServiceConfig,
             "from_environment",
             return_value=Service(),
         ), \
         patch.object(
             semantic_novelty_gate_online,
             "semantic_gpu_handoff",
             return_value=nullcontext(),
         ), \
         patch.object(
             semantic_novelty_gate_online,
             "run_gpu_tasks",
             side_effect=failed_gpu,
         ), \
         patch("sys.stdout", new_callable=StringIO) as output:
        try:
            semantic_novelty_gate_online.compute_online_novelty(["q0", "q1"])
        except RuntimeError as error:
            assert str(error) == "gpu 0 failed"
        else:
            raise AssertionError("worker failure must propagate")

        work_dir = captured["work_dir"]
        assert work_dir.is_dir()
        assert (work_dir / "semantic_failure.json").read_text() == "failure\n"
        assert "preserving failed semantic work directory" in output.getvalue()
