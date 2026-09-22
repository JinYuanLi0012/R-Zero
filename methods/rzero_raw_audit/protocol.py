"""Frozen ordinary R-Zero Phase-B protocol; no training-path imports or writes."""
from __future__ import annotations
import re

# Copied verbatim from question_generate/question_generate.py at 3259270.
QUESTIONER_CHAT = [{'role': 'system',
  'content': 'You are an expert competition-math problem setter.\n'
             'FIRST, in your private scratch-pad, think step-by-step to design a brand-new, '
             'non-trivial problem. The problem could come from any field of mathematics, including '
             'but not limited to algebra, geometry, number theory, combinatorics, prealgebra, '
             'probability, statistics, and calculus. Aim for a difficulty such that fewer than 30 '
             '% of advanced high-school students could solve it. Avoid re-using textbook clichés '
             'or famous contest problems.\n'
             'THEN, without revealing any of your private thoughts, output **exactly** the '
             'following two blocks:\n'
             '\n'
             '<question>\n'
             '{The full problem statement on one or more lines}\n'
             '</question>\n'
             '\n'
             '\\boxed{final_answer}\n'
             '\n'
             'Do NOT output anything else—no explanations, no extra markup.'},
 {'role': 'user',
  'content': 'Generate one new, challenging reasoning question now. Remember to format the output '
             'exactly as instructed.'}]
SOLVER_SYSTEM = "Please reason step by step, and put your final answer within \\boxed{}."
QUESTIONER_SAMPLING = dict(max_tokens=4096, temperature=1.0, top_p=0.95, n=1)
SOLVER_SAMPLING = dict(max_tokens=4096, temperature=1.0, top_p=1.0, top_k=40, n=9)


def render(tokenizer, chat):
    if tokenizer.chat_template:
        return tokenizer.apply_chat_template(chat, tokenize=False,
            add_generation_prompt=True, add_special_tokens=True)
    return "system: " + chat[0]["content"] + "\nuser: " + chat[1]["content"]


def parse_question(response):
    # Same tags/last boxed answer as the original generator. Retain raw text
    # separately so malformed output is never silently replaced or discarded.
    questions = re.findall(r"<question>(.*?)</question>", response, re.DOTALL)
    answers, i = [], 0
    prefix = r"\boxed{"
    while True:
        start = response.find(prefix, i)
        if start == -1:
            break
        j, depth = start + len(prefix), 1
        while j < len(response) and depth:
            if response[j] == "{": depth += 1
            elif response[j] == "}": depth -= 1
            j += 1
        answers.append(response[start + len(prefix):j-1])
        i = j
    parsed = bool(questions and answers)
    return dict(question=questions[-1].strip() if parsed else None,
                questioner_answer=answers[-1].strip() if parsed else None,
                questioner_parse_ok=parsed)


def majority_vote(extracted, grader):
    """Exact legacy ordering, bidirectional grading and nonempty denominator.

    Unlike majority vote over nine raw slots, R-Zero drops unparsed answers
    before calculating score. Ties keep the first encountered representative.
    A timeout skips that existing cluster without trying the reverse direction.
    """
    results = [answer for answer in extracted if answer]
    counts = {}
    for answer in results:
        matched = False
        for existing in counts:
            if answer == existing or ('no ' in answer.lower() and 'no ' in existing.lower()):
                counts[existing] += 1
                matched = True
                break
            first = grader(answer, existing, timeout=10)
            if first == 'TIMED_OUT': continue
            if first:
                counts[existing] += 1
                matched = True
                break
            second = grader(existing, answer, timeout=10)
            if second == 'TIMED_OUT': continue
            if second:
                counts[existing] += 1
                matched = True
                break
        if not matched:
            counts[answer] = 1
    winner = max(counts, key=counts.get) if counts else None
    largest = counts[winner] if winner is not None else 0
    return dict(majority_answer=winner, majority_count=largest,
                parsed_answer_count=len(results), answer_counts=counts,
                results=results, score=largest / len(results) if results else None,
                majority_fraction_of_all_votes=largest / len(extracted) if extracted else None,
                tied_largest_clusters=sum(count == largest for count in counts.values()))


def legacy_filter_reasons(question, vote):
    reasons = []
    if not vote['parsed_answer_count']: reasons.append('no_parsed_solver_answer')
    if "证明" in question: reasons.append('question_contains_proof_keyword')
    if 'box' in question.lower(): reasons.append('question_contains_box')
    if 'text' in (vote['majority_answer'] or '').lower(): reasons.append('answer_contains_text')
    if vote['score'] is not None and not 0.3 <= vote['score'] <= 0.8:
        reasons.append('score_outside_0.3_0.8')
    if vote['majority_answer'] in ('', 'None', None): reasons.append('empty_majority_answer')
    return reasons
