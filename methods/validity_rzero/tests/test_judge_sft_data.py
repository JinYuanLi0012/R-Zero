import pytest
from methods.validity_rzero.judge_sft_data import encode_example, metrics


def test_pair_inference_does_not_include_gold_or_demonstrations():
    from methods.validity_rzero.eval_judge_sft_pairs import pair_messages
    pair = {"a": {"question": "A text"}, "b": {"question": "B text"}, "expected_label": "SAME_TYPE"}
    messages = pair_messages(pair, "rules")
    assert messages == [{"role": "system", "content": "rules"},
                        {"role": "user", "content": "Question A:\nA text\n\nQuestion B:\nB text"}]


class Tokenizer:
    bos_token_id = 1
    eos_token_id = 2

    def apply_chat_template(self, messages, tokenize, add_generation_prompt):
        assert not tokenize and add_generation_prompt
        assert [m["role"] for m in messages] == ["system", "user"]
        return "BOS" + messages[0]["content"] + messages[1]["content"] + "assistant:\n"

    def encode(self, text, add_special_tokens):
        assert not add_special_tokens
        return ([1] + [ord(c)+10 for c in text[3:]]) if text.startswith("BOS") else [ord(c)+10 for c in text]


def test_only_assistant_and_eos_supervised():
    row = {"messages": [{"role": "system", "content": "rules"}, {"role": "user", "content": "questions"},
                        {"role": "assistant", "content": r"Same structure. \boxed{SAME_TYPE}"}]}
    example = encode_example(Tokenizer(), row, 2048)
    n = len(example["prompt_ids"])
    assert example["labels"][:n] == [-100]*n
    assert example["labels"][n:] == example["input_ids"][n:]
    assert example["input_ids"][-1] == 2
    assert example["expected_label"] == "SAME_TYPE"
    with pytest.raises(ValueError, match="refusing truncation"):
        encode_example(Tokenizer(), row, 10)


def test_parse_failure_counts_as_incorrect():
    rows = [{"expected_label": "SAME_TYPE", "prediction": None, "length_stop": True},
            {"expected_label": "DIFFERENT", "prediction": "SAME_TYPE", "length_stop": False},
            {"expected_label": "SAME_TYPE", "prediction": "SAME_TYPE", "length_stop": False}]
    result = metrics(rows)
    assert result["accuracy"] == 1/3
    assert result["balanced_accuracy"] == .25
    assert result["false_same_rate"] == 1
    assert result["length_stops"] == 1
