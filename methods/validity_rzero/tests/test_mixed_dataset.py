import pytest

from methods.validity_rzero.prepare_solver_dataset import build_mixed_rows, require_full_training_batch


def rzero_rows(count=8):
    return [
        {"question": f"q{index}", "answer": str(index), "score": 0.5, "discarded_by_validity": False}
        for index in range(count)
    ] + [
        {"question": "invalid", "answer": "", "score": None, "discarded_by_validity": True},
        {"question": "too easy", "answer": "1", "score": 1.0, "discarded_by_validity": False},
    ]


def terra_rows(count=10):
    return [
        {
            "id": f"t{index}",
            "question": f"terra {index}",
            "validity_rl_target": "INVALID" if index % 2 else str(index),
            "terra_validity": "INVALID" if index % 2 else "VALID",
            "canonical_final_answer": None if index % 2 else str(index),
            "answer_verified": False if index % 2 else True,
            "split": "train",
        }
        for index in range(count)
    ]


def test_mixes_only_filtered_rzero_and_terra_train_rows():
    mixed, stats = build_mixed_rows(rzero_rows(), terra_rows(), 0.3, 0.8, 0.2, seed=7)
    assert stats["rzero_sample_count"] == 8
    assert stats["terra_replay_sample_count"] == 2
    assert {row["source"] for row in mixed} == {"rzero", "terra"}
    assert all(row["problem"] != "invalid" for row in mixed)


def test_replay_selection_is_deterministic():
    first, _ = build_mixed_rows(rzero_rows(), terra_rows(), 0.3, 0.8, 0.2, seed=11)
    second, _ = build_mixed_rows(rzero_rows(), terra_rows(), 0.3, 0.8, 0.2, seed=11)
    assert first == second


def test_validation_split_can_never_enter_replay():
    rows = terra_rows()
    rows[0]["split"] = "validation"
    with pytest.raises(ValueError, match="not from the train split"):
        build_mixed_rows(rzero_rows(), rows, 0.3, 0.8, 0.2, seed=1)


def test_requires_one_complete_solver_batch():
    with pytest.raises(RuntimeError, match="increase SOLVER_GENERATE_SAMPLES"):
        require_full_training_batch(511, 512)
    require_full_training_batch(512, 512)
