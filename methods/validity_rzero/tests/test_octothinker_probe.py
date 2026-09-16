import pytest
from methods.validity_rzero.probe_octothinker_judge import select_pairs, options, summarize
from methods.validity_rzero.semantic_judge_offline.run_pair_judge_v3_vllm import sampling_options, parse_response_v3
from methods.validity_rzero.probe_octothinker_judge import condition_prompt
from methods.validity_rzero.octothinker_judge_fewshot import controls, EXAMPLES
from methods.validity_rzero.octothinker_judge_three_shot import expanded_controls, EXAMPLES as THREE_EXAMPLES
from methods.validity_rzero.octothinker_judge_balanced import sanity_checks, EXAMPLES as BALANCED_EXAMPLES


def test_invariant_revision_preserves_b_examples_sampling_and_suffix():
    pair = controls()[0]
    old = condition_prompt(pair, "fewshot-greedy")
    new = condition_prompt(pair, "invariant-greedy")
    assert old[old.index("Example 1"):] == new[new.index("Example 1"):]
    assert "replaceable slots" in new
    assert "Do not invent" in new
    assert options("invariant-greedy", 1024, 42) == options("fewshot-greedy", 1024, 42)


def test_greedy_changes_sampling_not_old_prompt():
    pair = controls()[0]
    assert condition_prompt(pair, "fewshot") == condition_prompt(pair, "fewshot-greedy")
    greedy = options("fewshot-greedy", 1024, 42)
    assert greedy == options("balanced-greedy", 1024, 42)
    assert greedy["temperature"] == greedy["presence_penalty"] == 0
    assert greedy["top_k"] == -1 and greedy["top_p"] == 1
    expected = options("fewshot", 1024, 42)
    expected.update(temperature=0.0, presence_penalty=0.0, top_p=1.0, top_k=-1, min_p=0.0)
    assert greedy == expected


def test_balanced_examples_and_sanity_separate_summary():
    assert sum(e[2] == "SAME_TYPE" for e in BALANCED_EXAMPLES) == 2
    examples = {q for e in BALANCED_EXAMPLES for q in e[:2]}
    checks = sanity_checks()
    assert len(checks) == 8
    assert all(p[k]["question"] not in examples for p in expanded_controls() + checks for k in ("a", "b"))
    rows = [{**p, "condition": "balanced-greedy", "parse": parse_response_v3(r"\boxed{SAME_TYPE}"),
             "finish_reason": "stop", "output_tokens": 10} for p in expanded_controls() + checks]
    metrics = summarize(rows)["balanced-greedy"]
    assert metrics["controls"]["n"] == 12
    assert metrics["sanity_checks"]["n"] == 8
    assert metrics["sanity_checks"]["SAME_TYPE"] == {"n": 6, "correct": 6}


def test_three_shot_balanced_controls_and_sampling():
    pairs = expanded_controls()
    assert len(pairs) == len({p["pair_id"] for p in pairs}) == 12
    assert sum(p["expected_label"] == "SAME_TYPE" for p in pairs) == 6
    examples = {q for e in EXAMPLES + THREE_EXAMPLES for q in e[:2]}
    assert all(p[k]["question"] not in examples for p in pairs for k in ("a", "b"))
    text = condition_prompt(pairs[0], "three-shot")
    assert text.count("Example ") == 3
    assert "2-4 concise sentences" in text
    assert text.endswith("Comparison:")
    assert options("three-shot", 1024, 42) == options("fewshot", 1024, 42)


def test_fewshot_and_controls_are_disjoint_and_sampling_unchanged():
    assert options("fewshot", 1024, 42) == options("current", 1024, 42)
    control = controls()
    assert [c["expected_label"] for c in control].count("SAME_TYPE") == 2
    examples = {q for e in EXAMPLES for q in e[:2]}
    assert all(c[k]["question"] not in examples for c in control for k in ("a", "b"))
    text = condition_prompt(control[0], "fewshot")
    assert text.endswith("Classification:")
    assert "NOT solving" in text
    assert text.count(r"\boxed{SAME_TYPE}") == text.count(r"\boxed{DIFFERENT}") == 3
    assert condition_prompt({"prompt": "original exact prompt"}, "current") == "original exact prompt"


def test_train_sampling_and_no_labels_in_prompt():
    rows = [{"id": i, "question": f"Compute {i}+1", "split": "train", "terra_validity": "INVALID"} for i in range(30)]
    pairs = select_pairs(rows, 20, 43)
    assert pairs == select_pairs(rows, 20, 43)
    assert len(pairs) == 10
    assert len({r[k]["id"] for r in pairs for k in ("a", "b")}) == 20
    assert "INVALID" not in pairs[0]["prompt"]
    assert pairs[0]["prompt"].endswith("Analysis:")
    with pytest.raises(ValueError):
        select_pairs(rows, 3, 43)
    with pytest.raises(ValueError):
        select_pairs([{**rows[0], "split": "validation"}], 2, 43)


def test_original_protocol_and_stop_only_change():
    baseline = options("current", 1024, 42)
    assert baseline == sampling_options(1024, 42)
    changed = options("no-box-stop", 1024, 42)
    assert changed.pop("stop") == []
    baseline.pop("stop")
    assert changed == baseline


def test_summary_does_not_call_parse_rate_accuracy():
    rows = [{"condition": "current", "parse": parse_response_v3(text), "finish_reason": finish,
             "output_tokens": tokens} for text, finish, tokens in [(r"\boxed{DIFFERENT}", "stop", 10), ("unfinished", "length", 1024)]]
    metrics = summarize(rows)["current"]
    assert metrics["parse_failure_rate"] == metrics["length_stop_rate"] == .5
    assert metrics["mean_output_tokens"] == 517
    assert "accuracy" not in metrics
