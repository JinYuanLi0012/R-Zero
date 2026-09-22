"""One model on one GPU per process; preserve every raw question and vote."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path

from .protocol import (QUESTIONER_CHAT, QUESTIONER_SAMPLING, SOLVER_SYSTEM,
                       SOLVER_SAMPLING, render, parse_question, majority_vote,
                       legacy_filter_reasons)


def write_rows(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f'.tmp-{os.getpid()}')
    with temporary.open('w') as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False) + '\n')
    os.replace(temporary, path)


def read_rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stage', choices=['generate', 'vote'], required=True)
    parser.add_argument('--model', required=True)
    parser.add_argument('--round', type=int, required=True)
    parser.add_argument('--shard', type=int, required=True)
    parser.add_argument('--count', type=int, required=True)
    parser.add_argument('--input', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    rows = read_rows(args.input) if args.stage == 'vote' else None
    if rows is not None and len(rows) != args.count:
        raise ValueError('Raw shard count mismatch')
    # Mark parse failures before inference. They remain rows, without fabricated
    # mathematical questions or solver votes.
    if rows is not None:
        for row in rows:
            row.update(solver_model=args.model, solver_seed=args.shard,
                       requested_vote_count=SOLVER_SAMPLING['n'],
                       solver_responses=[], solver_answers=[], solver_finish_reasons=[],
                       vote_status='questioner_parse_failed', majority_answer=None,
                       majority_count=0, parsed_answer_count=0, answer_counts={},
                       results=[], score=None, majority_fraction_of_all_votes=None,
                       tied_largest_clusters=0, would_pass_original_filter=False,
                       original_filter_reasons=['questioner_parse_failed'])
        positions = [i for i, row in enumerate(rows) if row['questioner_parse_ok']]
        if not positions:
            write_rows(args.output, rows)
            return

    import vllm
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    if args.stage == 'generate' and tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    options = dict(model=args.model, tokenizer=args.model, seed=args.shard)
    if args.stage == 'vote':
        options['gpu_memory_utilization'] = 0.85
    model = vllm.LLM(**options)
    sampling = QUESTIONER_SAMPLING if args.stage == 'generate' else SOLVER_SAMPLING
    params = vllm.SamplingParams(**sampling, stop_token_ids=[tokenizer.eos_token_id])
    if args.stage == 'generate':
        prompts = [render(tokenizer, QUESTIONER_CHAT)] * args.count
    else:
        prompts = [render(tokenizer, [{'role': 'system', 'content': SOLVER_SYSTEM},
                    {'role': 'user', 'content': rows[i]['question']}]) for i in positions]
    completions = model.generate(prompts, sampling_params=params, use_tqdm=True)
    if len(completions) != len(prompts):
        raise RuntimeError('vLLM returned an incomplete batch')
    if args.stage == 'generate':
        rows = []
        for index, completion in enumerate(completions):
            output = completion.outputs[0]
            rows.append(dict(id=f'q_r{args.round}_s{args.shard}_{index:06d}',
                round=args.round, shard=args.shard, shard_index=index,
                questioner_model=args.model, questioner_seed=args.shard,
                questioner_raw=output.text, questioner_finish_reason=output.finish_reason,
                **parse_question(output.text)))
    else:
        import stopit
        from mathruler.grader import extract_boxed_content, grade_answer

        @stopit.threading_timeoutable(default='TIMED_OUT')
        def timed_grade(first, second):
            return grade_answer(first, second)

        for index, completion in zip(positions, completions):
            row = rows[index]
            raw = [output.text for output in completion.outputs]
            if len(raw) != SOLVER_SAMPLING['n']:
                raise RuntimeError('Incomplete Solver vote group')
            row.update(solver_responses=raw,
                       solver_finish_reasons=[o.finish_reason for o in completion.outputs],
                       solver_seed=args.shard, requested_vote_count=SOLVER_SAMPLING['n'])
            try:
                extracted = [extract_boxed_content(text) for text in raw]
                row['solver_answers'] = extracted  # all nine slots, including empty parses
                vote = majority_vote(extracted, timed_grade)
                reasons = legacy_filter_reasons(row['question'], vote)
                row.update(vote, vote_status='ok' if vote['parsed_answer_count'] else 'no_parsed_answers',
                    original_filter_reasons=reasons, would_pass_original_filter=not reasons)
            except Exception as error:
                row.update(vote_status='grading_error', error=repr(error),
                    original_filter_reasons=['grading_error'], would_pass_original_filter=False)
    write_rows(args.output, rows)
    print(f'[{args.stage}] round={args.round} shard={args.shard} saved={len(rows)} file={args.output}', flush=True)


if __name__ == '__main__':
    main()
