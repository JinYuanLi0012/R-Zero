import unittest
from unittest.mock import MagicMock, patch
from types import SimpleNamespace

from qwen35.rzero.diagnostics.base_questioner import (
    THINKING_OFF_GENERATION_SUFFIX,
    build_record,
    summarize,
    validate_rendered_prompt,
)
from qwen35.rzero.diagnostics.base_questioner_no_meta import (
    QUESTIONER_NO_EXPLICIT_META_THINKING_MESSAGES,
)
from qwen35.rzero.prompts import QUESTIONER_MESSAGES


class BaseQuestionerDiagnosticTests(unittest.TestCase):
    def output(self, text, tokens=4, finish_reason="stop", stop_reason=None):
        return SimpleNamespace(
            text=text,
            token_ids=list(range(tokens)),
            finish_reason=finish_reason,
            stop_reason=stop_reason,
        )

    def test_records_preserve_raw_output_and_detect_literal_placeholders(self):
        text = "<think>meta</think><question>{The full problem statement on one or more lines}</question>\\boxed{final_answer}"
        record = build_record(0, self.output(text), 4096)
        self.assertEqual(record["raw_response"], text)
        self.assertTrue(record["parse_success"])
        self.assertTrue(record["valid_formatted_completion"])
        self.assertTrue(record["literal_final_answer"])
        self.assertTrue(record["placeholder_question"])
        self.assertIsNone(record["manual_classification"])

    def test_summary_keeps_heuristics_distinct_from_manual_review(self):
        placeholder = build_record(
            0,
            self.output("<question>Full problem statement</question>\\boxed{final_answer}"),
            4096,
        )
        real = build_record(
            1,
            self.output("<think>x</think><question>What is 17 times 23?</question>\\boxed{391}"),
            4096,
        )
        length = build_record(2, self.output("We need to design a problem", 4096, "length"), 4096)
        summary = summarize([placeholder, real, length], {"model_revision": "1001bb4"})
        self.assertEqual(summary["total"], 3)
        self.assertEqual(summary["literal_final_answer"], 1)
        self.assertEqual(summary["placeholder_question"], 1)
        self.assertEqual(summary["hit_4096"], 1)
        self.assertEqual(summary["heuristic_real_question"], 1)
        self.assertTrue(summary["manual_review"]["required"])
        self.assertEqual(summary["manual_review"]["unclassified_indices"], [0, 1, 2])

    def test_no_meta_variant_changes_only_the_explicit_design_thinking_instruction(self):
        released = QUESTIONER_MESSAGES[0]["content"]
        variant = QUESTIONER_NO_EXPLICIT_META_THINKING_MESSAGES[0]["content"]
        self.assertIn("private scratch-pad", released)
        self.assertIn("think step-by-step to design", released)
        self.assertNotIn("private scratch-pad", variant)
        self.assertNotIn("think step-by-step to design", variant)
        self.assertIn("Design a brand-new, non-trivial problem.", variant)
        self.assertIn("<question>\n{The full problem statement on one or more lines}\n</question>", variant)
        self.assertIn("\\boxed{final_answer}", variant)
        self.assertEqual(
            QUESTIONER_NO_EXPLICIT_META_THINKING_MESSAGES[1],
            QUESTIONER_MESSAGES[1],
        )

    def test_thinking_off_variant_uses_released_prompt_and_only_overrides_template(self):
        from qwen35.rzero.diagnostics import base_questioner_thinking_off

        with (
            patch.object(base_questioner_thinking_off, "build_parser") as build_parser,
            patch.object(base_questioner_thinking_off, "run_diagnostic") as run_diagnostic,
        ):
            build_parser.return_value.parse_args.return_value = MagicMock()
            base_questioner_thinking_off.main()

        build_parser.assert_called_once_with(default_samples=32)
        call = run_diagnostic.call_args
        self.assertIs(call.args[1], QUESTIONER_MESSAGES)
        self.assertEqual(call.args[2], "qwen35_base_questioner_thinking_off_raw_32.json")
        self.assertEqual(call.args[3], "qwen35_base_questioner_thinking_off_summary.json")
        self.assertEqual(call.args[4], "released_rzero_thinking_off")
        self.assertIs(call.kwargs["enable_thinking"], False)

    def test_thinking_off_requires_the_official_empty_thinking_prefix(self):
        validate_rendered_prompt("prefix" + THINKING_OFF_GENERATION_SUFFIX, False)
        validate_rendered_prompt("<|im_start|>assistant\n", None)
        with self.assertRaisesRegex(RuntimeError, "mislabeled diagnostic"):
            validate_rendered_prompt("<|im_start|>assistant\n", False)

    def test_thinking_off_counts_prefilled_closure_and_response_only_format(self):
        text = "<question>What is 17 times 23?</question>\\boxed{391}"
        record = build_record(
            0,
            self.output(text),
            4096,
            thinking_prefilled_closed=True,
        )
        self.assertTrue(record["closed_think"])
        self.assertFalse(record["generated_closed_think"])
        self.assertTrue(record["thinking_prefilled_closed"])
        self.assertTrue(record["valid_formatted_completion"])


if __name__ == "__main__":
    unittest.main()
