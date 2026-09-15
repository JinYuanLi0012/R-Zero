import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest
from tokenizers import Tokenizer
from tokenizers.models import WordLevel
from tokenizers.processors import TemplateProcessing
from transformers import PreTrainedTokenizerFast, AutoTokenizer

from methods.validity_rzero.octothinker import configure_tokenizer, generation_inputs

ROOT = Path(__file__).resolve().parents[3]


def tokenizer():
    engine = Tokenizer(WordLevel({"[UNK]": 0, "<|begin_of_text|>": 1, "<|end_of_text|>": 2}, unk_token="[UNK]"))
    engine.post_processor = TemplateProcessing(single="<|begin_of_text|> $A", special_tokens=[("<|begin_of_text|>", 1)])
    return PreTrainedTokenizerFast(tokenizer_object=engine, unk_token="[UNK]",
        bos_token="<|begin_of_text|>", eos_token="<|end_of_text|>")


def test_template_tokens_and_checkpoint_inheritance(tmp_path, monkeypatch):
    monkeypatch.setenv("VALIDITY_RZERO_MODEL_FAMILY", "octothinker")
    tok = configure_tokenizer(tokenizer())
    for messages in ([{"role": "user", "content": "validity task"}],
                     [{"role": "system", "content": "math task"}, {"role": "user", "content": "problem"}]):
        text = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        assert text.endswith("assistant:\n")
        ids = generation_inputs([text], tok)[0]["prompt_token_ids"]
        assert ids.count(tok.bos_token_id) == 1
        assert ids == tok.apply_chat_template(messages, tokenize=True, add_generation_prompt=True)
    tok.save_pretrained(tmp_path)
    monkeypatch.delenv("VALIDITY_RZERO_MODEL_FAMILY")
    reloaded = AutoTokenizer.from_pretrained(tmp_path)
    assert reloaded.chat_template == tok.chat_template
    assert reloaded.pad_token_id == reloaded.eos_token_id


def test_legacy_is_unchanged(monkeypatch):
    monkeypatch.delenv("VALIDITY_RZERO_MODEL_FAMILY", raising=False)
    tok = tokenizer()
    assert configure_tokenizer(tok).chat_template is None
    prompts = ["plain completion"]
    assert generation_inputs(prompts, tok) is prompts


@pytest.mark.parametrize("resume", [False, True])
def test_real_wrapper_environment(tmp_path, resume):
    method = tmp_path / "methods/validity_rzero"
    method.mkdir(parents=True)
    shutil.copyfile(ROOT / "methods/validity_rzero/run_octothinker.sh", method / "run_octothinker.sh")
    # Replace only expensive process boundaries; run real shell expansion and exports.
    (method / "run.sh").write_text('printf "MODE:%s\\n" "$*"\nenv\n')
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake = bin_dir / "python3"
    fake.write_text(f'#!{sys.executable}\nimport sys\nif sys.argv[1] == "-": print("/cache/OctoThinker-Hybrid-Base")\n')
    fake.chmod(0o755)
    env = dict(PATH=str(bin_dir) + os.pathsep + os.defpath, STORAGE_PATH=str(tmp_path / "storage"),
        HUGGINGFACENAME="test-user", BASE_MODEL="Qwen/stale", VALIDITY_RZERO_SEMANTIC_MODEL="Qwen/stale",
        SOLVER_NEGATIVE_ONLY="1", SOLVER_DYNAMIC_VOTE="1", SOLVER_TOKEN_MASKING="1", RZERO_FIRST_ROUND="6",
        QUESTION_GPU_IDS="0,3", SOLVER_TRAIN_FILES="stale/train", WANDB_MODE="disabled")
    command = ["bash", str(method / "run_octothinker.sh")]
    if resume:
        command.append("--resume")
    result = subprocess.run(command, env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    values = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
    for key in ("BASE_MODEL", "VALIDITY_RZERO_SEMANTIC_MODEL"):
        assert values[key] == "/cache/OctoThinker-Hybrid-Base"
    assert values["VALIDITY_RZERO_INITIAL_SOLVER"].endswith("evaluation_models/global_step_10/actor/huggingface")
    assert values["QUESTION_GPU_IDS"] == values["VALIDITY_RZERO_SEMANTIC_GPU_IDS"] == "0,1,2,3"
    assert values["QUESTIONER_TRAIN_GPU_IDS"] == "0,1"
    assert values["VLLM_GPU_IDS"] == "2,3"
    assert values["VALIDITY_RZERO_NOVELTY_K"] == "8"
    assert values["VALIDITY_RZERO_NOVELTY_MIN_SAME_HITS"] == "1"
    assert values["TERRA_REPLAY_RATIO"] == "0.1"
    assert values["RZERO_FIRST_ROUND"] == "1"
    assert values["SOLVER_DYNAMIC_VOTE"] == values["SOLVER_NEGATIVE_ONLY"] == values["SOLVER_TOKEN_MASKING"] == "0"
    assert values["QUESTIONER_MAX_STEPS"] == "5" and values["SOLVER_MAX_STEPS"] == "15"
    assert values["QUESTIONER_LOGGER"] == values["SOLVER_LOGGER"] == '["console","wandb"]'
    assert values["WANDB_MODE"] == "online"
    assert "SOLVER_TRAIN_FILES" not in values
    assert f'MODE:{"--resume" if resume else ""}\n' in result.stdout
