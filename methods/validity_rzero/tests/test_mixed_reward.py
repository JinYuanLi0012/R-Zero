from examples.reward_function.math import compute_score as math_score
from methods.validity_rl.validity_reward import compute_score as validity_score
from methods.validity_rzero.mixed_reward import compute_score


def test_dispatches_math_and_validity_rewards_exactly():
    predicts = [r"<think>x</think> \boxed{2}", r"<think>x</think> \boxed{INVALID}"]
    targets = ["2", "INVALID"]
    result = compute_score(predicts, targets, ["rzero", "terra"])
    assert result[0]["overall"] == math_score(predicts[:1], targets[:1])[0]["overall"]
    assert result[1]["overall"] == validity_score(predicts[1:], targets[1:])[0]["overall"]
    assert result[0]["rzero_count"] == 1
    assert result[0]["terra_count"] == 1
    assert result[0]["actual_replay_ratio"] == 0.5


def test_false_invalid_penalty_only_applies_to_terra_source():
    prediction = r"<think>x</think> \boxed{INVALID}"
    result = compute_score([prediction, prediction], ["2", "2"], ["rzero", "terra"])
    assert result[0]["overall"] == 0.1
    assert result[1]["overall"] == -0.5
