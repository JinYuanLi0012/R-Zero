from methods.validity_rzero.semantic_mc import (
    aggregate_semantic_penalties,
    build_pair_plan,
    cache_context,
    sample_candidate_and_panel_indices,
)
from methods.validity_rzero.semantic_mc_worker import generate_with_one_retry


def test_fixed_seed_2048_and_128_sampling():
    candidates, panel = sample_candidate_and_panel_indices(7440, 2048, 128, 42, 43)
    assert len(candidates) == len(set(candidates)) == 2048
    assert len(panel) == len(set(panel)) == 128
    assert set(panel) <= set(candidates)
    assert candidates[:10] == [5238, 912, 204, 6074, 2253, 2006, 1828, 1143, 6033, 839]
    assert panel[:10] == [3271, 5120, 1864, 3769, 1438, 479, 1124, 4312, 569, 3011]


def test_panel_text_is_not_deduplicated_and_cache_expands_pair_multiplicity():
    questions = {0: "same text", 1: "same text", 2: "other text"}
    context = cache_context("/frozen/snapshot")
    instances, tasks = build_pair_plan(questions, [0, 1, 2], [0, 1], context)

    # Only equal sample indices are self comparisons. Equal text at different
    # indices is valid, and both duplicate panel entries retain multiplicity.
    assert len(instances) == 3 * 2 - 2 == 4
    assert {(item.candidate_index, item.panel_index) for item in instances} == {
        (0, 1), (1, 0), (2, 0), (2, 1)
    }
    assert len(tasks) == 2
    multiplicities = sorted(
        sum(item.cache_key == cache_key for item in instances) for cache_key in tasks
    )
    assert multiplicities == [2, 2]

    judgments = {}
    for cache_key, task in tasks.items():
        judgments[cache_key] = {
            "parsed_label": "SAME_TYPE" if task.question_a == task.question_b else "DIFFERENT"
        }
    aggregates = aggregate_semantic_penalties([0, 1, 2], instances, judgments)
    assert aggregates[0]["same_count"] == aggregates[0]["compared_count"] == 1
    assert aggregates[1]["same_count"] == aggregates[1]["compared_count"] == 1
    assert aggregates[2]["same_count"] == 0
    assert aggregates[2]["compared_count"] == 2
    assert aggregates[0]["semantic_penalty"] == 1.0
    assert aggregates[2]["semantic_penalty"] == 0.0


def test_retry_once_and_final_failure_is_excluded_from_both_counts():
    tasks = [
        {"cache_key": "first_pass", "prompt": "p0"},
        {"cache_key": "eventual", "prompt": "p1"},
        {"cache_key": "failed", "prompt": "p2"},
    ]
    calls = []

    def generate(prompts):
        calls.append(prompts)
        return (
            [r"\boxed{DIFFERENT}", "bad", "bad"]
            if len(calls) == 1
            else [r"\boxed{SAME_TYPE}", "bad again"]
        )

    def parse(response):
        label = (
            "SAME_TYPE" if "SAME_TYPE" in response
            else "DIFFERENT" if "DIFFERENT" in response
            else None
        )
        return {"parsed_label": label}

    judgments = generate_with_one_retry(tasks, generate, parse)
    assert calls == [["p0", "p1", "p2"], ["p1", "p2"]]
    assert judgments["first_pass"] == {"parsed_label": "DIFFERENT", "attempts": 1}
    assert judgments["eventual"] == {"parsed_label": "SAME_TYPE", "attempts": 2}
    assert judgments["failed"] == {"parsed_label": None, "attempts": 2}

    questions = {0: "candidate", 1: "ref one", 2: "ref two"}
    instances, pair_tasks = build_pair_plan(
        questions, [0], [1, 2], cache_context("/frozen/snapshot")
    )
    pair_keys = [item.cache_key for item in instances]
    aggregates = aggregate_semantic_penalties(
        [0], instances,
        {
            pair_keys[0]: {"parsed_label": "SAME_TYPE", "attempts": 2},
            pair_keys[1]: {"parsed_label": None, "attempts": 2},
        },
    )
    assert aggregates[0] == {
        "same_count": 1,
        "compared_count": 1,
        "parse_failure_count": 1,
        "semantic_penalty": 1.0,
    }
    assert len(pair_tasks) == 2


def test_zero_successful_denominator_returns_zero_and_warns():
    questions = {0: "candidate", 1: "reference"}
    instances, _ = build_pair_plan(
        questions, [0], [1], cache_context("/frozen/snapshot")
    )
    messages = []
    aggregates = aggregate_semantic_penalties(
        [0], instances, {instances[0].cache_key: {"parsed_label": None}}, warn=messages.append
    )
    assert aggregates[0]["same_count"] == 0
    assert aggregates[0]["compared_count"] == 0
    assert aggregates[0]["parse_failure_count"] == 1
    assert aggregates[0]["semantic_penalty"] == 0.0
    assert len(messages) == 1
    assert "WARNING" in messages[0] and "penalty=0" in messages[0]
