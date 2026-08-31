from contextlib import nullcontext
from io import StringIO
import os
import tempfile
from unittest.mock import patch

from methods.validity_rzero import semantic_mc_online
from methods.validity_rzero.semantic_judge_offline.semantic_pair_prompt_formal import (
    PROMPT_TEMPLATE,
    PROMPT_VERSION,
    build_prompt,
)


EXPECTED_PROMPT = r"""You are judging whether two generated math problems are repetitions of the
same recurring exercise pattern.

Choose SAME_TYPE when the two problems have essentially the same distinctive
mathematical setup and ask the same kind of task, so that they feel like
variations of the same exercise.

Differences in constants, coefficients, variables, formulas, bounds, or other
local details do not by themselves make the problems different.

Do not choose SAME_TYPE merely because the problems share a broad topic,
similar wording, presentation style.

If the common pattern is not clear and specific, choose DIFFERENT.

Briefly compare the exercise pattern of the two problems, then end with exactly

\boxed{SAME_TYPE}

or

\boxed{DIFFERENT}.

Question A:
{question_a}

Question B:
{question_b}

Analysis:"""


def test_formal_prompt_is_exact_and_keeps_strict_box_contract():
    assert PROMPT_VERSION == "semantic-pair-formal-recurring-exercise-v1"
    assert PROMPT_TEMPLATE == EXPECTED_PROMPT
    prompt = build_prompt("candidate", "reference")
    assert "Question A:\ncandidate" in prompt
    assert "Question B:\nreference" in prompt
    assert prompt.endswith("Analysis:")


def test_online_protocol_uses_candidate_prefix_batch8192_deferred_retry_and_cache():
    captured = {}

    class Service:
        gpu_ids = ("2", "3")

    def fake_gpu(tasks, model, gpu_ids, work_dir, **kwargs):
        captured.update({
            "tasks": tasks,
            "model": model,
            "gpu_ids": gpu_ids,
            "work_dir": work_dir,
            "kwargs": kwargs,
        })
        return (
            {task.cache_key: {"parsed_label": "DIFFERENT", "attempts": 1} for task in tasks},
            {
                "wall_seconds": 12.5,
                "retry": {
                    "first_pass_batch_count": 2,
                    "first_pass_failure_count": 3,
                    "retry_batch_count": 1,
                    "retried_request_count": 3,
                },
                "prefix_cache": {
                    "enabled_explicitly": True,
                    "token_hit_rate": 0.75,
                },
            },
        )

    with tempfile.TemporaryDirectory() as directory, \
         patch.dict(os.environ, {
             "STORAGE_PATH": directory,
             "VALIDITY_RZERO_SEMANTIC_PANEL_SIZE": "2",
             "VALIDITY_RZERO_SEMANTIC_PANEL_SEED": "43",
             "VALIDITY_RZERO_SEMANTIC_WORKER_BATCH_SIZE": "8192",
         }, clear=True), \
         patch.object(semantic_mc_online, "resolve_frozen_model", return_value=("/frozen/base", "rev")), \
         patch.object(semantic_mc_online.SolverServiceConfig, "from_environment", return_value=Service()), \
         patch.object(semantic_mc_online, "semantic_gpu_handoff", return_value=nullcontext()), \
         patch.object(semantic_mc_online, "run_gpu_tasks", side_effect=fake_gpu), \
         patch("sys.stdout", new_callable=StringIO) as output:
        penalties = semantic_mc_online.compute_online_semantic_penalties(
            ["candidate zero", "candidate one", "candidate two"]
        )

    assert all(item["semantic_penalty"] == 0.0 for item in penalties)
    assert captured["kwargs"]["batch_size"] == 8192
    assert captured["model"] == "/frozen/base"
    assert captured["gpu_ids"] == ["2", "3"]
    tasks = captured["tasks"]
    assert all(
        task.question_a == ["candidate zero", "candidate one", "candidate two"][task.candidate_index]
        for task in tasks
    )
    assert all(task.prompt == build_prompt(task.question_a, task.question_b) for task in tasks)
    candidate_order = [task.candidate_index for task in tasks]
    assert candidate_order == sorted(candidate_order)
    log = output.getvalue()
    assert f"prompt_version={PROMPT_VERSION}" in log
    assert "worker_batch_size=8192" in log
    assert "deferred_retry_batches=1" in log
    assert "prefix_cache_enabled=True" in log
    assert "prefix_cache_token_hit_rate=0.750000" in log
