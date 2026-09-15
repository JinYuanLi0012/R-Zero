"""Opt-in OctoThinker chat boundary; task prompts and reward rules stay unchanged."""
import os
from pathlib import Path


def enabled():
    return os.getenv("VALIDITY_RZERO_MODEL_FAMILY") == "octothinker"


def configure_tokenizer(tokenizer):
    if enabled():
        if tokenizer.bos_token != "<|begin_of_text|>":
            raise ValueError("OctoThinker entry received an incompatible tokenizer")
        tokenizer.chat_template = (Path(__file__).parents[1] / "validity_rl/octothinker_chat.jinja").read_text()
        if tokenizer.pad_token_id is None:
            tokenizer.pad_token = tokenizer.eos_token
    return tokenizer


def generation_inputs(prompts, tokenizer):
    if not enabled():
        return prompts
    # Already rendered chat contains BOS; do not let vLLM add it again.
    return [{"prompt_token_ids": tokenizer.encode(prompt, add_special_tokens=False)} for prompt in prompts]
