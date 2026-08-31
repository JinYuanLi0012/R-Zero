import ast
from contextlib import redirect_stdout
from io import StringIO
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from types import ModuleType
from typing import Dict, List
from unittest.mock import patch


CALLER_PENALTY = Path(__file__).parents[3] / "examples" / "reward_function" / "caller_penalty.py"


def _load_compute_score(final_results, penalties):
    tree = ast.parse(CALLER_PENALTY.read_text(encoding="utf-8"), filename=str(CALLER_PENALTY))
    function = next(
        node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "compute_score"
    )
    module = ast.Module(body=[function], type_ignores=[])
    namespace = {
        "Dict": Dict,
        "List": List,
        "cluster_share_per_problem": lambda *_args, **_kwargs: penalties,
        "extract_boxed_content": lambda _text: "answer",
        "generate_results": lambda *_args, **_kwargs: final_results,
        "json": json,
        "os": os,
        "re": re,
    }
    exec(compile(module, str(CALLER_PENALTY), "exec"), namespace)
    return namespace["compute_score"]


def _run_compute_score(
    final_results, penalties, environment, semantic_stats=None, ready_files=None, semantic_calls=None
):
    compute_score = _load_compute_score(final_results, penalties)
    semantic_module = ModuleType("methods.validity_rzero.semantic_mc_online")
    def semantic_penalties(_questions, **kwargs):
        if semantic_calls is not None:
            semantic_calls.append(kwargs)
        if semantic_stats is not None:
            return semantic_stats
        raise AssertionError("semantic dependency must not be used")
    semantic_module.compute_online_semantic_penalties = semantic_penalties
    previous_cwd = os.getcwd()
    try:
        with tempfile.TemporaryDirectory() as temporary_directory:
            os.chdir(temporary_directory)
            output = StringIO()
            with patch.dict(os.environ, environment, clear=True), \
                 patch.dict(sys.modules, {semantic_module.__name__: semantic_module}), \
                 redirect_stdout(output):
                kwargs = (
                    {"validity_rzero_semantic_gpu_ready_file": ready_files}
                    if ready_files is not None
                    else {}
                )
                scores = compute_score(
                    ["<question>question</question> \\boxed{answer}"] * len(final_results),
                    ["answer"] * len(final_results),
                    **kwargs,
                )
    finally:
        os.chdir(previous_cwd)
    return scores, output.getvalue()


def _validity_result(base_reward=0.4, decision="VALID", invalid_votes=0):
    return {
        "question": "question",
        "questioner_base_reward": base_reward,
        "invalid_votes": invalid_votes,
        "total_votes": 9,
        "validity_decision": decision,
        "validity_penalty": base_reward if decision == "INVALID" else 0.0,
        "math_frontier_score": base_reward if decision == "VALID" else 0.0,
    }


def test_validity_diversity_penalty_scales_and_caps():
    similarities = [0.02, 0.09, 0.20]
    scores, log_output = _run_compute_score(
        [_validity_result()] * len(similarities),
        similarities,
        {
            "VALIDITY_RZERO_ENABLED": "1",
        },
    )

    expected_penalties = [0.10, 0.45, 0.50]
    for score, similarity, expected_penalty in zip(scores, similarities, expected_penalties):
        assert abs(score["similarity_penalty"] - similarity) < 1e-12
        assert score["diversity_lambda"] == 5.0
        assert abs(score["diversity_penalty"] - expected_penalty) < 1e-12
        assert abs(score["overall"] - (0.4 - expected_penalty)) < 1e-12

    logged = [
        json.loads(line.split(" ", 1)[1])
        for line in log_output.splitlines()
        if line.startswith("[validity_rzero][questioner_reward] ")
    ]
    assert [item["similarity_penalty"] for item in logged] == similarities
    assert [item["diversity_lambda"] for item in logged] == [5.0, 5.0, 5.0]
    assert all(
        abs(item["diversity_penalty"] - expected) < 1e-12
        for item, expected in zip(logged, expected_penalties)
    )


def test_baseline_reward_is_unchanged_when_validity_is_disabled():
    scores, _ = _run_compute_score(
        [{"question": "question", "score": 0.3}],
        [0.09],
        {
            "VALIDITY_RZERO_ENABLED": "0",
            "VALIDITY_RZERO_DIVERSITY_LAMBDA": "not-a-number",
        },
    )

    assert abs(scores[0]["overall"] - (min(0.3, 1 - 0.3) - 0.09)) < 1e-12
    assert scores[0]["accuracy"] == 0.09
    assert "diversity_penalty" not in scores[0]


def test_invalid_majority_keeps_negative_base_reward_and_subtracts_diversity():
    base_reward = 0.5 - 5 / 9
    scores, _ = _run_compute_score(
        [_validity_result(base_reward=base_reward, decision="INVALID", invalid_votes=5)],
        [0.20],
        {
            "VALIDITY_RZERO_ENABLED": "1",
        },
    )

    assert abs(scores[0]["diversity_penalty"] - 0.5) < 1e-12
    assert abs(scores[0]["overall"] - (base_reward - 0.5)) < 1e-12


def test_legacy_bleu_mode_remains_reproducible_without_scaling():
    scores, _ = _run_compute_score(
        [_validity_result()], [0.20],
        {"VALIDITY_RZERO_ENABLED": "1", "VALIDITY_RZERO_DIVERSITY_MODE": "bleu_legacy"},
    )
    assert scores[0]["diversity_lambda"] is None
    assert scores[0]["diversity_penalty"] == 0.20
    assert abs(scores[0]["overall"] - 0.20) < 1e-12


def test_semantic_mode_subtracts_same_over_successfully_parsed_for_valid_and_invalid():
    invalid_base = 0.5 - 5 / 9
    stats = [
        {"same_count": 2, "compared_count": 4, "parse_failure_count": 1, "semantic_penalty": 0.5},
        {"same_count": 1, "compared_count": 4, "parse_failure_count": 0, "semantic_penalty": 0.25},
    ]
    scores, logs = _run_compute_score(
        [
            _validity_result(base_reward=0.4),
            _validity_result(base_reward=invalid_base, decision="INVALID", invalid_votes=5),
        ],
        [999, 999],
        {"VALIDITY_RZERO_ENABLED": "1", "VALIDITY_RZERO_DIVERSITY_MODE": "semantic_mc"},
        semantic_stats=stats,
    )
    assert abs(scores[0]["overall"] - (0.4 - 2 / 4)) < 1e-12
    assert abs(scores[1]["overall"] - (invalid_base - 1 / 4)) < 1e-12
    assert scores[0]["same_count"] == 2
    assert scores[0]["compared_count"] == 4
    assert scores[0]["parse_failure_count"] == 1
    assert '"diversity_mode": "semantic_mc"' in logs


def test_semantic_batch_forwards_one_shared_gpu_barrier():
    calls = []
    _run_compute_score(
        [_validity_result()],
        [0.1],
        {"VALIDITY_RZERO_ENABLED": "1", "VALIDITY_RZERO_DIVERSITY_MODE": "semantic_mc"},
        semantic_stats=[{
            "same_count": 0,
            "compared_count": 1,
            "parse_failure_count": 0,
            "semantic_penalty": 0.0,
        }],
        ready_files=["/tmp/step.json", "/tmp/step.json"],
        semantic_calls=calls,
    )
    assert calls == [{"gpu_ready_file": "/tmp/step.json"}]


def test_disabled_baseline_never_imports_semantic_even_if_mode_is_set():
    scores, _ = _run_compute_score(
        [{"question": "question", "score": 0.3}], [0.09],
        {
            "VALIDITY_RZERO_ENABLED": "0",
            "VALIDITY_RZERO_DIVERSITY_MODE": "semantic_mc",
            "VALIDITY_RZERO_SEMANTIC_MODEL": "must-not-load",
        },
    )
    assert abs(scores[0]["overall"] - (0.3 - 0.09)) < 1e-12
