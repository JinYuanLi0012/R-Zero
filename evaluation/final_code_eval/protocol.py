"""Official completion text; only native BOS/EOS differ between families."""


class TokenInputModel:
    def __init__(self, model, tasks):
        self.model = model
        self.inputs = {t["rendered_prompt"]: t["prompt_token_ids"] for t in tasks}

    def generate(self, prompts, **kwargs):
        return self.model.generate([{"prompt_token_ids": self.inputs[p]} for p in prompts], **kwargs)


def configure(tokenizer, family):
    expected_eos = "<|endoftext|>" if family == "qwen" else "<|end_of_text|>"
    if tokenizer.eos_token != expected_eos or tokenizer.eos_token_id is None:
        raise ValueError(f"{family}: unexpected native EOS; inspect checkpoint tokenizer")
    if family == "qwen" and tokenizer.bos_token_id is not None:
        raise ValueError("Qwen3 Base expects no BOS")
    if family == "octo" and (tokenizer.bos_token != "<|begin_of_text|>" or tokenizer.bos_token_id is None):
        raise ValueError("Octo requires native Llama BOS")
    # Never inspect/apply a training chat template. Preserve native tokenization.


def render(task, tokenizer, family, max_new_tokens, max_model_len):
    prompt = task["prompt"]
    ids = tokenizer.encode(prompt, add_special_tokens=True)
    if family == "octo" and (not ids or ids[0] != tokenizer.bos_token_id or ids.count(tokenizer.bos_token_id) != 1):
        raise ValueError(f"{task['task_id']}: expected exactly one native leading BOS")
    if len(ids) + max_new_tokens > max_model_len:
        raise ValueError(f"{task['task_id']}: prompt plus output exceeds context")
    return {"rendered_prompt": prompt, "prompt_tokens": len(ids), "prompt_token_ids": ids}
