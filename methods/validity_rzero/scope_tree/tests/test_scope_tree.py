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
    validate_audit, validate_global, validate_proposal,
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


def audit(ids, revise=(), remove=(), gap=None):
    return {"principle_ok": True, "principle_feedback": "Consistent axis", "gap": gap,
            "children": [{"id": i, "fits_parent": True, "follows_principle": True,
                          "granularity_ok": i not in revise,
                          "action": "REMOVE" if i in remove else "REVISE" if i in revise else "KEEP",
                          "reason": "Review finding"} for i in ids],
            "pairs": [{"a": a, "b": b, "relation": "DISTINCT", "reason": "Different scope"}
                      for a, b in itertools.combinations(ids, 2)]}


def repair(replacements=None, additions=None):
    return {"partition_principle": "Shared structural axis",
            "replacements": [{"id": key, "child": value} for key, value in (replacements or {}).items()],
            "additions": additions or []}


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


def clean_script():
    return {
        "root/propose": proposal(["Broad A", "Broad B"]),
        "root/audit/0": audit(["1", "2"]),
        "1/propose": proposal(["A one", "A two"]),
        "1/audit/0": audit(["1.1", "1.2"]),
        "2/propose": proposal(["B one", "B two"]),
        "2/audit/0": audit(["2.1", "2.2"]),
        "global/audit/0": {"issues": []},
    }


class SchemaTests(unittest.TestCase):
    def test_analysis_required_and_strict_box(self):
        self.assertEqual(parse_response(wrapped({"a": {"b": 1}})), {"a": {"b": 1}})
        invalid = [
            '<final_json>{}</final_json>',
            '<analysis></analysis><final_json>{}</final_json>',
            wrapped({}) + "trailing",
            wrapped({}) + wrapped({}),
            '<analysis>x</analysis><final_json>{"a":1,"a":2}</final_json>',
            '<analysis>x</analysis><final_json>{"a":NaN}</final_json>',
            '<analysis>x</analysis><final_json>{',
        ]
        for raw in invalid:
            with self.subTest(raw=raw), self.assertRaises(SchemaError):
                parse_response(raw)

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

    def test_gap_prevents_acceptance_even_when_all_children_keep(self):
        self.assertFalse(passed(audit(["1", "2"], gap="A substantially different representation is missing")))

    def test_repair_keeps_accepted_nodes_and_can_fill_gap(self):
        children = [node("1", "A"), node("2", "B")]
        parent = {"id": "root", "partition_principle": "Shared structural axis"}
        result = apply_repair(repair({"2": child("B repaired")}, [child("C")]), parent, children,
                              audit(["1", "2"], revise=["2"], gap="Uncovered region"), 1)
        self.assertEqual(result["children"][0], children[0])
        self.assertEqual([n["id"] for n in result["children"]], ["1", "2", "3"])
        with self.assertRaises(SchemaError):
            apply_repair(repair({"1": child("Changed accepted")}), parent, children, audit(["1", "2"]), 1)
        with self.assertRaises(SchemaError):
            apply_repair(repair(additions=[child("C")]), parent, children, audit(["1", "2"]), 1)

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
            resumed = StructuredClient(FakeBackend([]), directory)
            self.assertEqual(resumed.request("x", "task", validate_proposal), result)
            self.assertEqual(resumed.calls, 3)

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


class FlowTests(unittest.TestCase):
    def test_happy_path_depth_two_only(self):
        client = ScriptedClient(clean_script())
        builder = TreeBuilder(client)
        self.assertTrue(builder.build())
        self.assertEqual(len(client.labels), 7)
        self.assertEqual(builder.status["state"], "accepted")
        self.assertTrue(all(not leaf["children"] for p in builder.root["children"] for leaf in p["children"]))

    def test_second_repair_gets_a_third_audit(self):
        script = clean_script()
        script.update({"root/audit/0": audit(["1", "2"], revise=["2"]),
                       "root/repair/0": repair({"2": child("B revised once")}),
                       "root/audit/1": audit(["1", "2"], revise=["2"]),
                       "root/repair/1": repair({"2": child("B revised twice")}),
                       "root/audit/2": audit(["1", "2"])})
        client = ScriptedClient(script)
        self.assertTrue(TreeBuilder(client).build())
        self.assertIn("root/audit/2", client.labels)

    def test_budget_exhaustion_does_not_freeze_bad_tree(self):
        script = {"root/propose": proposal(["A", "B"]), "root/audit/0": audit(["1", "2"], revise=["2"])}
        builder = TreeBuilder(ScriptedClient(script), max_repairs=0)
        self.assertFalse(builder.build())
        self.assertEqual(builder.status["parents"]["root"], "repair_budget_exhausted")

    def test_identical_repair_stops_as_stalled(self):
        script = {"root/propose": proposal(["A", "B"]),
                  "root/audit/0": audit(["1", "2"], revise=["2"]),
                  "root/repair/0": repair({"2": child("B")})}
        builder = TreeBuilder(ScriptedClient(script))
        self.assertFalse(builder.build())
        self.assertEqual(builder.status["parents"]["root"], "stalled")

    def test_global_repair_is_followed_by_local_and_global_reaudit(self):
        script = clean_script()
        script.update({"global/audit/0": {"issues": [{"a": "1.1", "b": "2.1", "revise_id": "2.1",
                                                     "relation": "NEAR_DUPLICATE", "reason": "same structure"}]},
                       "global/repair/2": repair({"2.1": child("B new structure")}),
                       "global/local_reaudit/2": audit(["2.1", "2.2"]),
                       "global/audit/1": {"issues": []}})
        client = ScriptedClient(script)
        self.assertTrue(TreeBuilder(client).build())
        self.assertEqual(client.labels[-2:], ["global/local_reaudit/2", "global/audit/1"])

    def test_global_repair_cannot_hide_new_local_gap(self):
        script = clean_script()
        script.update({"global/audit/0": {"issues": [{"a": "1.1", "b": "2.1", "revise_id": "2.1",
                                                     "relation": "NESTED", "reason": "nested scope"}]},
                       "global/repair/2": repair({"2.1": None}),
                       "global/local_reaudit/2": audit(["2.2"], gap="Removal leaves a major structural gap"),
                       "global/audit/1": {"issues": []}})
        builder = TreeBuilder(ScriptedClient(script))
        self.assertFalse(builder.build())
        self.assertEqual(builder.status["global"], "unresolved")

    def test_full_pipeline_with_structured_transport_and_cached_resume(self):
        script = clean_script()
        with tempfile.TemporaryDirectory() as directory:
            backend = FakeBackend(list(script.values()))
            self.assertTrue(TreeBuilder(StructuredClient(backend, directory)).build())
            self.assertEqual(len(backend.seeds), 7)
            self.assertTrue(TreeBuilder(StructuredClient(FakeBackend([]), directory)).build())

    def test_prompts_have_no_fixed_taxonomy_or_width_quota(self):
        self.assertIn("no target count", prompts.WIDTH)
        self.assertIn("final depth", prompts.granularity(2))
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


if __name__ == "__main__":
    unittest.main()
