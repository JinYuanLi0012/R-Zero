import pytest
from methods.validity_rzero.probe_octothinker_judge import select_pairs, options, summarize
from methods.validity_rzero.semantic_judge_offline.run_pair_judge_v3_vllm import sampling_options, parse_response_v3
from methods.validity_rzero.probe_octothinker_judge import condition_prompt
from methods.validity_rzero.octothinker_judge_fewshot import controls, EXAMPLES


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
