import pytest

from methods.validity_rzero.gating import (
    PHASE_A_MATH_VOTES,
    PHASE_B_MATH_VOTES,
    evaluate_validity_responses,
    valid_positions,
)


def responses(invalid_votes: int):
    return [r"<think>broken</think> \boxed{INVALID}"] * invalid_votes + [
        r"<think>valid</think> \boxed{12}"
    ] * (9 - invalid_votes)


def test_four_invalid_votes_take_valid_path():
    result = evaluate_validity_responses(responses(4))
    assert result["validity_decision"] == "VALID"
    assert result["validity_penalty"] == 0.0


def test_five_invalid_votes_receive_boundary_penalty():
    result = evaluate_validity_responses(responses(5))
    assert result["validity_decision"] == "INVALID"
    assert result["validity_penalty"] == pytest.approx(-1 / 18)


def test_nine_invalid_votes_receive_full_penalty():
    result = evaluate_validity_responses(responses(9))
    assert result["validity_decision"] == "INVALID"
    assert result["validity_penalty"] == -0.5


def test_invalid_mention_outside_final_box_is_not_a_vote():
    values = [
        r"<think>I checked whether this was invalid.</think> \boxed{12}",
    ] * 9
    result = evaluate_validity_responses(values)
    assert result["invalid_votes"] == 0
    assert result["validity_decision"] == "VALID"


def test_only_final_box_is_used():
    values = [r"\boxed{INVALID} corrected: \boxed{12}"] * 9
    assert evaluate_validity_responses(values)["validity_decision"] == "VALID"


def test_exactly_nine_votes_are_required():
    with pytest.raises(ValueError, match="expected 9"):
        evaluate_validity_responses(responses(4)[:-1])


def test_only_valid_rows_enter_the_fresh_math_stage():
    gates = [evaluate_validity_responses(responses(9)), evaluate_validity_responses(responses(4))]
    assert valid_positions(gates) == [1]


def test_original_math_rollout_counts_are_fixed():
    assert PHASE_A_MATH_VOTES == 10
    assert PHASE_B_MATH_VOTES == 9
