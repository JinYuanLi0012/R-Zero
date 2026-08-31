import unittest
from unittest.mock import patch

from methods.validity_rzero.semantic_judge_offline import run_round4_semantic_smoke_v7
from methods.validity_rzero.semantic_judge_offline.run_pair_judge_v3_vllm import (
    STOP_STRINGS,
    sampling_options,
)
from methods.validity_rzero.semantic_judge_offline.run_pair_judge_v6_pattern_reasoning import (
    PROMPT_TEMPLATE as V6_PROMPT_TEMPLATE,
)
from methods.validity_rzero.semantic_judge_offline.semantic_pair_prompt_v7_guardrail import (
    PROMPT_TEMPLATE as V7_PROMPT_TEMPLATE,
    PROMPT_VERSION as V7_PROMPT_VERSION,
    build_prompt as build_v7_prompt,
)
from methods.validity_rzero.semantic_mc import build_pair_plan, cache_context


GUARDRAIL = (
    "Do not reduce the two problems to a generic task shell.\n"
    "The distinctive mathematical construction in the setup must also feel like\n"
    "the same recurring exercise pattern.\n\n"
    "If the similarity you identified would apply equally well to many unrelated\n"
    "math problems, choose DIFFERENT.\n\n"
)


class Round4SemanticSmokeV7Tests(unittest.TestCase):
    def test_v7_is_exactly_v6_plus_the_specificity_guardrail(self):
        insertion_point = (
            "If they feel like genuinely different kinds of exercises, "
            "choose DIFFERENT.\n\n"
        )
        self.assertNotIn(GUARDRAIL, V6_PROMPT_TEMPLATE)
        self.assertEqual(
            V7_PROMPT_TEMPLATE,
            V6_PROMPT_TEMPLATE.replace(
                insertion_point,
                GUARDRAIL + insertion_point,
                1,
            ),
        )
        self.assertTrue(V7_PROMPT_TEMPLATE.endswith("Analysis:"))

    def test_v7_preserves_pairs_orientation_and_sampling(self):
        questions = {0: "candidate zero", 1: "reference one", 2: "candidate two"}
        candidates, panel = [0, 1, 2], [0, 1]
        v6_context = cache_context(
            "/frozen/base",
            1024,
            42,
            prompt_version="semantic-pair-v6-exercise-pattern-brief-reasoning",
            prompt_template=V6_PROMPT_TEMPLATE,
            orientation="candidate_then_reference_v1",
        )
        v7_context = cache_context(
            "/frozen/base",
            1024,
            42,
            prompt_version=V7_PROMPT_VERSION,
            prompt_template=V7_PROMPT_TEMPLATE,
            orientation="candidate_then_reference_v1",
        )
        v6_instances, _ = build_pair_plan(questions, candidates, panel, v6_context)
        v7_instances, v7_tasks = build_pair_plan(
            questions,
            candidates,
            panel,
            v7_context,
            prompt_builder=build_v7_prompt,
        )

        self.assertEqual(v6_context["model_identity"], v7_context["model_identity"])
        self.assertEqual(v6_context["sampling"], v7_context["sampling"])
        self.assertEqual(v7_context["sampling"], sampling_options(1024, 42))
        self.assertEqual(v7_context["sampling"]["stop"], list(STOP_STRINGS))
        self.assertTrue(v7_context["sampling"]["include_stop_str_in_output"])
        self.assertEqual(
            [(item.candidate_index, item.panel_index) for item in v6_instances],
            [(item.candidate_index, item.panel_index) for item in v7_instances],
        )
        for instance in v7_instances:
            task = v7_tasks[instance.cache_key]
            self.assertEqual(task.question_a, questions[instance.candidate_index])
            self.assertEqual(task.question_b, questions[instance.panel_index])

    def test_v7_entrypoint_versions_outputs_and_keeps_v6_execution_protocol(self):
        sentinel_args = object()
        with (
            patch.object(run_round4_semantic_smoke_v7, "arguments", return_value=sentinel_args),
            patch.object(run_round4_semantic_smoke_v7, "run_smoke") as run_smoke,
        ):
            run_round4_semantic_smoke_v7.main()

        positional, keywords = run_smoke.call_args
        self.assertEqual(positional, (sentinel_args,))
        self.assertEqual(keywords["prompt_version"], V7_PROMPT_VERSION)
        self.assertEqual(keywords["prompt_template"], V7_PROMPT_TEMPLATE)
        self.assertIs(keywords["prompt_builder"], build_v7_prompt)
        self.assertEqual(keywords["artifact_stem"], "semantic_smoke_v7_pattern_guardrail")
        self.assertEqual(
            keywords["controlled_baseline"],
            "round4_semantic_mc_smoke_2048x128_v6_pattern_reasoning",
        )
        self.assertEqual(keywords["pair_orientation"], "candidate_then_reference_v1")
        self.assertEqual(keywords["inference_order"], "candidate_grouped_panel_order_v1")


if __name__ == "__main__":
    unittest.main()
