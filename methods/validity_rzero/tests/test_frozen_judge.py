import json
from unittest.mock import patch
import pytest
from methods.validity_rzero.frozen_judge import judge_sampling, online_protocol, file_hash, verify_frozen
from methods.validity_rzero.semantic_judge_offline.run_pair_judge_v3_vllm import sampling_options


def protocol_file(root):
    protocol = {"version": "octo-judge-sft-v2-clear-eos-v1", "max_tokens": 256,
                "system_prompt": "rules", "chat_template": "saved-template"}
    (root / "judge_protocol.json").write_text(json.dumps(protocol))
    return protocol


def test_legacy_unchanged(tmp_path):
    assert judge_sampling(tmp_path, 1024, 42) == sampling_options(1024, 42)
    build = lambda a, b: a+b
    assert online_protocol(tmp_path, build, "legacy", "template") == (build, "legacy", "template", 1024)


def test_frozen_prompt_sampling_and_integrity(tmp_path):
    protocol_file(tmp_path)
    (tmp_path / "model.safetensors").write_bytes(b"test weights")
    hashes = {x.name: file_hash(x) for x in tmp_path.iterdir()}
    (tmp_path / "SHA256SUMS.json").write_text(json.dumps(hashes))
    assert verify_frozen(tmp_path) == file_hash(tmp_path / "SHA256SUMS.json")
    options = judge_sampling(tmp_path, 256, 42)
    assert options["temperature"] == options["presence_penalty"] == 0
    assert options["stop"] == [] and options["ignore_eos"] is False
    with pytest.raises(ValueError):
        judge_sampling(tmp_path, 1024, 42)
    class Tokenizer:
        chat_template = "saved-template"
        def apply_chat_template(self, messages, tokenize, add_generation_prompt):
            assert not tokenize and add_generation_prompt
            assert messages == [{"role": "system", "content": "rules"},
                                {"role": "user", "content": "Question A:\nA\n\nQuestion B:\nB"}]
            return "rendered"
    with patch("transformers.AutoTokenizer.from_pretrained", return_value=Tokenizer()):
        build, version, identity, budget = online_protocol(tmp_path, None, None, None)
        assert build("A", "B") == "rendered"
        assert budget == 256 and "rules" in identity
    (tmp_path / "model.safetensors").write_bytes(b"changed")
    with pytest.raises(ValueError, match="checksum mismatch"):
        verify_frozen(tmp_path)
