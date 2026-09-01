from methods.validity_rzero.semantic_mc import PairInstance, cache_context
from methods.validity_rzero.semantic_novelty_gate import (
    aggregate_novelty,
    build_novelty_pair_plan,
    novelty_training_diagnostics,
    sample_references_per_candidate,
)


def test_per_candidate_sampling_is_deterministic_distinct_and_nonself():
    indices = list(range(12))
    first = sample_references_per_candidate(indices, 8, 43)
    second = sample_references_per_candidate(indices, 8, 43)
    assert first == second
    assert all(len(references) == 8 for references in first.values())
    assert all(index not in references for index, references in first.items())
    assert len({tuple(references) for references in first.values()}) > 1


def test_identical_text_at_different_index_remains_a_reference_pair():
    questions = {0: "same text", 1: "same text", 2: "other text"}
    references, instances, tasks = build_novelty_pair_plan(
        questions,
        [0, 1, 2],
        8,
        43,
        cache_context("/frozen", orientation="candidate_then_reference_v1"),
        prompt_builder=lambda a, b: f"{a}|{b}",
    )
    assert references[0] == [1, 2] or references[0] == [2, 1]
    identical = next(item for item in instances if item.candidate_index == 0 and item.panel_index == 1)
    assert tasks[identical.cache_key].question_a == "same text"
    assert tasks[identical.cache_key].question_b == "same text"


def test_any_same_rejects_no_same_passes_and_parse_failure_fails_open():
    instances = [
        PairInstance(0, 1, "same"),
        PairInstance(0, 2, "different"),
        PairInstance(1, 0, "failure"),
    ]
    aggregates = aggregate_novelty(
        [0, 1],
        instances,
        {
            "same": {"parsed_label": "SAME_TYPE"},
            "different": {"parsed_label": "DIFFERENT"},
            "failure": {"parsed_label": None},
        },
    )
    assert aggregates[0] == {
        "same_count": 1,
        "compared_count": 2,
        "parse_failure_count": 0,
        "novelty": 0,
    }
    assert aggregates[1] == {
        "same_count": 0,
        "compared_count": 0,
        "parse_failure_count": 1,
        "novelty": 1,
    }


def test_real_group_survivor_metrics_include_zero_one_and_multi_survivor_groups():
    rows = [
        {"question": "q0", "validity_decision": "VALID"},
        {"question": "q1", "validity_decision": "VALID"},
        {"question": "q2", "validity_decision": "INVALID"},
        {"question": "q3", "validity_decision": "VALID"},
        {"question": "q4", "validity_decision": "VALID"},
        {"question": "q5", "validity_decision": "VALID"},
    ]
    stats = [
        {"novelty": 1, "same_count": 0, "compared_count": 8, "parse_failure_count": 0},
        {"novelty": 0, "same_count": 1, "compared_count": 8, "parse_failure_count": 0},
        {"novelty": 1, "same_count": 0, "compared_count": 7, "parse_failure_count": 1},
        {"novelty": 0, "same_count": 2, "compared_count": 8, "parse_failure_count": 0},
        {"novelty": 1, "same_count": 0, "compared_count": 8, "parse_failure_count": 0},
        {"novelty": 1, "same_count": 0, "compared_count": 8, "parse_failure_count": 0},
    ]
    metrics = novelty_training_diagnostics(rows, stats, ["a", "a", "b", "b", "c", "c"])
    assert metrics["mean_survivors_per_grpo_group"] == 1.0
    assert metrics["zero_survivor_grpo_group_rate"] == 1 / 3
    assert metrics["one_survivor_grpo_group_rate"] == 1 / 3
    assert metrics["multi_survivor_grpo_group_rate"] == 1 / 3
    assert metrics["semantic_parse_failure_rate"] == 1 / 48
