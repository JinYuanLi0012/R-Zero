import pytest

from methods.validity_rl.simulate_terra_majority_vote import (
    build_one_stage_result,
    build_two_stage_result,
    cluster_math_answers,
    metrics_for,
    validity_decision,
)


@pytest.mark.parametrize(
    ("invalid_votes", "total", "expected"),
    [
        (5, 8, "INVALID"),
        (4, 8, "TIE"),
        (3, 8, "VALID"),
        (9, 16, "INVALID"),
        (8, 16, "TIE"),
        (7, 16, "VALID"),
    ],
)
def test_validity_vote_boundaries(invalid_votes, total, expected):
    assert validity_decision(invalid_votes, total) == expected


def test_math_clustering_discards_invalid_and_empty_outputs():
    result = cluster_math_answers([r"\frac{1}{2}", "0.5", "3", "", "INVALID"])
    assert result["math_outputs"] == [r"\frac{1}{2}", "0.5", "3"]
    assert result["majority_count"] == 2
    assert result["majority_answer"] == r"\frac{1}{2}"


def test_two_stage_runs_math_only_after_valid_decision():
    row = {"id": "valid", "terra_validity": "VALID", "canonical_final_answer": "2"}
    result = build_two_stage_result(
        row,
        [r"\boxed{INVALID}"] * 3 + [r"\boxed{2}"] * 5,
        [r"\boxed{2}"] * 5 + [r"\boxed{3}"] * 3,
    )
    assert result["stage1_decision"] == "VALID"
    assert result["stage2_majority_count"] == 5
    assert result["final_prediction"] == "2"
    assert result["correct"] is True

    tied = build_two_stage_result(
        row,
        [r"\boxed{INVALID}"] * 4 + [r"\boxed{2}"] * 4,
        None,
    )
    assert tied["final_prediction_type"] == "TIE"
    assert tied["stage2_outputs"] == []


def test_one_stage_and_aggregate_metrics():
    valid_row = {"id": "valid", "terra_validity": "VALID", "canonical_final_answer": "2"}
    invalid_row = {
        "id": "invalid",
        "terra_validity": "INVALID",
        "canonical_final_answer": None,
    }
    one_valid = build_one_stage_result(
        valid_row,
        [r"\boxed{INVALID}"] * 7 + [r"\boxed{2}"] * 6 + [r"\boxed{3}"] * 3,
    )
    one_invalid = build_one_stage_result(
        invalid_row,
        [r"\boxed{INVALID}"] * 9 + [r"\boxed{2}"] * 7,
    )
    two_valid = build_two_stage_result(
        valid_row,
        [r"\boxed{INVALID}"] * 3 + [r"\boxed{2}"] * 5,
        [r"\boxed{2}"] * 8,
    )
    two_invalid = build_two_stage_result(
        invalid_row,
        [r"\boxed{INVALID}"] * 5 + [r"\boxed{2}"] * 3,
        None,
    )
    records = [
        {
            "round": "v1",
            "terra_label": "VALID",
            "two_stage": two_valid,
            "one_stage": one_valid,
        },
        {
            "round": "v1",
            "terra_label": "INVALID",
            "two_stage": two_invalid,
            "one_stage": one_invalid,
        },
    ]
    for method in ("two_stage", "one_stage"):
        metrics = metrics_for(records, method)
        assert metrics["final_outcome_accuracy"] == 1.0
        assert metrics["valid_math_accuracy"] == 1.0
        assert metrics["invalid_recall"] == 1.0
        assert metrics["false_invalid_rate"] == 0.0
        assert sum(metrics["vote_statistics"]["terra_valid"].values()) == 1
        assert sum(metrics["vote_statistics"]["terra_invalid"].values()) == 1
