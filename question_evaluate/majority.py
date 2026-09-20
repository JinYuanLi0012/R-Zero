"""Shared R-Zero answer clustering and base-solver prompt rendering."""
SYSTEM_PROMPT = r'Please reason step by step, and put your final answer within \boxed{}.'


def render_prompt(tokenizer, question):
    chat = [{'role': 'system', 'content': SYSTEM_PROMPT}, {'role': 'user', 'content': question}]
    if tokenizer.chat_template:
        return tokenizer.apply_chat_template(chat, tokenize=False, add_generation_prompt=True, add_special_tokens=True)
    return 'system: ' + SYSTEM_PROMPT + '\nuser: ' + question


def majority_vote(results, compare):
    """Same ordered, bidirectional grouping as evaluate.py; ties use first group.

    compare(a,b) must implement the caller's timeout and return TIMED_OUT on timeout.
    Score denominator is nonempty extracted answers, not requested sample count.
    The historical 'no ' heuristic is intentionally preserved.
    """
    results = [r for r in results if r]
    counts = {}
    for result in results:
        matched = False
        for existing in counts:
            if result == existing or ('no ' in result.lower() and 'no ' in existing.lower()):
                matched = True
            else:
                first = compare(result, existing)
                if first == 'TIMED_OUT':
                    continue
                if first:
                    matched = True
                else:
                    second = compare(existing, result)
                    if second == 'TIMED_OUT':
                        continue
                    matched = bool(second)
            if matched:
                counts[existing] += 1
                break
        if not matched:
            counts[result] = 1
    if not counts:
        return {'answer': None, 'score': None, 'answer_counts': {}, 'results': []}
    answer = max(counts, key=counts.get)
    return {'answer': answer, 'score': counts[answer] / len(results),
            'answer_counts': counts, 'results': results}
