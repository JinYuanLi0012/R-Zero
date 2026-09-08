"""CPU-only schemas and bounded PROPOSE / AUDIT / REPAIR state machine."""

from copy import deepcopy
import itertools
import json
import re

from . import prompts


class BudgetExhausted(RuntimeError):
    pass


class SchemaError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise SchemaError(message)


def obj(value, keys, label):
    require(isinstance(value, dict), f"{label} must be an object")
    require(set(value) == set(keys), f"{label} keys must be {sorted(keys)}")


def string(value, label, empty=False):
    require(isinstance(value, str) and (empty or bool(value.strip())), f"{label} must be a string" )


def array(value, label):
    require(isinstance(value, list), f"{label} must be a list")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


JSON_FENCE = re.compile(r"```(?:json)?[ \t]*\r?\n(.*?)\r?\n[ \t]*```", re.DOTALL | re.IGNORECASE)


def final_box(text):
    # An explicit final box takes precedence over drafts. Broken or repeated
    # final tags must not silently fall back to a different result.
    if "<final_json>" in text or "</final_json>" in text:
        for tag in ("<final_json>", "</final_json>"):
            require(text.count(tag) == 1, f"expected exactly one {tag}")
        match = re.search(r"<final_json>(.*?)</final_json>", text, re.DOTALL)
        require(match is not None, "final_json opening and closing delimiters are out of order")
        return match, "final_json"
    # Base can instead produce reasoning followed by one Markdown JSON box.
    # Never search arbitrary bare objects or choose among multiple code blocks.
    match = JSON_FENCE.search(text)
    require(text.count("```") == 2 and match is not None,
            "expected one complete final_json box or one unambiguous JSON code fence")
    return match, "json_fence"


def parse_response(text):
    # Analysis is free text, not a second machine-readable payload. Base models
    # may use plain prose, <think>, or <analysis>; none changes the final schema.
    match, box_format = final_box(text)
    # Keep the requested reasoning-before-result protocol, without requiring its
    # exact spelling or tag syntax. This is a presence check, not a reasoning judge.
    analysis = re.sub(r"</?(?:analysis|think)>", "", text[:match.start()]).strip()
    require(bool(analysis), "missing analysis before final result; reason briefly before the final result")
    payload = match[1].strip()
    # Harmless fenced JSON inside the designated box is still unambiguous.
    fence = JSON_FENCE.fullmatch(payload) if box_format == "final_json" else None
    if fence:
        payload = fence[1].strip()
    try:
        data = json.loads(payload, object_pairs_hook=unique_object,
                          parse_constant=lambda x: (_ for _ in ()).throw(SchemaError(f"invalid JSON constant {x}")))
    except json.JSONDecodeError as exc:
        raise SchemaError(f"invalid JSON: {exc.msg}") from exc
    require(isinstance(data, dict), "final_json must contain an object")
    return data


def response_diagnostics(text):
    """Cheap output-shape evidence for console logs and persisted attempts."""
    try:
        match, box_format = final_box(text)
        prefix = text[:match.start()]
    except SchemaError:
        box_format, prefix = None, ""
    analysis = re.sub(r"</?(?:analysis|think)>", "", prefix).strip()
    return {
        "raw_characters": len(text),
        "final_json_open_count": text.count("<final_json>"),
        "final_json_close_count": text.count("</final_json>"),
        "final_box_format": box_format,
        "has_analysis_before_final": bool(analysis),
        "raw_head": text[:300],
        "raw_tail": text[-500:],
    }


def child_schema(child):
    obj(child, ("name", "scope", "distinguishing_feature"), "child")
    for key, value in child.items():
        string(value, key)
    return child


def child_names(children):
    names = [" ".join(c["name"].lower().split()) for c in children]
    require(len(names) == len(set(names)), "duplicate sibling names")
    require(bool(children), "a partition cannot be empty")


def validate_proposal(data):
    obj(data, ("partition_principle", "children"), "proposal")
    string(data["partition_principle"], "partition_principle")
    array(data["children"], "children")
    for child in data["children"]:
        child_schema(child)
    child_names(data["children"])
    return data


def validate_audit(data, children, depth=None):
    depth = depth or children[0]["depth"]
    checks = ("fits_parent", "follows_principle", "comparable_breadth")
    if depth == 2:
        checks += ("generation_ready",)
    obj(data, ("principle_ok", "principle_feedback", "children", "pairs"), "audit")
    require(type(data["principle_ok"]) is bool, "principle_ok must be boolean")
    string(data["principle_feedback"], "principle_feedback", empty=data["principle_ok"])
    array(data["children"], "children")
    array(data["pairs"], "pairs")
    ids = {c["id"] for c in children}
    seen, decisions = set(), {}
    for row in data["children"]:
        obj(row, ("id", "action", "reason") + checks, "child audit")
        string(row["id"], "id")
        require(row["id"] in ids and row["id"] not in seen, "unknown or repeated child audit id")
        seen.add(row["id"])
        for key in checks:
            require(type(row[key]) is bool, f"{key} must be boolean")
        require(row["action"] in ("KEEP", "REVISE", "REMOVE"), "invalid child action")
        if row["action"] == "KEEP":
            require(all(row[k] for k in checks),
                    "KEEP contradicts failed child checks")
            require(data["principle_ok"], "unusable principle cannot retain accepted children")
        string(row["reason"], "reason")
        decisions[row["id"]] = row["action"]
    require(seen == ids, "audit must assess every child")
    pairs = set()
    for row in data["pairs"]:
        obj(row, ("a", "b", "relation", "reason"), "pair audit")
        string(row["a"], "a")
        string(row["b"], "b")
        require(row["a"] in ids and row["b"] in ids and row["a"] != row["b"], "invalid pair endpoints")
        pair = tuple(sorted((row["a"], row["b"])))
        require(pair not in pairs, "duplicate pair audit")
        pairs.add(pair)
        require(row["relation"] in ("DISTINCT", "OVERLAP", "NESTED", "NEAR_DUPLICATE"), "invalid pair relation")
        if row["relation"] != "DISTINCT":
            require(any(decisions[i] != "KEEP" for i in pair), "overlapping pair cannot keep both children")
        string(row["reason"], "reason")
    require(pairs == set(itertools.combinations(sorted(ids), 2)), "audit must cover EVERY unordered sibling pair")
    return data


def passed(audit):
    return audit["principle_ok"] and all(
        row["action"] == "KEEP" for row in audit["children"]
    )


def new_node(parent, depth, serial, child):
    node_id = str(serial) if depth == 1 else f"{parent['id']}.{serial}"
    return {"id": node_id, "depth": depth, **child, "parent_id": parent["id"], "children": []}


def apply_repair(data, parent, children, audit, depth):
    obj(data, ("partition_principle", "replacements"), "repair")
    string(data["partition_principle"], "partition_principle")
    if audit["principle_ok"]:
        require(data["partition_principle"] == parent["partition_principle"], "accepted partition principle is immutable")
    array(data["replacements"], "replacements")
    rejected = {row["id"]: row["action"] for row in audit["children"] if row["action"] != "KEEP"}
    replacements = {}
    for row in data["replacements"]:
        obj(row, ("id", "child"), "replacement")
        string(row["id"], "id")
        require(row["id"] in rejected and row["id"] not in replacements, "replacement must target each rejected id exactly once")
        if row["child"] is not None:
            child_schema(row["child"])
            require(rejected[row["id"]] != "REMOVE", "REMOVE requires child=null")
        replacements[row["id"]] = row["child"]
    require(set(replacements) == set(rejected), "missing rejected child replacements")
    result = []
    for child in children:
        if child["id"] not in replacements:
            result.append(deepcopy(child))
        elif replacements[child["id"]] is not None:
            result.append({**deepcopy(child), **replacements[child["id"]]})
    child_names(result)
    return {"partition_principle": data["partition_principle"], "children": result}


def leaf_records(root):
    return [
        {"id": leaf["id"], "parent_id": parent["id"],
         "path": [root["name"], parent["name"], leaf["name"]],
         "name": leaf["name"], "scope": leaf["scope"],
         "distinguishing_feature": leaf["distinguishing_feature"],
         "parent_partition_principle": parent["partition_principle"]}
        for parent in root["children"] for leaf in parent["children"]
    ]


def validate_global(data, leaves):
    obj(data, ("issues",), "global audit")
    array(data["issues"], "issues")
    lookup = {c["id"]: c for c in leaves}
    seen = set()
    for issue in data["issues"]:
        obj(issue, ("a", "b", "relation", "revise_id", "reason"), "global issue")
        for key in ("a", "b", "revise_id"):
            string(issue[key], key)
        a, b = issue["a"], issue["b"]
        require(a in lookup and b in lookup and a != b, "invalid global pair ids")
        require(lookup[a]["parent_id"] != lookup[b]["parent_id"], "global issue must cross branches")
        pair = tuple(sorted((a, b)))
        require(pair not in seen, "duplicate global issue")
        seen.add(pair)
        require(issue["revise_id"] in pair, "revise_id must be one pair endpoint")
        require(issue["relation"] in ("STRONG_OVERLAP", "NEAR_DUPLICATE", "NESTED"), "invalid global relation")
        string(issue["reason"], "reason")
    return data


def validate_coverage(data):
    obj(data, ("has_major_gap", "gap_description", "reason"), "coverage")
    require(type(data["has_major_gap"]) is bool, "has_major_gap must be boolean")
    string(data["reason"], "reason")
    if data["has_major_gap"]:
        string(data["gap_description"], "gap_description")
    else:
        require(data["gap_description"] is None, "NO major gap requires gap_description=null")
    return data


def validate_addition(data, children):
    obj(data, ("child",), "single addition")
    child_schema(data["child"])
    child_names(children + [data["child"]])
    return data["child"]


def validate_global_addition(data, root):
    obj(data, ("parent_id", "child"), "global addition")
    string(data["parent_id"], "parent_id")
    parents = {p["id"]: p for p in [root] + root["children"]}
    require(data["parent_id"] in parents, "addition parent must be root or existing L1")
    validate_addition({"child": data["child"]}, parents[data["parent_id"]]["children"])
    return data


def partition_state(parent):
    # Descendant expansion does not change this parent's sibling allocation.
    return json.dumps({"principle": parent["partition_principle"],
                       "children": [{k: c[k] for k in ("id", "name", "scope", "distinguishing_feature")}
                                    for c in parent["children"]]}, sort_keys=True)


class TreeBuilder:
    def __init__(self, client, max_repairs=2, checkpoint=None, max_children_per_parent=16):
        self.client = client
        self.max_repairs = max_repairs
        self.max_children = max_children_per_parent
        self.checkpoint = checkpoint or (lambda root, status: None)
        self.status = {"state": "building", "parents": {}, "coverage": {}, "global": "pending"}
        self.root = {"id": "root", "depth": 0, "name": "Competition-mathematics problem scopes",
                     "scope": prompts.ROOT_SCOPE, "distinguishing_feature": prompts.GLOBAL_REQUIREMENT,
                     "parent_id": None, "children": []}
        self.serials = {}

    def save(self):
        self.checkpoint(self.root, self.status)

    def mark(self, parent, state):
        self.status["parents"][parent["id"]] = state
        self.save()
        return state == "accepted"

    def reset_coverage(self, parent):
        self.status["coverage"][parent["id"]] = {"consecutive_no": 0, "partition": partition_state(parent)}
        self.mark(parent, "checking")

    def append_child(self, parent, depth, child):
        serial = max(self.serials.get(parent["id"], 0),
                     max((int(c["id"].split(".")[-1]) for c in parent["children"]), default=0)) + 1
        self.serials[parent["id"]] = serial
        parent["children"].append(new_node(parent, depth, serial, child))
        self.reset_coverage(parent)

    def build_children(self, parent, depth):
        proposal = self.client.request(f"{parent['id']}/propose", prompts.propose(parent, depth), validate_proposal)
        parent["partition_principle"] = proposal["partition_principle"]
        parent["children"] = [new_node(parent, depth, i, c) for i, c in enumerate(proposal["children"], 1)]
        self.serials[parent["id"]] = len(parent["children"])
        return self.settle(parent, depth, parent["id"])

    def settle(self, parent, depth, prefix, allow_changes=True, protected=()):
        """Audit and double-check coverage; any change restarts both checks.

        Repair budget is shared across all additions in this local build. Accepted
        children stay protected across subsequent repairs and additions. Verification-only global
        passes cannot start a second repair/addition sweep.
        """
        self.reset_coverage(parent)
        states, gaps = {partition_state(parent)}, set()
        protected = set(protected)
        repairs, epoch = 0, 0
        while True:
            if len(parent["children"]) > self.max_children:
                return self.mark(parent, "children_limit_exhausted")
            children = parent["children"]
            review = self.client.request(f"{prefix}/audit/{epoch}", prompts.audit(parent, children, depth),
                                         lambda d: validate_audit(d, children, depth))
            if not passed(review):
                if not allow_changes:
                    return self.mark(parent, "verification_failed")
                if any(r["id"] in protected and r["action"] != "KEEP" for r in review["children"]):
                    return self.mark(parent, "protected_sibling_conflict")
                if repairs >= self.max_repairs:
                    return self.mark(parent, "repair_budget_exhausted")
                protected.update(r["id"] for r in review["children"] if r["action"] == "KEEP")
                result = self.client.request(f"{prefix}/repair/{repairs}", prompts.repair(parent, children, review, depth),
                                             lambda d: apply_repair(d, parent, children, review, depth))
                parent.update(result)
                repairs += 1
            else:
                self.mark(parent, "checking_coverage")
                gap = None
                # Distinct labels produce distinct samples; each receives identical
                # state, never the previous judge's verdict. This is not a claim of
                # statistical independence of same-model judgments.
                for confirmation in range(2):
                    coverage = self.client.request(f"{prefix}/coverage/{epoch}/{confirmation}",
                                                   prompts.coverage_check(parent, children, depth), validate_coverage)
                    if coverage["has_major_gap"]:
                        gap = coverage["gap_description"]
                        self.status["coverage"][parent["id"]]["consecutive_no"] = 0
                        self.save()
                        break
                    self.status["coverage"][parent["id"]]["consecutive_no"] = confirmation + 1
                    self.save()
                if gap is None:
                    return self.mark(parent, "accepted")
                if not allow_changes:
                    return self.mark(parent, "coverage_unresolved")
                signature = " ".join(gap.casefold().split())
                if signature in gaps:
                    return self.mark(parent, "stalled_repeated_gap")
                gaps.add(signature)
                if len(children) >= self.max_children:
                    return self.mark(parent, "children_limit_exhausted")
                protected.update(c["id"] for c in children)
                child = self.client.request(f"{prefix}/addition/{epoch}",
                                            prompts.gap_addition(parent, children, depth, gap),
                                            lambda d: validate_addition(d, children))
                self.append_child(parent, depth, child)
            state = partition_state(parent)
            self.reset_coverage(parent)
            if state in states:
                return self.mark(parent, "stalled")
            states.add(state)
            epoch += 1

    def global_audit(self, label):
        leaves = leaf_records(self.root)
        return self.client.request(label, prompts.global_audit(leaves), lambda d: validate_global(d, leaves))

    def check_global_coverage(self, phase):
        self.status["global_coverage_no"] = 0
        for confirmation in range(2):
            result = self.client.request(f"global/coverage/{phase}/{confirmation}",
                                         prompts.global_coverage(self.root, leaf_records(self.root)), validate_coverage)
            if result["has_major_gap"]:
                self.status["global_coverage_no"] = 0
                self.save()
                return result
            self.status["global_coverage_no"] = confirmation + 1
            self.save()
        return result

    def finish_global(self):
        review = self.global_audit("global/audit/0")
        coverage = self.check_global_coverage(0)
        if not review["issues"] and not coverage["has_major_gap"]:
            self.status["global"] = "accepted"
            return True
        self.status["global"] = "repairing"
        self.status["global_coverage_no"] = 0
        affected = {}
        for parent in self.root["children"]:
            issues = [i for i in review["issues"] if i["revise_id"] in {c["id"] for c in parent["children"]}]
            if not issues:
                continue
            targets = {i["revise_id"] for i in issues}
            feedback = {"principle_ok": True, "principle_feedback": "Preserve accepted parent partition.",
                        "children": [{"id": c["id"], "action": "REVISE" if c["id"] in targets else "KEEP"}
                                     for c in parent["children"]],
                        "global_issues": issues, "all_leaves": leaf_records(self.root)}
            children = parent["children"]
            before = partition_state(parent)
            result = self.client.request(f"global/repair/{parent['id']}", prompts.repair(parent, children, feedback, 2),
                                         lambda d: apply_repair(d, parent, children, feedback, 2))
            parent.update(result)
            self.reset_coverage(parent)
            if partition_state(parent) == before:
                self.mark(parent, "stalled")
                self.status["global"] = "unresolved"
                return False
            affected[parent["id"]] = (parent, 2)
        new_branch = None
        if coverage["has_major_gap"]:
            addition = self.client.request("global/addition", prompts.global_addition(
                self.root, leaf_records(self.root), coverage["gap_description"]),
                lambda d: validate_global_addition(d, self.root))
            parent = next(p for p in [self.root] + self.root["children"] if p["id"] == addition["parent_id"])
            if len(parent["children"]) >= self.max_children:
                self.mark(parent, "children_limit_exhausted")
                self.status["global"] = "unresolved"
                return False
            depth = parent["depth"] + 1
            self.append_child(parent, depth, addition["child"])
            affected[parent["id"]] = (parent, depth)
            if parent is self.root:
                new_branch = parent["children"][-1]
        # Exactly one global sweep. Verify affected siblings and reset coverage;
        # no further changes here. A new L1 must first pass root verification,
        # then receive a complete ordinary L2 build before final global checks.
        local_ok = True
        for parent, depth in affected.values():
            ok = self.settle(parent, depth, f"global/verify/{parent['id']}", allow_changes=False)
            local_ok = ok and local_ok
        if new_branch is not None and local_ok:
            local_ok = self.build_children(new_branch, 2)
        if not local_ok:
            self.status["global"] = "unresolved"
            return False
        final = self.global_audit("global/audit/1")
        final_coverage = self.check_global_coverage(1)
        ok = not final["issues"] and not final_coverage["has_major_gap"]
        self.status["global"] = "accepted" if ok else "unresolved"
        return ok

    def build(self):
        self.save()
        try:
            all_ok = self.build_children(self.root, 1)
            if all_ok:
                for parent in self.root["children"]:
                    ok = self.build_children(parent, 2)
                    all_ok = ok and all_ok
                if all_ok:
                    all_ok = self.finish_global()
        except BudgetExhausted as exc:
            self.status["error"] = str(exc)
            self.status["stop_reason"] = "call_budget_exhausted"
            all_ok = False
        self.status["state"] = "accepted" if all_ok else "unresolved"
        self.save()
        return all_ok
