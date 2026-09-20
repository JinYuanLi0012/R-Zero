"""Same messages and decoding protocol; only training template/token IDs vary."""
from pathlib import Path
from evaluation.octo_code_eval.protocol import TokenInputModel

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ('Please reason step by step and solve the programming problem. '
          'Put your final, complete Python solution in a markdown code block.')


def template_for(family):
    path = (Path(__file__).with_name('qwen_training.jinja') if family == 'qwen'
            else ROOT / 'methods/validity_rl/octothinker_chat.jinja')
    return path.read_text()


def configure(tokenizer, template, family):
    expected_eos = '<|endoftext|>' if family == 'qwen' else '<|end_of_text|>'
    if tokenizer.eos_token != expected_eos or tokenizer.eos_token_id is None:
        raise ValueError(f'{family}: EOS differs from the training Base tokenizer')
    if family == 'octo' and tokenizer.bos_token != '<|begin_of_text|>':
        raise ValueError('Octo requires its training BOS')
    if family == 'qwen' and tokenizer.bos_token_id is not None:
        raise ValueError('Qwen3 Base training tokenizer has no BOS')
    if tokenizer.chat_template and tokenizer.chat_template != template:
        raise ValueError('Checkpoint template differs from the pinned training template; '
                         'inspect checkpoint provenance before comparing results')
    # Identical for Base and Solver, including absent-template handling.
    tokenizer.chat_template = template
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    return tokenizer


def messages_for(task):
    if 'task_prompt' in task:
        content = task['task_prompt']
    else:
        # Preserve official LCB task details/starter code, discard its separate system message.
        content = '\n\n'.join(m['content'] for m in task['messages'] if m['role'] == 'user')
    return [{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': content}]


def render(task, tokenizer, max_new_tokens, max_model_len, family):
    messages = messages_for(task)
    # Matches RLHFDataset: no enable_thinking override, no implicit extra BOS.
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    ids = tokenizer.encode(prompt, add_special_tokens=False)
    if family == 'octo' and (not ids or ids[0] != tokenizer.bos_token_id
                            or ids.count(tokenizer.bos_token_id) != 1):
        raise ValueError(f"{task['task_id']}: expected exactly one leading Octo BOS")
    if len(ids) + max_new_tokens > max_model_len:
        raise ValueError(f"{task['task_id']}: prompt plus output exceeds context; increase --max-model-len")
    return {**task, 'messages': messages, 'stop': [], 'rendered_prompt': prompt,
            'prompt_tokens': len(ids), 'prompt_token_ids': ids}
