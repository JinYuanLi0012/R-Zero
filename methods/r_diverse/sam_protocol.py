"""SAM generation framing and strict extraction; no mathematical validity gate."""
import ast
from pathlib import Path


CODE_PROTOCOL = 'sam-code-tolerant-v3'


def code_prompt(question, tokenizer, mode='completion', retry=False):
    text = Path(__file__).with_name('code_prompt.txt').read_text().replace('{question}', question).rstrip()
    if mode == 'completion':
        # Continue the answer, matching the paper's few-shot Input -> Output -> CODE.
        return text + '\nOutput:\n<CODE>\n' + ('def solver(' if retry else '')
    if mode == 'chat':
        if not tokenizer.chat_template:
            raise ValueError('SAM chat mode requires a tokenizer with a chat template')
        if retry:
            text += '\nReturn only a complete Python solver function in <CODE>...</CODE>. Do not repeat the instructions or examples.'
        return tokenizer.apply_chat_template([{'role': 'user', 'content': text}],
                                             tokenize=False, add_generation_prompt=True)
    raise ValueError(f'Unknown coder prompt mode: {mode}')


def extract_code(raw, mode='completion', truncated=False):
    """Accept one target block; its opening tag is prefilled for Base completion.

    Never search through prose, select a nested/last block, or embed raw output.
    An echoed prompt contains example blocks that are not the target answer.
    """
    if truncated:
        raise ValueError('SAM generation reached its length limit')
    text = raw.strip()
    has_open = text.startswith('<CODE>')
    if has_open:
        text = text[len('<CODE>'):].lstrip()
    has_close = text.endswith('</CODE>')
    code = text[:-len('</CODE>')].strip() if has_close else text
    if '<CODE>' in code or '</CODE>' in code:
        raise ValueError('SAM response contains nested CODE tags / echoed instructions or examples')
    if not code:
        raise ValueError('SAM response has an empty code block')
    if not has_close or (mode == 'chat' and not has_open):
        # Only recover missing wrappers for a complete standalone solver module.
        # Parse, never execute; this is not a mathematical correctness check.
        try:
            tree = ast.parse(code)
        except (SyntaxError, ValueError) as error:
            raise ValueError('Unframed SAM response is not complete Python code') from error
        functions = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
        if (len(functions) != 1 or functions[0].name != 'solver'
                or not all(isinstance(n, (ast.Import, ast.ImportFrom, ast.FunctionDef)) for n in tree.body)
                or not any(isinstance(n, ast.Return) for n in ast.walk(functions[0]))):
            raise ValueError('Unframed SAM response must contain imports and one solver function returning a value')
    return code
