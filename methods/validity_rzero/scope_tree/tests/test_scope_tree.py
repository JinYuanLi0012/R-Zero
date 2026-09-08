"""CPU regressions for the real state machine; no model quality is simulated."""

from copy import deepcopy
import itertools
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

from methods.validity_rzero.scope_tree import prompts
from methods.validity_rzero.scope_tree.core import (
    SchemaError, TreeBuilder, apply_repair, parse_response, passed,
    response_diagnostics, validate_addition, validate_audit, validate_coverage, validate_global, validate_proposal,
)
from methods.validity_rzero.scope_tree.run import (
    BudgetExhausted, ParseRetriesExhausted, StructuredClient,
)
from methods.validity_rzero.scope_tree import run as runner


def child(name):
    return {"name": name, "scope": f"Scope of {name}", "distinguishing_feature": f"Feature of {name}"}


def node(node_id, name):
    return {"id": node_id, "depth": 2 if "." in node_id else 1,
            "parent_id": node_id.split(".")[0] if "." in node_id else "root",
            **child(name), "children": []}


def proposal(names):
    return {"partition_principle": "Shared structural axis", "children": [child(n) for n in names]}


def audit(ids, revise=(), remove=()):
    rows = []
    for i in ids:
        row = {"id": i, "fits_parent": True, "follows_principle": True,
               "comparable_breadth": i not in revise,
               "action": "REMOVE" if i in remove else "REVISE" if i in revise else "KEEP",
               "reason": "Review finding"}
        if "." in i:
            row["generation_ready"] = True
        rows.append(row)
    return {"principle_ok": True, "principle_feedback": "Consistent axis", "children": rows,
            "pairs": [{"a": a, "b": b, "relation": "DISTINCT", "reason": "Different scope"}
                      for a, b in itertools.combinations(ids, 2)]}


def coverage(gap=None):
    return {"has_major_gap": gap is not None, "gap_description": gap, "reason": "Allocation assessment"}


def repair(replacements=None):
    return {"partition_principle": "Shared structural axis",
            "replacements": [{"id": key, "child": value} for key, value in (replacements or {}).items()]}


def wrapped(value):
    return "<analysis>Assess the supplied scope and distinctions.</analysis>\n<final_json>" + json.dumps(value) + "</final_json>"


class FakeBackend:
    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.seeds = []

    def generate(self, system, user, seed):
        self.seeds.append(seed)
        if not self.outputs:
            raise AssertionError("unexpected inference")
        value = self.outputs.pop(0)
        return {"raw_completion": value if isinstance(value, str) else wrapped(value), "finish_reason": "stop"}


class ScriptedClient:
    def __init__(self, script):
        self.script = dict(script)
        self.labels = []

    def request(self, label, prompt, validator):
        self.labels.append(label)
        return validator(deepcopy(self.script[label]))


def confirmations(prefix, epoch=0):
    return {f"{prefix}/coverage/{epoch}/{i}": coverage() for i in range(2)}


def clean_script():
    return {
        "root/propose": proposal(["Broad A", "Broad B"]),
        "root/audit/0": audit(["1", "2"]), **confirmations("root"),
        "1/propose": proposal(["A one", "A two"]),
        "1/audit/0": audit(["1.1", "1.2"]), **confirmations("1"),
        "2/propose": proposal(["B one", "B two"]),
        "2/audit/0": audit(["2.1", "2.2"]), **confirmations("2"),
        "global/audit/0": {"issues": []}, **confirmations("global"),
    }


class SchemaTests(unittest.TestCase):
    def test_analysis_present_and_final_box_unambiguous(self):
        self.assertEqual(parse_response(wrapped({"a": {"b": 1}})), {"a": {"b": 1}})
        invalid = [
            '<final_json>{}</final_json>',
            '<analysis></analysis><final_json>{}</final_json>',
            wrapped({}) + wrapped({}),
            '<analysis>x</analysis><final_json>{"a":1,"a":2}</final_json>',
            '<analysis>x</analysis><final_json>{"a":NaN}</final_json>',
            '<analysis>x</analysis><final_json>{',
        ]
        for raw in invalid:
            with self.subTest(raw=raw), self.assertRaises(SchemaError):
                parse_response(raw)

    def test_plain_or_think_analysis_and_extra_prose_do_not_block_final_json(self):
        data = {"a": {"nested": [1, 2]}, "text": "A {brace} inside a string"}
        final = "<final_json>" + json.dumps(data) + "</final_json>"
        for raw in (
            "First I compare the relevant structures.\n" + final,
            "<think>Compare the scope and granularity.</think>\n" + final,
            "<analysis>Compare structures.</analysis>\nFinal result:\n" + final,
            "<analysis>Compare structures.</analysis>\n" + final + "\nDone.",
            "Compare the scopes.\n<final_json>```json\n" + json.dumps(data) + "\n```</final_json>",
        ):
            with self.subTest(raw=raw):
                self.assertEqual(parse_response(raw), data)

    def test_missing_or_broken_final_still_rejected(self):
        for raw in (
            'I compare the scopes. {"children": []}',
            'I compare. <final_json>{"children": []}',
            'I compare. </final_json>{}<final_json>',
            'I compare. <final_json>{}{}</final_json>',
        ):
            with self.subTest(raw=raw), self.assertRaises(SchemaError):
                parse_response(raw)

    def test_json_fence_fallback_requires_one_complete_box_and_analysis(self):
        self.assertEqual(parse_response('分析：比较对象。\n```json\n{"a": 1}\n```\n说明。'), {"a": 1})
        for raw in (
            '```json\n{}\n```',
            'Reason. ```json\n{}\n```\n```json\n{}\n```',
            'Reason. ```json\n{}',
            'Reason. <final_json>```json\n{}\n```',
            'Reason. ```json\n{"a":1,"a":2}\n```',
            'Reason. ```json\n{"a":NaN}\n```',
        ):
            with self.subTest(raw=raw), self.assertRaises(SchemaError):
                parse_response(raw)

    def test_explicit_final_wins_over_draft_fence(self):
        raw = 'Draft. ```json\n{"draft": true}\n```\nCompare structures.\n<final_json>{"final": true}</final_json>'
        self.assertEqual(parse_response(raw), {"final": True})

    def test_diagnostics_distinguish_missing_final_from_unstructured_analysis(self):
        raw = 'Reasoning in plain text. <final_json>{}</final_json>'
        info = response_diagnostics(raw)
        self.assertEqual(info["final_json_open_count"], 1)
        self.assertEqual(info["final_json_close_count"], 1)
        self.assertTrue(info["has_nonempty_prefix"])
        self.assertEqual(response_diagnostics('long unfinished reasoning')["final_json_open_count"], 0)
        self.assertEqual(response_diagnostics('Reason. ```json\n{}\n```')["final_box_format"], "json_fence")

    def test_adaptive_width_has_no_eight_or_four_limit(self):
        validate_proposal(proposal([f"Family {i}" for i in range(11)]))
        with self.assertRaises(SchemaError):
            validate_proposal(proposal([]))
        with self.assertRaises(SchemaError):
            validate_proposal(proposal(["A", "a"]))

    def test_complete_pair_matrix_required(self):
        children = [node(str(i), str(i)) for i in range(3)]
        result = audit(["0", "1", "2"])
        validate_audit(result, children)
        result["pairs"].pop()
        with self.assertRaises(SchemaError):
            validate_audit(result, children)

    def test_contradictory_overlap_or_keep_is_rejected(self):
        children = [node("1", "A"), node("2", "B")]
        result = audit(["1", "2"])
        result["pairs"][0]["relation"] = "OVERLAP"
        with self.assertRaises(SchemaError):
            validate_audit(result, children)
        result = audit(["1", "2"])
        result["children"][0]["fits_parent"] = False
        with self.assertRaises(SchemaError):
            validate_audit(result, children)

    def test_coverage_has_separate_strict_schema(self):
        validate_coverage(coverage())
        validate_coverage(coverage("A substantial unallocated region"))
        for bad in ({**coverage(), "has_major_gap": "false"},
                    {**coverage(), "gap_description": "Contradiction"},
                    {**coverage(), "has_major_gap": True},
                    {**coverage(), "reason": ""}):
            with self.assertRaises(SchemaError):
                validate_coverage(bad)
        with self.assertRaises(SchemaError):
            validate_audit({**audit(["1"]), "gap": None}, [node("1", "A")])

    def test_repair_keeps_accepted_nodes_and_addition_is_separate(self):
        children = [node("1", "A"), node("2", "B")]
        parent = {"id": "root", "partition_principle": "Shared structural axis"}
        result = apply_repair(repair({"2": child("B repaired")}), parent, children,
                              audit(["1", "2"], revise=["2"]), 1)
        self.assertEqual(result["children"][0], children[0])
        with self.assertRaises(SchemaError):
            apply_repair(repair({"1": child("Changed accepted")}), parent, children, audit(["1", "2"]), 1)
        with self.assertRaises(SchemaError):
            apply_repair({**repair(), "additions": [child("C")]}, parent, children, audit(["1", "2"]), 1)
        self.assertEqual(validate_addition({"child": child("C")}, children), child("C"))
        for bad in ({"children": [child("C"), child("D")]}, {"child": child("A")}, {"child": [child("C")]}):
            with self.assertRaises(SchemaError):
                validate_addition(bad, children)

    def test_bad_breadth_or_routine_leaf_cannot_keep(self):
        for ids, key in ((["1"], "comparable_breadth"), (["1.1"], "generation_ready")):
            review = audit(ids)
            review["children"][0][key] = False
            with self.assertRaises(SchemaError):
                validate_audit(review, [node(ids[0], "Routine ax+b=c")])
            review["children"][0]["action"] = "REVISE"
            self.assertFalse(passed(validate_audit(review, [node(ids[0], "Routine ax+b=c")])))

    def test_removal_and_principle_changes_checked(self):
        children = [node("1", "A"), node("2", "B")]
        parent = {"id": "root", "partition_principle": "Shared structural axis"}
        result = apply_repair(repair({"2": None}), parent, children, audit(["1", "2"], remove=["2"]), 1)
        self.assertEqual(len(result["children"]), 1)
        changed = repair()
        changed["partition_principle"] = "Other axis"
        with self.assertRaises(SchemaError):
            apply_repair(changed, parent, children, audit(["1", "2"]), 1)

    def test_global_only_cross_branch_high_confidence_pairs(self):
        leaves = [node("1.1", "A"), node("1.2", "B"), node("2.1", "C")]
        issue = {"a": "1.1", "b": "2.1", "revise_id": "2.1", "relation": "STRONG_OVERLAP", "reason": "same assignments"}
        validate_global({"issues": [issue]}, leaves)
        issue["b"] = "1.2"
        with self.assertRaises(SchemaError):
            validate_global({"issues": [issue]}, leaves)


class RetryTests(unittest.TestCase):
    def test_malformed_and_schema_failure_retry_then_resume_without_inference(self):
        with tempfile.TemporaryDirectory() as directory:
            backend = FakeBackend(["truncated", {"wrong": []}, proposal(["A", "B"])])
            client = StructuredClient(backend, directory)
            result = client.request("x", "task", validate_proposal)
            self.assertEqual(len(result["children"]), 2)
            self.assertEqual(len(set(backend.seeds)), 3)
            attempts = list((Path(directory) / "requests").glob("*/attempt_*.json"))
            self.assertEqual(len(attempts), 3)
            self.assertTrue(all("raw_completion" in json.loads(p.read_text()) for p in attempts))
            self.assertTrue(all("diagnostics" in json.loads(p.read_text()) for p in attempts))
            resumed = StructuredClient(FakeBackend([]), directory)
            self.assertEqual(resumed.request("x", "task", validate_proposal), result)
            self.assertEqual(resumed.calls, 3)

    def test_plain_analysis_valid_json_does_not_spend_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            result = proposal(["A", "B"])
            raw = "Compare mathematical objects and avoid overly narrow subcases.\n<final_json>" + json.dumps(result) + "</final_json>"
            client = StructuredClient(FakeBackend([raw]), directory)
            self.assertEqual(client.request("x", "task", validate_proposal), result)
            self.assertEqual(client.calls, 1)

    def test_retry_exhaustion_is_bounded_and_persistent(self):
        with tempfile.TemporaryDirectory() as directory:
            client = StructuredClient(FakeBackend(["bad"] * 3), directory)
            with self.assertRaises(ParseRetriesExhausted):
                client.request("x", "task", validate_proposal)
            resumed = StructuredClient(FakeBackend([]), directory)
            with self.assertRaises(ParseRetriesExhausted):
                resumed.request("x", "task", validate_proposal)
            self.assertEqual(resumed.calls, 3)

    def test_global_budget_counts_retries(self):
        with tempfile.TemporaryDirectory() as directory:
            client = StructuredClient(FakeBackend(["bad"]), directory, max_calls=1)
            with self.assertRaises(BudgetExhausted):
                client.request("x", "task", validate_proposal)
            self.assertEqual(client.calls, 1)


class RecordedOutputTests(unittest.TestCase):
    """Exact Base completions from the failed v1 root/propose, excluding run metadata."""

    def setUp(self):
        self.rows = json.loads((Path(__file__).parent / "fixtures" / "root_propose_v1.json").read_text(encoding="utf-8"))

    def test_recorded_outputs_reject_repetition_accept_tagged_and_fenced_results(self):
        self.assertEqual(self.rows[0]["finish_reason"], "length")
        with self.assertRaises(SchemaError):
            parse_response(self.rows[0]["raw_completion"])
        for row, expected_width in zip(self.rows[1:], (10, 4)):
            with self.subTest(attempt=row["attempt"]):
                result = validate_proposal(parse_response(row["raw_completion"]))
                self.assertEqual(len(result["children"]), expected_width)

    def test_recorded_retry_stops_at_second_completion_and_persists_evidence(self):
        outputs = iter(self.rows)
        backend = types.SimpleNamespace(generate=lambda *args: deepcopy(next(outputs)))
        with tempfile.TemporaryDirectory() as directory:
            client = StructuredClient(backend, directory)
            result = client.request("root/propose", "Recorded request replay", validate_proposal)
            self.assertEqual(client.calls, 2)
            self.assertEqual(len(result["children"]), 10)
            saved = [json.loads(p.read_text()) for p in sorted((Path(directory) / "requests").glob("*/attempt_*.json"))]
            self.assertEqual([r["status"] for r in saved], ["parse_error", "ok"])
            self.assertEqual([r["finish_reason"] for r in saved], ["length", "stop"])
            self.assertEqual(saved[0]["raw_completion"], self.rows[0]["raw_completion"])
            resumed = StructuredClient(FakeBackend([]), directory)
            self.assertEqual(resumed.request("root/propose", "Recorded request replay", validate_proposal), result)


class FlowTests(unittest.TestCase):
    def test_happy_path_depth_two_and_two_checks(self):
        client = ScriptedClient(clean_script())
        builder = TreeBuilder(client)
        self.assertTrue(builder.build())
        self.assertEqual(len(client.labels), 15)
        self.assertTrue(all(c["consecutive_no"] == 2 for c in builder.status["coverage"].values()))
        self.assertTrue(all(not leaf["children"] for p in builder.root["children"] for leaf in p["children"]))

    def test_one_no_cannot_freeze_when_call_budget_ends(self):
        with tempfile.TemporaryDirectory() as directory:
            backend = FakeBackend([proposal(["A"]), audit(["1"]), coverage()])
            builder = TreeBuilder(StructuredClient(backend, directory, max_calls=3))
            self.assertFalse(builder.build())
            self.assertEqual(builder.status["state"], "unresolved")
            self.assertEqual(builder.status["coverage"]["root"]["consecutive_no"], 1)
            self.assertEqual(builder.status["stop_reason"], "call_budget_exhausted")

    def test_no_yes_addition_restarts_checks_and_preserves_siblings(self):
        script = {"root/propose": proposal(["A", "B"]), "root/audit/0": audit(["1", "2"]),
                  "root/coverage/0/0": coverage(), "root/coverage/0/1": coverage("Unallocated structure"),
                  "root/addition/0": {"child": child("C")}, "root/audit/1": audit(["1", "2", "3"]),
                  **confirmations("root", 1)}
        snapshots = []
        client = ScriptedClient(script)
        builder = TreeBuilder(client, checkpoint=lambda root, status: snapshots.append(deepcopy(status)))
        self.assertTrue(builder.build_children(builder.root, 1))
        self.assertEqual([c["name"] for c in builder.root["children"]], ["A", "B", "C"])
        self.assertEqual(client.labels[-2:], ["root/coverage/1/0", "root/coverage/1/1"])
        counts = [s["coverage"].get("root", {}).get("consecutive_no") for s in snapshots]
        self.assertIn(1, counts)
        self.assertIn(0, counts[counts.index(1) + 1:])

    def test_yes_addition_then_repeated_gap_stalls(self):
        script = {"root/propose": proposal(["A"]), "root/audit/0": audit(["1"]),
                  "root/coverage/0/0": coverage("Missing structure"), "root/addition/0": {"child": child("B")},
                  "root/audit/1": audit(["1", "2"]), "root/coverage/1/0": coverage("missing  structure")}
        builder = TreeBuilder(ScriptedClient(script))
        self.assertFalse(builder.build())
        self.assertEqual(builder.status["parents"]["root"], "stalled_repeated_gap")

    def test_width_ceiling_is_not_success(self):
        for too_large in (False, True):
            script = {"root/propose": proposal(["A", "B"] if too_large else ["A"]),
                      "root/audit/0": audit(["1"]), "root/coverage/0/0": coverage("Gap")}
            builder = TreeBuilder(ScriptedClient(script), max_children_per_parent=1)
            self.assertFalse(builder.build())
            self.assertEqual(builder.status["parents"]["root"], "children_limit_exhausted")

    def test_second_repair_gets_third_audit_and_fresh_coverage(self):
        script = {"root/propose": proposal(["A", "B"]), "root/audit/0": audit(["1", "2"], revise=["2"]),
                  "root/repair/0": repair({"2": child("B revised once")}),
                  "root/audit/1": audit(["1", "2"], revise=["2"]),
                  "root/repair/1": repair({"2": child("B revised twice")}),
                  "root/audit/2": audit(["1", "2"]), **confirmations("root", 2)}
        builder = TreeBuilder(ScriptedClient(script))
        self.assertTrue(builder.build_children(builder.root, 1))

    def test_budget_exhaustion_does_not_freeze_bad_tree(self):
        script = {"root/propose": proposal(["A", "B"]), "root/audit/0": audit(["1", "2"], revise=["2"])}
        builder = TreeBuilder(ScriptedClient(script), max_repairs=0)
        self.assertFalse(builder.build())
        self.assertEqual(builder.status["parents"]["root"], "repair_budget_exhausted")

    def test_identical_repair_stops_as_stalled(self):
        script = {"root/propose": proposal(["A", "B"]), "root/audit/0": audit(["1", "2"], revise=["2"]),
                  "root/repair/0": repair({"2": child("B")})}
        builder = TreeBuilder(ScriptedClient(script))
        self.assertFalse(builder.build())
        self.assertEqual(builder.status["parents"]["root"], "stalled")

    def test_addition_cannot_force_changes_to_accepted_siblings(self):
        script = {"root/propose": proposal(["A"]), "root/audit/0": audit(["1"]),
                  "root/coverage/0/0": coverage("Gap"), "root/addition/0": {"child": child("B")},
                  "root/audit/1": audit(["1", "2"], revise=["1"])}
        builder = TreeBuilder(ScriptedClient(script))
        self.assertFalse(builder.build())
        self.assertEqual(builder.status["parents"]["root"], "protected_sibling_conflict")
        self.assertEqual(builder.root["children"][0]["name"], "A")

    def test_global_repair_followed_by_local_double_coverage_and_global_checks(self):
        script = clean_script()
        script.update({"global/audit/0": {"issues": [{"a": "1.1", "b": "2.1", "revise_id": "2.1",
                                                     "relation": "NEAR_DUPLICATE", "reason": "same structure"}]},
                       "global/repair/2": repair({"2.1": child("B new structure")}),
                       "global/verify/2/audit/0": audit(["2.1", "2.2"]), **confirmations("global/verify/2"),
                       "global/audit/1": {"issues": []}, **confirmations("global", 1)})
        client = ScriptedClient(script)
        self.assertTrue(TreeBuilder(client).build())
        self.assertEqual(client.labels[-3:], ["global/audit/1", "global/coverage/1/0", "global/coverage/1/1"])

    def test_global_repair_cannot_hide_new_local_gap(self):
        script = clean_script()
        script.update({"global/audit/0": {"issues": [{"a": "1.1", "b": "2.1", "revise_id": "2.1",
                                                     "relation": "NESTED", "reason": "nested scope"}]},
                       "global/repair/2": repair({"2.1": None}),
                       "global/verify/2/audit/0": audit(["2.2"]),
                       "global/verify/2/coverage/0/0": coverage("Removal leaves a major gap")})
        builder = TreeBuilder(ScriptedClient(script))
        self.assertFalse(builder.build())
        self.assertEqual(builder.status["global"], "unresolved")
        self.assertEqual(builder.status["parents"]["2"], "coverage_unresolved")

    def global_addition_script(self, new_branch=False):
        script = clean_script()
        script["global/coverage/0/0"] = coverage("Missing major generation region")
        target = "root" if new_branch else "2"
        ids = ["1", "2", "3"] if new_branch else ["2.1", "2.2", "2.3"]
        script.update({"global/addition": {"parent_id": target, "child": child("New region")},
                       f"global/verify/{target}/audit/0": audit(ids), **confirmations(f"global/verify/{target}"),
                       "global/audit/1": {"issues": []}, **confirmations("global", 1)})
        if new_branch:
            script.update({"3/propose": proposal(["C one", "C two"]), "3/audit/0": audit(["3.1", "3.2"]),
                           **confirmations("3")})
        return script

    def test_global_gap_addition_existing_branch_and_new_l1(self):
        for new_branch in (False, True):
            with self.subTest(new_branch=new_branch):
                client = ScriptedClient(self.global_addition_script(new_branch))
                builder = TreeBuilder(client)
                self.assertTrue(builder.build())
                self.assertTrue(all(p["children"] for p in builder.root["children"]))
                self.assertEqual(len(builder.root["children"]), 3 if new_branch else 2)
                self.assertEqual(client.labels.count("global/addition"), 1)

    def test_global_addition_cannot_repeat_sweep_or_skip_validation(self):
        for failed_local in (False, True):
            script = self.global_addition_script()
            if failed_local:
                script["global/verify/2/audit/0"] = audit(["2.1", "2.2", "2.3"], revise=["2.3"])
            else:
                script["global/coverage/1/1"] = coverage("Another global gap")
            builder = TreeBuilder(ScriptedClient(script))
            self.assertFalse(builder.build())
            self.assertEqual(builder.status["global"], "unresolved")

    def test_full_pipeline_transport_distinct_samples_and_cached_resume(self):
        with tempfile.TemporaryDirectory() as directory:
            backend = FakeBackend(list(clean_script().values()))
            self.assertTrue(TreeBuilder(StructuredClient(backend, directory)).build())
            self.assertEqual(len(backend.seeds), 15)
            self.assertEqual(len(set(backend.seeds)), 15)
            requests = [json.loads(p.read_text()) for p in (Path(directory) / "requests").glob("*/request.json")]
            a, b = [next(r for r in requests if r["label"] == f"root/coverage/0/{i}") for i in range(2)]
            self.assertEqual(a["user"], b["user"])
            self.assertTrue(TreeBuilder(StructuredClient(FakeBackend([]), directory)).build())

    def test_changed_partition_cannot_reuse_previous_coverage_confirmations(self):
        outputs = [proposal(["A"]), audit(["1"]), coverage(), coverage("Unallocated region"),
                   {"child": child("B")}, audit(["1", "2"]), coverage(), coverage()]
        with tempfile.TemporaryDirectory() as directory:
            backend = FakeBackend(outputs)
            builder = TreeBuilder(StructuredClient(backend, directory))
            self.assertTrue(builder.build_children(builder.root, 1))
            self.assertEqual(len(backend.seeds), 8)
            requests = [json.loads(p.read_text()) for p in (Path(directory) / "requests").glob("*/request.json")]
            old = next(r for r in requests if r["label"] == "root/coverage/0/0")
            new = next(r for r in requests if r["label"] == "root/coverage/1/0")
            self.assertNotEqual(old["user"], new["user"])
            resumed = TreeBuilder(StructuredClient(FakeBackend([]), directory))
            self.assertTrue(resumed.build_children(resumed.root, 1))
            self.assertEqual(resumed.root, builder.root)

    def test_new_l1_must_complete_l2_and_final_overlap_must_pass(self):
        script = self.global_addition_script(True)
        script["3/audit/0"] = audit(["3.1", "3.2"], revise=["3.1"])
        builder = TreeBuilder(ScriptedClient(script), max_repairs=0)
        self.assertFalse(builder.build())
        self.assertEqual(builder.status["parents"]["3"], "repair_budget_exhausted")
        script = self.global_addition_script()
        script["global/audit/1"] = {"issues": [{"a": "1.1", "b": "2.3", "revise_id": "2.3",
                                               "relation": "NESTED", "reason": "New leaf still overlaps"}]}
        self.assertFalse(TreeBuilder(ScriptedClient(script)).build())

    def test_added_child_can_be_repaired_without_touching_accepted_sibling(self):
        script = {"root/propose": proposal(["A"]), "root/audit/0": audit(["1"]),
                  "root/coverage/0/0": coverage("Gap"), "root/addition/0": {"child": child("B")},
                  "root/audit/1": audit(["1", "2"], revise=["2"]),
                  "root/repair/0": repair({"2": child("B repaired")}),
                  "root/audit/2": audit(["1", "2"]), **confirmations("root", 2)}
        builder = TreeBuilder(ScriptedClient(script))
        self.assertTrue(builder.build_children(builder.root, 1))
        self.assertEqual([c["name"] for c in builder.root["children"]], ["A", "B repaired"])

    def test_global_overlap_repair_and_gap_addition_share_one_verified_sweep(self):
        script = self.global_addition_script()
        script.update({"global/audit/0": {"issues": [{"a": "1.1", "b": "2.1", "revise_id": "2.1",
                                                     "relation": "NESTED", "reason": "Overlap"}]},
                       "global/repair/2": repair({"2.1": child("Revised B")})})
        client = ScriptedClient(script)
        builder = TreeBuilder(client)
        self.assertTrue(builder.build())
        self.assertEqual(client.labels.count("global/verify/2/audit/0"), 1)
        self.assertEqual(builder.root["children"][1]["children"][0]["name"], "Revised B")

    def test_shared_target_and_depth_constraints_in_prompts(self):
        self.assertIn("no target count", prompts.WIDTH)
        self.assertIn("final depth", prompts.granularity(2))
        for text in ("fewer than 30%", "including but not limited to", "external datasets", "non-trivial"):
            self.assertIn(text, prompts.SYSTEM)
        with self.assertRaises(ValueError):
            prompts.granularity(3)


class RunnerTests(unittest.TestCase):
    def runtime_modules(self):
        return {"transformers": types.SimpleNamespace(__version__="test"),
                "vllm": types.SimpleNamespace(__version__="test")}

    def test_cli_artifacts_and_completed_resume_skip_model_loading(self):
        with tempfile.TemporaryDirectory() as directory:
            model = Path(directory) / "model"
            model.mkdir()
            (model / "config.json").write_text('{}')
            output = Path(directory) / "output"
            args = ["--model", str(model), "--output-dir", str(output)]
            backend = FakeBackend(list(clean_script().values()))
            with patch.object(runner, "VLLMBackend", return_value=backend), patch.dict("sys.modules", self.runtime_modules()):
                self.assertEqual(runner.main(args), 0)
            self.assertTrue((output / "tree.json").is_file())
            self.assertTrue((output / "tree.md").is_file())
            self.assertEqual(json.loads((output / "manifest.json").read_text())["state"], "accepted")
            with patch.object(runner, "VLLMBackend", side_effect=AssertionError("should reuse accepted tree")):
                self.assertEqual(runner.main(args + ["--resume"]), 0)
            with self.assertRaisesRegex(ValueError, "fingerprint differs"):
                runner.main(args + ["--resume", "--seed", "9"])

    def test_cli_unresolved_does_not_publish_tree_json(self):
        with tempfile.TemporaryDirectory() as directory:
            model = Path(directory) / "model"
            model.mkdir()
            output = Path(directory) / "output"
            backend = FakeBackend([proposal(["A", "B"]), audit(["1", "2"], revise=["2"])])
            with patch.object(runner, "VLLMBackend", return_value=backend), patch.dict("sys.modules", self.runtime_modules()):
                code = runner.main(["--model", str(model), "--output-dir", str(output), "--max-repairs", "0"])
            self.assertEqual(code, 2)
            self.assertFalse((output / "tree.json").exists())
            self.assertTrue((output / "partial_tree.json").exists())
            self.assertEqual(json.loads((output / "manifest.json").read_text())["state"], "unresolved")

    def test_cli_parse_failure_retains_raw_and_failed_status(self):
        with tempfile.TemporaryDirectory() as directory:
            model = Path(directory) / "model"
            model.mkdir()
            output = Path(directory) / "output"
            with patch.object(runner, "VLLMBackend", return_value=FakeBackend(["bad"] * 3)), patch.dict("sys.modules", self.runtime_modules()):
                with self.assertRaises(ParseRetriesExhausted):
                    runner.main(["--model", str(model), "--output-dir", str(output)])
            self.assertFalse((output / "tree.json").exists())
            manifest = json.loads((output / "manifest.json").read_text())
            self.assertEqual(manifest["state"], "failed")
            self.assertEqual(manifest["calls_used"], 3)
            self.assertEqual(len(list((output / "requests").glob("*/attempt_*.json"))), 3)

    def test_cli_call_budget_is_unresolved_and_resume_does_not_reset_it(self):
        with tempfile.TemporaryDirectory() as directory:
            model = Path(directory) / "model"
            model.mkdir()
            output = Path(directory) / "output"
            args = ["--model", str(model), "--output-dir", str(output), "--max-calls", "3"]
            backend = FakeBackend([proposal(["A"]), audit(["1"]), coverage()])
            with patch.object(runner, "VLLMBackend", return_value=backend), patch.dict("sys.modules", self.runtime_modules()):
                self.assertEqual(runner.main(args), 2)
                self.assertEqual(runner.main(args + ["--resume"]), 2)
            self.assertFalse((output / "tree.json").exists())
            manifest = json.loads((output / "manifest.json").read_text())
            self.assertEqual(manifest["stop_reason"], "call_budget_exhausted")
            self.assertEqual(manifest["calls_used"], 3)
            self.assertEqual(manifest["config"]["max_children_per_parent"], 16)
            self.assertEqual(manifest["config"]["max_new_tokens"], 8192)
            with self.assertRaisesRegex(ValueError, "fingerprint differs"):
                runner.main(args + ["--resume", "--max-children-per-parent", "12"])


if __name__ == "__main__":
    unittest.main()
