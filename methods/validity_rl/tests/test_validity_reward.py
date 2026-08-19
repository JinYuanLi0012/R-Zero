import pytest

from methods.validity_rl.validity_reward import compute_score


def score(predict: str, target: str):
    return compute_score([predict], [target])[0]


def test_valid_correct_answer():
    assert score(r"<think>done</think> \boxed{12}", "12")["overall"] == 1.0


def test_valid_equivalent_answer():
    assert score(r"<think>done</think> \boxed{0.5}", r"\frac{1}{2}")["overall"] == 1.0


def test_valid_wrong_answer():
    assert score(r"<think>done</think> \boxed{13}", "12")["overall"] == 0.0


def test_valid_false_invalid_is_penalized():
    result = score(r"<think>unsure</think> \boxed{ invalid }", "12")
    assert result["overall"] == -0.5
    assert result["false_invalid"] == 1.0


def test_invalid_correct_rejection():
    result = score(r"<think>contradiction</think> \boxed{INVALID}", "INVALID")
    assert result["overall"] == 1.0
    assert result["pred_invalid"] == 1.0


def test_invalid_math_answer_is_zero():
    assert score(r"<think>guessed</think> \boxed{4}", "INVALID")["overall"] == 0.0


@pytest.mark.parametrize("predict", ["no final answer", r"<think>done</think> \boxed{}"])
def test_missing_or_empty_box_is_malformed(predict):
    result = score(predict, "12")
    assert result["overall"] == -0.1
    assert result["format_failure"] == 1.0


def test_invalid_mention_in_reasoning_is_ignored():
    predict = (
        "<think>I checked whether the problem was invalid. "
        r"It is actually consistent.</think> \boxed{12}"
    )
    result = score(predict, "12")
    assert result["overall"] == 1.0
    assert result["pred_invalid"] == 0.0


def test_only_the_final_box_is_scored():
    predict = r"<think>first attempt</think> \boxed{INVALID} Correction: \boxed{12}"
    assert score(predict, "12")["overall"] == 1.0


def test_batch_lengths_must_match():
    with pytest.raises(ValueError):
        compute_score([r"\boxed{1}"], [])
