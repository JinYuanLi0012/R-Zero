"""Short-lived single-GPU inference: original Q/S sampling, SAM code or embedding."""
import argparse
import ast
import json
import re
from pathlib import Path

from methods.r_diverse.core import parse_question, read_json, write_json
from methods.r_diverse.prompts import QUESTIONER_MESSAGES, SOLVER_SYSTEM


def render(tokenizer, messages):
    if tokenizer.chat_template:
        return tokenizer.apply_chat_template(messages, tokenize=False,
                                             add_generation_prompt=True, add_special_tokens=True)
    return '\n'.join(m['role'] + ': ' + m['content'] for m in messages)


def majority(texts, phase):
    from mathruler.grader import extract_boxed_content, grade_answer
    import stopit

    @stopit.threading_timeoutable(default='TIMED_OUT')
    def grade(a, b):
        return grade_answer(a, b)

    results = [extract_boxed_content(text) for text in texts]
    denominator = len(results) if phase == 'reward' else sum(bool(x) for x in results)
    counts = {}
    for answer in results:
        if not answer:
            continue
        matched = False
        for previous in counts:
            same = answer == previous or ('no ' in answer.lower() and 'no ' in previous.lower())
            if not same:
                try:
                    forward = grade(answer, previous, timeout=10)
                    # Preserve upstream label-path timeout behavior.
                    if forward == 'TIMED_OUT' and phase == 'label':
                        continue
                    same = forward != 'TIMED_OUT' and bool(forward)
                    if not same:
                        backward = grade(previous, answer, timeout=10)
                        same = backward != 'TIMED_OUT' and bool(backward)
                except Exception:
                    same = False
            if same:
                counts[previous] += 1
                matched = True
                break
        if not matched:
            counts[answer] = 1
    answer = max(counts, key=counts.get) if counts else ''
    return {'answer': answer, 'score': counts.get(answer, 0) / denominator if denominator else 0.0,
            'results': results}


def generate(job):
    import vllm
    from transformers import AutoTokenizer
    cfg, mode, rows = job['config'], job['mode'], job['rows']
    tokenizer = AutoTokenizer.from_pretrained(job['model'])
    llm = vllm.LLM(
        model=job['model'], tokenizer=job['model'], tensor_parallel_size=1,
        distributed_executor_backend='mp', dtype='bfloat16',
        gpu_memory_utilization=cfg['inference_memory'],
        max_model_len=cfg['inference_context'], seed=job['seed'],
        enable_prefix_caching=True,
    )
    if mode == 'generate':
        prompts = [render(tokenizer, QUESTIONER_MESSAGES) for _ in rows]
        params = vllm.SamplingParams(n=1, max_tokens=cfg['response_tokens'],
                                     temperature=1.0, top_p=0.95)
    elif mode == 'solve':
        prompts = [render(tokenizer, [{'role': 'system', 'content': SOLVER_SYSTEM},
                                     {'role': 'user', 'content': row['question']}]) for row in rows]
        params = vllm.SamplingParams(n=10 if job['phase'] == 'reward' else 9,
                                     max_tokens=cfg['response_tokens'], temperature=1.0,
                                     top_p=1.0, top_k=40)
    else:
        template = Path(__file__).with_name('code_prompt.txt').read_text()
        # Base Coder receives the literal few-shot completion prompt. An explicitly
        # selected instruction model uses its own chat template, never a Qwen3 one.
        texts = [template.replace('{question}', row['question']) for row in rows]
        prompts = [render(tokenizer, [{'role': 'user', 'content': text}])
                   if tokenizer.chat_template else text for text in texts]
        params = vllm.SamplingParams(n=1, max_tokens=cfg['code_tokens'], temperature=0.0,
                                     top_p=1.0, stop=['</CODE>'], include_stop_str_in_output=True)
    output = []
    batch_size = cfg['inference_batch']
    for begin in range(0, len(rows), batch_size):
        completions = llm.generate(prompts[begin:begin + batch_size], params, use_tqdm=False)
        for row, completion in zip(rows[begin:begin + batch_size], completions):
            texts = [o.text for o in completion.outputs]
            if mode == 'generate':
                item = dict(row, **parse_question(texts[0]), raw_output=texts[0])
            elif mode == 'solve':
                item = dict(row, **majority(texts, job['phase']))
            else:
                matches = re.findall(r'<CODE>(.*?)</CODE>', texts[0], re.S)
                # No expensive repair or retry: missing tags use the raw completion.
                code = matches[-1].strip() if matches else texts[0].strip()
                if not code:
                    raise RuntimeError(f"Empty SAM code for row {row['id']}; see worker input")
                try:
                    ast.parse(code)
                    syntax_ok = True
                except SyntaxError:
                    syntax_ok = False
                item = dict(row, code=code, raw_code_output=texts[0],
                            code_tags_ok=bool(matches), code_syntax_ok=syntax_ok,
                            code_truncated=completion.outputs[0].finish_reason == 'length')
            output.append(item)
    return output


def embed(job):
    import torch
    import torch.nn.functional as F
    from transformers import AutoModel, AutoTokenizer
    cfg = job['config']
    tokenizer = AutoTokenizer.from_pretrained(job['model'], padding_side='left')
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModel.from_pretrained(job['model'], torch_dtype=torch.bfloat16,
                                      attn_implementation='sdpa').to('cuda').eval()
    output = []
    for begin in range(0, len(job['rows']), cfg['embedding_batch']):
        rows = job['rows'][begin:begin + cfg['embedding_batch']]
        # Same representation for candidates AND memory: raw code, no query/doc prefixes.
        batch = tokenizer([r['code'] for r in rows], padding=True, truncation=True,
                          max_length=cfg['embedding_tokens'], return_tensors='pt').to('cuda')
        with torch.inference_mode():
            hidden = model(**batch).last_hidden_state
            vectors = F.normalize(hidden[:, -1].float(), p=2, dim=1).cpu().tolist()
        output.extend(dict(row, embedding=vector) for row, vector in zip(rows, vectors))
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    job = read_json(args.input)
    rows = embed(job) if job['mode'] == 'embed' else generate(job)
    if len(rows) != len(job['rows']):
        raise RuntimeError('GPU worker lost rows')
    write_json(args.output, rows)


if __name__ == '__main__':
    main()
