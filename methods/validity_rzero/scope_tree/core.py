"""Single-answer parsing and a bounded, incremental two-level tree builder."""
import re

from . import prompts


class BudgetExhausted(RuntimeError):
    pass


class SchemaError(ValueError):
    pass


def parse_response(text):
    openings = list(re.finditer(r'<box\s*>', text, re.IGNORECASE))
    closings = list(re.finditer(r'<[/\\]box\s*>', text, re.IGNORECASE))
    if len(openings) != 1 or len(closings) != 1 or openings[0].end() > closings[0].start():
        raise SchemaError('Expected one complete <box>answer</box>')
    answer = text[openings[0].end():closings[0].start()].strip()
    if not answer:
        raise SchemaError('The box answer is empty')
    return answer


def description(answer):
    if answer.upper() in ('YES', 'NO', 'NONE'):
        raise SchemaError('This task needs one description in the box, not a verdict')
    return answer


def decision(answer):
    if answer.upper() not in ('YES', 'NO'):
        raise SchemaError('This task needs only YES or NO in the box')
    return answer.upper() == 'YES'


def gap_answer(answer):
    if answer.upper() == 'NONE':
        return None
    return description(answer)


def response_diagnostics(text):
    return {'raw_characters': len(text),
            'box_open_count': len(re.findall(r'<box\s*>', text, re.IGNORECASE)),
            'box_close_count': len(re.findall(r'<[/\\]box\s*>', text, re.IGNORECASE)),
            'raw_head': text[:250], 'raw_tail': text[-350:]}


def node(node_id, parent_id, depth, text):
    # The whole answer is the scope. No extraction of name/scope/distinction fields.
    return {'id': node_id, 'parent_id': parent_id, 'depth': depth,
            'name': text, 'scope': text, 'children': []}


def leaf_records(root):
    return [c for p in root['children'] for c in p['children']]


def normalized(text):
    return ' '.join(text.casefold().split())


class TreeBuilder:
    def __init__(self, client, max_repairs=2, checkpoint=None, max_children_per_parent=16):
        self.client = client
        self.max_repairs = max_repairs
        self.max_children = max_children_per_parent
        self.checkpoint = checkpoint or (lambda root, status: None)
        self.root = node('root', None, 0, prompts.ROOT_SCOPE)
        self.root['name'] = 'Competition-mathematics problem scopes'
        self.status = {'state': 'building', 'parents': {}, 'coverage_no': {}, 'global': 'pending'}

    def save(self):
        self.checkpoint(self.root, self.status)

    def mark(self, parent, state):
        self.status['parents'][parent['id']] = state
        self.save()
        return state == 'accepted'

    def accept_one(self, parent, depth, gap, number):
        prefix = f"{parent['id']}/candidate/{number}"
        candidate = self.client.request(prefix + '/propose', prompts.propose(parent, depth, gap), description)
        accepted = {normalized(c['scope']) for c in parent['children']}
        seen = set()
        for attempt in range(self.max_repairs + 1):
            signature = normalized(candidate)
            if signature in seen:
                return self.mark(parent, 'stalled_duplicate_candidate')
            seen.add(signature)
            if signature in accepted:
                ok, feedback = False, 'This is an exact duplicate of an accepted family. Give a distinct replacement.'
            else:
                ok = self.client.request(f'{prefix}/audit/{attempt}', prompts.audit(parent, candidate, depth), decision)
                feedback = getattr(self.client, 'last_raw_completion', 'The candidate was rejected; reconsider all suitability criteria.')
            if ok:
                node_id = str(number) if depth == 1 else f"{parent['id']}.{number}"
                parent['children'].append(node(node_id, parent['id'], depth, candidate))
                self.status['coverage_no'][parent['id']] = 0
                self.save()
                return True
            if attempt == self.max_repairs:
                return self.mark(parent, 'repair_budget_exhausted')
            candidate = self.client.request(f'{prefix}/repair/{attempt}',
                                            prompts.repair(parent, candidate, feedback, depth), description)
        raise AssertionError('unreachable')

    def build_children(self, parent, depth):
        prefix = parent['id']
        self.mark(parent, 'building')
        parent['partition_principle'] = self.client.request(prefix + '/principle', prompts.principle(parent, depth), description)
        self.status['coverage_no'][prefix] = 0
        gap, seen_gaps = None, set()
        while True:
            if len(parent['children']) >= self.max_children:
                return self.mark(parent, 'children_limit_exhausted')
            number = len(parent['children']) + 1
            if not self.accept_one(parent, depth, gap, number):
                return False
            # Each accepted single candidate hands control back to the program.
            # Coverage checks share the same input but not the preceding verdict.
            for confirmation in range(2):
                gap = self.client.request(f'{prefix}/coverage/{number}/{confirmation}',
                                          prompts.coverage(parent, depth), gap_answer)
                if gap is not None:
                    self.status['coverage_no'][prefix] = 0
                    self.save()
                    break
                self.status['coverage_no'][prefix] = confirmation + 1
                self.save()
            if gap is None:
                return self.mark(parent, 'accepted')
            signature = normalized(gap)
            if signature in seen_gaps:
                return self.mark(parent, 'stalled_repeated_gap')
            seen_gaps.add(signature)

    def build(self):
        self.save()
        try:
            ok = self.build_children(self.root, 1)
            if ok:
                for parent in self.root['children']:
                    if not self.build_children(parent, 2):
                        ok = False
                        break
            if ok:
                ok = self.client.request('global/audit', prompts.global_audit(self.root), decision)
                self.status['global'] = 'accepted' if ok else 'unresolved'
        except BudgetExhausted as exc:
            self.status['stop_reason'] = 'call_budget_exhausted'
            self.status['error'] = str(exc)
            ok = False
        self.status['state'] = 'accepted' if ok else 'unresolved'
        self.save()
        return ok
