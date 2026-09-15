import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

from jinja2 import Template
import pytest

from methods.validity_rl import evaluate_terra_validation as evaluate
from methods.validity_rl import prepare_octothinker_eval as merge

METHOD = Path(__file__).resolve().parents[1]


def checkpoint(root, step):
    actor = root / f"global_step_{step}" / "actor"
    hf = actor / "huggingface"
    hf.mkdir(parents=True)
    for name in ("config.json", "tokenizer_config.json", "tokenizer.json"):
        (hf / name).write_text("{}")
    for rank in range(2):
        (actor / f"model_world_size_2_rank_{rank}.pt").write_bytes(b"fake test shard")
    return actor


def test_merge_is_separate_reusable_and_rejects_changed_source(tmp_path, monkeypatch):
    root, out = tmp_path / "run", tmp_path / "merged"
    actor = checkpoint(root, 10)
    calls = []

    def fake_merge(command, **kwargs):
        calls.append(command)
        assert kwargs["env"]["CUDA_VISIBLE_DEVICES"] == ""
        stage = Path(command[-1])
        assert (stage / "model_world_size_2_rank_0.pt").is_symlink()
        (stage / "huggingface/model.safetensors").write_bytes(b"test weights")

    monkeypatch.setattr(merge.subprocess, "run", fake_merge)
    merge.prepare(root, out, [10])
    merge.prepare(root, out, [10])
    assert len(calls) == 1
    assert not (actor / "huggingface/model.safetensors").exists()
    assert (actor / "model_world_size_2_rank_0.pt").read_bytes() == b"fake test shard"
    (actor / "model_world_size_2_rank_1.pt").write_bytes(b"changed")
    with pytest.raises(ValueError, match="source changed"):
        merge.prepare(root, out, [10])


def test_preflight_and_missing_index_shard(tmp_path):
    checkpoint(tmp_path / "run", 5)
    with pytest.raises(ValueError, match="Missing or empty"):
        merge.prepare(tmp_path / "run", tmp_path / "merged", [5, 15])
    assert not (tmp_path / "merged").exists()
    hf = tmp_path / "run/global_step_5/actor/huggingface"
    (hf / "model.safetensors.index.json").write_text(json.dumps({"weight_map": {"x": "missing.safetensors"}}))
    with pytest.raises(ValueError, match="missing.safetensors"):
        merge.validate_weights(hf)


def test_generation_uses_training_template_and_no_extra_bos(monkeypatch):
    class Tokenizer:
        chat_template = None
        eos_token_id = 128001

        def apply_chat_template(self, messages, **kwargs):
            return Template(self.chat_template).render(messages=messages,
                bos_token="<|begin_of_text|>", add_generation_prompt=True)

        def encode(self, text, add_special_tokens):
            assert add_special_tokens is False
            assert text.count("<|begin_of_text|>") == 1
            assert text.startswith("<|begin_of_text|>user: What is 2+2?")
            assert text.endswith("assistant:\n")
            return [128000, 42]

    class Model:
        def __init__(self, **kwargs):
            assert kwargs["tensor_parallel_size"] == 2

        def generate(self, inputs, **kwargs):
            assert inputs == [{"prompt_token_ids": [128000, 42]}]
            return [SimpleNamespace(outputs=[SimpleNamespace(text=r"\boxed{4}")])]

    monkeypatch.setattr(evaluate.AutoTokenizer, "from_pretrained", lambda _: Tokenizer())
    monkeypatch.setitem(sys.modules, "vllm", SimpleNamespace(LLM=Model, SamplingParams=lambda **kw: kw))
    args = SimpleNamespace(model="test", chat_template=METHOD / "octothinker_chat.jinja",
        prompt_template=METHOD / "validity_solver.jinja", tensor_parallel_size=2, gpu_memory_utilization=.85)
    assert evaluate.generate_responses(args, [{"question": "What is 2+2?"}]) == [r"\boxed{4}"]
    assert evaluate.DEFAULT_DATASET == "jinyuan222/rzero-validity-rl-terra-v1"
    assert evaluate.EXPECTED_VALIDATION_SIZE == 297


def test_two_gpu_shell_keeps_api_and_octothinker_base(tmp_path):
    env = {k: v for k, v in os.environ.items() if not k.startswith("VALIDITY_")}
    env.update(STORAGE_PATH=str(tmp_path), VALIDITY_TERRA_MODELS="base",
        VALIDITY_TERRA_GPU_IDS="0,3", VALIDITY_TERRA_DRY_RUN="1", OPENAI_API_KEY="test-not-used")
    result = subprocess.run(["bash", str(METHOD / "evaluate_octothinker_terra.sh")],
        env=env, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    assert "OctoThinker/OctoThinker-3B-Hybrid-Base" in result.stdout
    assert "--tensor-parallel-size 2" in result.stdout
    assert "--chat-template" in result.stdout
    assert "--skip-api-recheck" not in result.stdout
    env["VALIDITY_TERRA_GPU_IDS"] = "0,0"
    assert subprocess.run(["bash", str(METHOD / "evaluate_octothinker_terra.sh")], env=env,
        capture_output=True).returncode == 2
