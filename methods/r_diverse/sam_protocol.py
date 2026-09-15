"""SAM generation framing and strict extraction; no mathematical validity gate."""
from pathlib import Path


CODE_PROTOCOL = 'sam-code-prefill-v2'


def code_prompt(question, tokenizer, mode='completion'):
    text = Path(__file__).with_name('code_prompt.txt').read_text().replace('{question}', question).rstrip()
    if mode == 'completion':
        # Continue the answer, matching the paper's few-shot Input -> Output -> CODE.
        return text + '\nOutput:\n<CODE>\n'
    if mode == 'chat':
        if not tokenizer.chat_template:
            raise ValueError('SAM chat mode requires a tokenizer with a chat template')
        return tokenizer.apply_chat_template([{'role': 'user', 'content': text}],
                                             tokenize=False, add_generation_prompt=True)
    raise ValueError(f'Unknown coder prompt mode: {mode}')


def extract_code(raw, mode='completion'):
    """Accept one target block; its opening tag is prefilled for Base completion.

    Never search through prose, select a nested/last block, or embed raw output.
    An echoed prompt contains example blocks that are not the target answer.
    """
    text = raw.strip()
    if text.startswith('<CODE>'):
        text = text[len('<CODE>'):].lstrip()
    elif mode != 'completion':
        raise ValueError('SAM response must start with <CODE>')
    if not text.endswith('</CODE>'):
        raise ValueError('SAM response is missing its final </CODE> (possibly truncated)')
    code = text[:-len('</CODE>')].strip()
    if '<CODE>' in code or '</CODE>' in code:
        raise ValueError('SAM response contains nested CODE tags / echoed instructions or examples')
    if not code:
        raise ValueError('SAM response has an empty code block')
    return code
