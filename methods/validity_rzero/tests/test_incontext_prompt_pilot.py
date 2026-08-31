from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from methods.validity_rzero.incontext_pilot.run_prompt_pilot import (
    BASELINE_USER_PROMPT,
    SYSTEM_PROMPT,
    build_requests,
    build_review_sample,
    condition_metrics,
    contrastive_user_prompt,
    eligible_archive_rows,
    extract_last_boxed,
    normalized_template,
    parse_completion,
    sample_reference_groups,
)


class FakeTokenizer:
    chat_template = "fake"

    def encode(self, text, add_special_tokens=False):
        del add_special_tokens
        return text.split()

    def apply_chat_template(
        self, chat, tokenize=False, add_generation_prompt=True, add_special_tokens=True
    ):
        assert tokenize is False
        assert add_generation_prompt is True
        assert add_special_tokens is True
        return "\n".join(f"{item['role']}: {item['content']}" for item in chat) + "\nassistant:"


def archive_rows():
    return [
        {
            "_row_index": 0, "question": "valid passed one",
            "validity_decision": "VALID", "passed_rzero_filter": True,
        },
        {
            "_row_index": 1, "question": "valid passed one",
            "validity_decision": "VALID", "passed_rzero_filter": True,
        },
        {"_row_index": 2, "question": "valid but failed", "validity_decision": "VALID", "passed_rzero_filter": False},
        {"_row_index": 3, "question": "invalid", "validity_decision": "INVALID", "passed_rzero_filter": True},
        {"_row_index": 4, "question": "valid passed two", "validity_decision": "VALID", "passed_rzero_filter": True},
        {"_row_index": 5, "question": "valid passed three", "validity_decision": "VALID", "passed_rzero_filter": True},
        {"_row_index": 6, "question": "one two three four five six", "validity_decision": "VALID", "passed_rzero_filter": True},
    ]


def test_archive_filter_is_valid_passed_and_keeps_duplicate_rows():
    eligible, counts = eligible_archive_rows(archive_rows(), FakeTokenizer(), 4)
    assert [item["row_index"] for item in eligible] == [0, 1, 4, 5]
    assert [item["question"] for item in eligible].count("valid passed one") == 2
    assert counts == {
        "eligible": 4,
        "not_phase_b_passed": 1,
        "not_valid": 1,
        "over_reference_token_limit": 1,
        "total": 7,
    }


def test_reference_groups_are_seeded_and_have_distinct_row_indices():
    eligible, _ = eligible_archive_rows(archive_rows(), FakeTokenizer(), 4)
    first = sample_reference_groups(eligible, 5, 3, seed=43)
    second = sample_reference_groups(eligible, 5, 3, seed=43)
    assert first == second
    assert all(len({item["row_index"] for item in group}) == 3 for group in first)


def test_group_build_pairs_prompts_and_request_seeds():
    eligible, _ = eligible_archive_rows(archive_rows(), FakeTokenizer(), 4)
    reference_groups = sample_reference_groups(eligible, 2, 3, seed=43)
    groups, requests = build_requests(FakeTokenizer(), reference_groups, 1000, sampling_seed=42)
    assert len(groups) == 2
    assert [item["condition"] for item in requests] == [
        "P0_fixed_prompt", "P1_history_context",
        "P0_fixed_prompt", "P1_history_context",
    ]
    assert [item["request_seed"] for item in requests] == [42, 42, 43, 43]
    assert requests[0]["prompt"] == requests[2]["prompt"]
    assert requests[1]["prompt"] != requests[3]["prompt"]


def test_prompt_marks_references_as_negative_and_keeps_original_contract():
    references = [{"question": f"question {index}"} for index in range(3)]
    treatment = contrastive_user_prompt(references)
    assert "negative references, not examples to imitate" in " ".join(treatment.split())
    assert "core solution method" in treatment
    assert all(f"[Negative reference {index}]" in treatment for index in range(1, 4))
    assert "<question>" in SYSTEM_PROMPT
    assert "\\boxed{final_answer}" in SYSTEM_PROMPT
    assert BASELINE_USER_PROMPT.startswith("Generate one new")


def test_nested_box_and_completion_parse():
    text = "<question>Find x.</question>\\n\\boxed{\\frac{1}{2}}"
    assert extract_last_boxed(text) == r"\frac{1}{2}"
    question, answer, ok = parse_completion(text)
    assert (question, answer, ok) == ("Find x.", r"\frac{1}{2}", True)
    assert parse_completion("no format") == ("", "", False)


def test_normalized_metrics_report_archive_and_family_concentration():
    archive = [
        {"question": "Find the smallest n such that n^2 exceeds 10."},
        {"question": "A distinct archive question."},
    ]
    rows = [
        {
            "condition": "P0_fixed_prompt", "format_ok": True,
            "question": "Find the smallest n such that n^2 exceeds 20.",
            "max_reference_4gram_jaccard": 0.0,
        },
        {
            "condition": "P0_fixed_prompt", "format_ok": True,
            "question": "Find the smallest n such that n^2 exceeds 30.",
            "max_reference_4gram_jaccard": 0.0,
        },
        {
            "condition": "P0_fixed_prompt", "format_ok": False,
            "question": "", "max_reference_4gram_jaccard": 0.0,
        },
    ]
    metrics = condition_metrics(rows, archive)
    assert normalized_template(rows[0]["question"]) == normalized_template(rows[1]["question"])
    assert metrics["completion_count"] == 3
    assert metrics["format_success_rate"] == 2 / 3
    assert metrics["exact_unique_rate"] == 1.0
    assert metrics["normalized_template_unique_rate"] == 0.5
    assert metrics["top_1_template_share"] == 1.0
    assert metrics["normalized_archive_overlap_rate"] == 1.0
    assert metrics["reference_4gram_jaccard"]["mean"] == 0.0


def test_review_sample_keeps_paired_group_rollouts():
    groups = [
        {"group_index": index, "references": [{"row_index": index, "question": "ref"}]}
        for index in range(3)
    ]
    generations = []
    for group_index in range(3):
        for condition in ("P0_fixed_prompt", "P1_history_context"):
            for completion_index in range(4):
                generations.append({
                    "group_index": group_index,
                    "condition": condition,
                    "completion_index": completion_index,
                    "format_ok": True,
                    "question": f"{condition}-{group_index}-{completion_index}",
                    "answer": "answer",
                })
    first = build_review_sample(groups, generations, count=2, seed=44)
    second = build_review_sample(groups, generations, count=2, seed=44)
    assert first == second
    assert len(first) == 2
    assert all(len(row["P0_fixed_prompt"]) == 4 for row in first)
    assert all(len(row["P1_history_context"]) == 4 for row in first)
