from __future__ import annotations

import ast
import unittest
from pathlib import Path


REWARD_PATH = Path(__file__).resolve().parents[1] / "reward.py"


class RequestSemanticsTests(unittest.TestCase):
    def test_solver_population_request_has_no_deadline_or_retry_interface(self):
        tree = ast.parse(REWARD_PATH.read_text(encoding="utf-8"))
        functions = {
            node.name: node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
        }

        compute_args = {argument.arg for argument in functions["compute_score"].args.args}
        compute_args.update(
            argument.arg for argument in functions["compute_score"].args.kwonlyargs
        )
        self.assertNotIn("request_timeout", compute_args)
        self.assertNotIn("retries", compute_args)

        request_calls = [
            node
            for node in ast.walk(functions["_request_one"])
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "requests"
            and node.func.attr == "get"
        ]
        self.assertEqual(len(request_calls), 1)
        self.assertNotIn("timeout", {keyword.arg for keyword in request_calls[0].keywords})


if __name__ == "__main__":
    unittest.main()
