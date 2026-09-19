"""Use the training role template and exactly one BOS for both Base and Solver."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "methods/validity_rl/octothinker_chat.jinja"


def configure(tokenizer, template, base_model=False):
    if tokenizer.bos_token != "<|begin_of_text|>" or tokenizer.bos_token_id is None:
        raise ValueError("Expected an Octo Hybrid/Llama tokenizer with a BOS token")
    if tokenizer.eos_token_id is None:
        raise ValueError("Octo tokenizer is missing EOS")
    if tokenizer.chat_template:
        if tokenizer.chat_template != template:
            raise ValueError("Saved checkpoint template differs from the Octo training template; "
                             "refusing to compare different protocols")
    elif not base_model:
        raise ValueError("Solver checkpoint is missing its saved chat template. Use the complete "
                         "merged checkpoint; --base-model is only for the original Base baseline")
    # This is the same assignment as the training entry, never persisted to the model.
    tokenizer.chat_template = template
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    return tokenizer


def render(task, tokenizer, max_new_tokens, max_model_len):
    prompt = tokenizer.apply_chat_template(task["messages"], tokenize=False,
                                           add_generation_prompt=True)
    ids = tokenizer.encode(prompt, add_special_tokens=False)
    if not ids or ids[0] != tokenizer.bos_token_id or ids.count(tokenizer.bos_token_id) != 1:
        raise ValueError(f"{task['task_id']}: expected exactly one leading BOS")
    if len(ids) + max_new_tokens > max_model_len:
        raise ValueError(f"{task['task_id']}: {len(ids)} prompt tokens + {max_new_tokens} output "
                         "tokens do not fit; increase --max-model-len")
    return {**task, "rendered_prompt": prompt, "prompt_tokens": len(ids),
            "prompt_token_ids": ids}


class TokenInputModel:
    """Adapt the shared resume loop to vLLM's explicit-token input interface."""
    def __init__(self, model, tasks):
        self.model = model
        self.inputs = {t["rendered_prompt"]: t["prompt_token_ids"] for t in tasks}

    def generate(self, prompts, **kwargs):
        return self.model.generate([{"prompt_token_ids": self.inputs[p]} for p in prompts], **kwargs)
