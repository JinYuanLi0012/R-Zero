"""CPU-only schemas and bounded PROPOSE / AUDIT / REPAIR state machine."""

from copy import deepcopy
import itertools
import json
import re

from . import prompts


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


def parse_response(text):
    for tag in ("<analysis>", "</analysis>", "<final_json>", "</final_json>"):
        require(text.count(tag) == 1, f"expected exactly one {tag}")
    match = re.fullmatch(
        r"\s*<analysis>(.*?)</analysis>\s*<final_json>(.*?)</final_json>\s*", text, re.DOTALL
    )
    require(match is not None, "expected analysis then final_json, without extra text")
    require(bool(match[1].strip()), "analysis block must be nonempty")
    try:
        data = json.loads(match[2], object_pairs_hook=unique_object,
                          parse_constant=lambda x: (_ for _ in ()).throw(SchemaError(f"invalid JSON constant {x}")))
    except json.JSONDecodeError as exc:
        raise SchemaError(f"invalid JSON: {exc.msg}") from exc
    require(isinstance(data, dict), "final_json must contain an object")
    return data


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


def validate_audit(data, children):
    obj(data, ("principle_ok", "principle_feedback", "children", "pairs", "gap"), "audit")
    require(type(data["principle_ok"]) is bool, "principle_ok must be boolean")
    string(data["principle_feedback"], "principle_feedback", empty=data["principle_ok"])
    require(data["gap"] is None or isinstance(data["gap"], str) and bool(data["gap"].strip()),
            "gap must be null or a nonempty structural gap description")
    array(data["children"], "children")
    array(data["pairs"], "pairs")
    ids = {c["id"] for c in children}
    seen, decisions = set(), {}
    for row in data["children"]:
        obj(row, ("id", "fits_parent", "follows_principle", "granularity_ok", "action", "reason"), "child audit")
        string(row["id"], "id")
        require(row["id"] in ids and row["id"] not in seen, "unknown or repeated child audit id")
        seen.add(row["id"])
        for key in ("fits_parent", "follows_principle", "granularity_ok"):
            require(type(row[key]) is bool, f"{key} must be boolean")
        require(row["action"] in ("KEEP", "REVISE", "REMOVE"), "invalid child action")
        if row["action"] == "KEEP":
            require(all(row[k] for k in ("fits_parent", "follows_principle", "granularity_ok")),
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
    return audit["principle_ok"] and audit["gap"] is None and all(
        row["action"] == "KEEP" for row in audit["children"]
    )


def new_node(parent, depth, serial, child):
    node_id = str(serial) if depth == 1 else f"{parent['id']}.{serial}"
    return {"id": node_id, "depth": depth, **child, "parent_id": parent["id"], "children": []}


def apply_repair(data, parent, children, audit, depth):
    obj(data, ("partition_principle", "replacements", "additions"), "repair")
    string(data["partition_principle"], "partition_principle")
    if audit["principle_ok"]:
        require(data["partition_principle"] == parent["partition_principle"], "accepted partition principle is immutable")
    array(data["replacements"], "replacements")
    array(data["additions"], "additions")
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
    require(audit["gap"] is not None or not data["additions"], "additions require an audited structural gap")
    for child in data["additions"]:
        child_schema(child)
    result = []
    for child in children:
        if child["id"] not in replacements:
            result.append(deepcopy(child))
        elif replacements[child["id"]] is not None:
            result.append({**deepcopy(child), **replacements[child["id"]]})
    # Never reuse ids removed during this repair; ids remain stable for kept nodes.
    serial = max(int(c["id"].split(".")[-1]) for c in children)
    for child in data["additions"]:
        serial += 1
        result.append(new_node(parent, depth, serial, child))
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


class TreeBuilder:
    def __init__(self, client, max_repairs=2, checkpoint=None):
        self.client = client
        self.max_repairs = max_repairs
        self.checkpoint = checkpoint or (lambda root, status: None)
        self.status = {"state": "building", "parents": {}, "global": "pending"}
        self.root = {"id": "root", "depth": 0, "name": prompts.ROOT_SCOPE,
                     "scope": prompts.ROOT_SCOPE, "distinguishing_feature": prompts.GLOBAL_REQUIREMENT,
                     "parent_id": None, "children": []}

    def save(self):
        self.checkpoint(self.root, self.status)

    def build_children(self, parent, depth):
        prefix = parent["id"]
        proposal = self.client.request(f"{prefix}/propose", prompts.propose(parent, depth), validate_proposal)
        parent["partition_principle"] = proposal["partition_principle"]
        parent["children"] = [new_node(parent, depth, i, child) for i, child in enumerate(proposal["children"], 1)]
        self.save()
        states = {json.dumps(parent, sort_keys=True)}
        for iteration in range(self.max_repairs + 1):
            children = parent["children"]
            audit = self.client.request(f"{prefix}/audit/{iteration}", prompts.audit(parent, children, depth),
                                        lambda data: validate_audit(data, children))
            if passed(audit):
                self.status["parents"][prefix] = "accepted"
                self.save()
                return True
            if iteration == self.max_repairs:
                self.status["parents"][prefix] = "repair_budget_exhausted"
                self.save()
                return False
            repair = self.client.request(f"{prefix}/repair/{iteration}", prompts.repair(parent, children, audit, depth),
                                         lambda data: apply_repair(data, parent, children, audit, depth))
            parent.update(repair)
            fingerprint = json.dumps(parent, sort_keys=True)
            if fingerprint in states:
                self.status["parents"][prefix] = "stalled"
                self.save()
                return False
            states.add(fingerprint)
            self.save()
        raise AssertionError("unreachable")

    def global_audit(self, label):
        leaves = leaf_records(self.root)
        return self.client.request(label, prompts.global_audit(leaves), lambda data: validate_global(data, leaves))

    def finish_global(self):
        audit = self.global_audit("global/audit/0")
        if not audit["issues"]:
            self.status["global"] = "accepted"
            return True
        self.status["global"] = "repairing"
        affected = []
        # Exactly one global repair sweep, targeting only implicated leaves.
        for parent in self.root["children"]:
            ids = {c["id"] for c in parent["children"]}
            issues = [i for i in audit["issues"] if i["revise_id"] in ids]
            if not issues:
                continue
            affected.append(parent)
            targets = {i["revise_id"] for i in issues}
            feedback = {"principle_ok": True, "principle_feedback": "Preserve accepted parent partition.",
                        "gap": None, "pairs": [], "children": [
                            {"id": c["id"], "action": "REVISE" if c["id"] in targets else "KEEP",
                             "reason": "Global cross-branch repair" if c["id"] in targets else "Accepted sibling"}
                            for c in parent["children"]],
                        "global_issues": issues, "all_leaves": leaf_records(self.root)}
            children = parent["children"]
            repair = self.client.request(f"global/repair/{parent['id']}", prompts.repair(parent, children, feedback, 2),
                                         lambda data: apply_repair(data, parent, children, feedback, 2))
            parent.update(repair)
            self.save()
        local_ok = True
        for parent in affected:
            children = parent["children"]
            review = self.client.request(f"global/local_reaudit/{parent['id']}", prompts.audit(parent, children, 2),
                                         lambda data: validate_audit(data, children))
            ok = passed(review)
            self.status["parents"][parent["id"]] = "accepted" if ok else "global_repair_local_failure"
            local_ok = local_ok and ok
        final = self.global_audit("global/audit/1")
        self.status["global"] = "accepted" if not final["issues"] and local_ok else "unresolved"
        return self.status["global"] == "accepted"

    def build(self):
        self.save()
        root_ok = self.build_children(self.root, 1)
        if not root_ok:
            self.status["state"] = "unresolved"
            self.save()
            return False
        all_ok = True
        for node in self.root["children"]:
            ok = self.build_children(node, 2)
            all_ok = all_ok and ok
        if all_ok:
            all_ok = self.finish_global()
        self.status["state"] = "accepted" if all_ok else "unresolved"
        self.save()
        return all_ok
