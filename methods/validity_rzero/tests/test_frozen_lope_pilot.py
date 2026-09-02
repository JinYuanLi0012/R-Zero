from pathlib import Path
import random
import sys


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from methods.validity_rzero.frozen_lope_pilot.run_frozen_lope_pilot import (
    BOUNDARY,
    SYSTEM_PROMPT,
    build_requests,
    condition_metrics,
    generate_lorem_perturbation,
    numeric_template_key,
    parse_completion,
    surface_key,
)
from methods.validity_rzero.frozen_lope_pilot.lorem_compat import WORD_POOL


class FakeTokenizer:
    chat_template = "fake"
    eos_token_id = 0

    def encode(self, text, add_special_tokens=False):
        del add_special_tokens
        return text.split()

    def decode(self, token_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False):
        del skip_special_tokens, clean_up_tokenization_spaces
        return " ".join(token_ids)

    def apply_chat_template(
        self, chat, tokenize=False, add_generation_prompt=True, add_special_tokens=True
    ):
        assert tokenize is False
        assert add_generation_prompt is True
        assert add_special_tokens is True
        return "\n".join(f"{item['role']}: {item['content']}" for item in chat) + "\nassistant:"


def fake_lorem(count):
    return " ".join(f"lorem{index}" for index in range(count))


def test_lorem_generation_is_seeded_exact_and_preserves_global_random_state():
    tokenizer = FakeTokenizer()
    random.seed(123)
    before = random.getstate()
    first = generate_lorem_perturbation(tokenizer, 50001, 100, 300, fake_lorem)
    after = random.getstate()
    second = generate_lorem_perturbation(tokenizer, 50001, 100, 300, fake_lorem)
    assert first == second
    assert 100 <= first[1] <= 300
    assert len(tokenizer.encode(first[0])) == first[1]
    assert before == after
    assert len(WORD_POOL) == 63


def test_requests_are_one_to_one_seed_paired_and_only_lope_has_perturbation():
    requests = build_requests(
        FakeTokenizer(),
        request_count=3,
        generation_seed_base=10000,
        perturbation_seed_base=50000,
        lorem_min_tokens=3,
        lorem_max_tokens=5,
        max_prompt_tokens=1000,
        word_generator=fake_lorem,
    )
    assert len(requests) == 6
    for index in range(0, len(requests), 2):
        fixed, lope = requests[index:index + 2]
        assert fixed["condition"] == "fixed"
        assert lope["condition"] == "lope"
        assert fixed["request_id"] == lope["request_id"]
        assert fixed["generation_seed"] == lope["generation_seed"]
        assert fixed["perturbation_text"] is None
        assert fixed["perturbation_seed"] is None
        assert lope["perturbation_text"]
        assert lope["perturbation_seed"] == 50000 + lope["request_id"]
        assert lope["prompt"].index(lope["perturbation_text"]) < lope["prompt"].index(BOUNDARY)
        assert lope["prompt"].index(BOUNDARY) < lope["prompt"].index(SYSTEM_PROMPT)


def test_parser_requires_question_and_boxed_answer():
    text = r"<question>Find x.</question>\boxed{\frac{1}{2}}"
    assert parse_completion(text) == ("Find x.", r"\frac{1}{2}", True)
    assert parse_completion("<question>Find x.</question>") == ("Find x.", "", False)


def test_requested_normalizations_and_family_member_metrics():
    first = "  Find   n such that n^2 = 10. "
    second = "find n such that n^2 = 20."
    third = "A unique question."
    assert surface_key(first) != surface_key(second)
    assert numeric_template_key(first) == numeric_template_key(second)
    rows = [
        {"parsed_question_success": True, "parsed_question": first},
        {"parsed_question_success": True, "parsed_question": second},
        {"parsed_question_success": True, "parsed_question": third},
        {"parsed_question_success": False, "parsed_question": ""},
    ]
    metrics = condition_metrics(rows)
    assert metrics["parsed_question_success_rate"] == 3 / 4
    assert metrics["surface_duplicate_share"] == 0.0
    assert metrics["numeric_normalized_repeated_template_share"] == 2 / 3
    assert metrics["top_5_normalized_template_mass"] == 1.0
