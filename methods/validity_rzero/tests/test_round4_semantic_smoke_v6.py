import argparse
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from methods.validity_rzero.semantic_judge_offline import run_round4_semantic_smoke
from methods.validity_rzero.semantic_judge_offline import run_round4_semantic_smoke_v6
from methods.validity_rzero.semantic_judge_offline.run_pair_judge_v6_pattern_reasoning import (
    PROMPT_TEMPLATE as V6_PROMPT_TEMPLATE,
    PROMPT_VERSION as V6_PROMPT_VERSION,
    build_prompt as build_v6_prompt,
)
from methods.validity_rzero.semantic_mc import (
    UniquePairTask, build_pair_plan, cache_context,
)
from methods.validity_rzero.semantic_mc_gpu import (
    aggregate_prefix_cache_metrics, shard_tasks_by_candidate,
)
from methods.validity_rzero.semantic_mc_worker import (
    generate_with_deferred_retry, prefix_cache_observation,
)


class Round4SemanticSmokeV6Tests(unittest.TestCase):
    def test_v6_pair_plan_changes_only_prompt_protocol_and_cache_namespace(self):
        questions = {
            0: "recurrence question",
            1: "modular question",
            2: "unique question",
        }
        candidates, panel = [0, 1, 2], [0, 1]
        old_context = cache_context("/frozen/base", 1024, 42)
        v6_context = cache_context(
            "/frozen/base",
            1024,
            42,
            prompt_version=V6_PROMPT_VERSION,
            prompt_template=V6_PROMPT_TEMPLATE,
            orientation="candidate_then_reference_v1",
        )
        old_instances, old_tasks = build_pair_plan(
            questions, candidates, panel, old_context
        )
        v6_instances, v6_tasks = build_pair_plan(
            questions,
            candidates,
            panel,
            v6_context,
            prompt_builder=build_v6_prompt,
        )

        self.assertEqual(
            [(item.candidate_index, item.panel_index) for item in old_instances],
            [(item.candidate_index, item.panel_index) for item in v6_instances],
        )
        self.assertEqual(len(old_instances), 4)
        self.assertEqual(len(v6_instances), 4)
        self.assertEqual(old_context["model_identity"], v6_context["model_identity"])
        self.assertEqual(old_context["sampling"], v6_context["sampling"])
        self.assertEqual(old_context["orientation"], "lexicographic_question_text_v1")
        self.assertEqual(v6_context["orientation"], "candidate_then_reference_v1")
        self.assertTrue(set(old_tasks).isdisjoint(v6_tasks))
        self.assertTrue(all(task.prompt.endswith("Analysis:") for task in v6_tasks.values()))
        self.assertTrue(all(
            task.prompt == build_v6_prompt(task.question_a, task.question_b)
            for task in v6_tasks.values()
        ))
        for instance in v6_instances:
            task = v6_tasks[instance.cache_key]
            self.assertEqual(task.question_a, questions[instance.candidate_index])
            self.assertEqual(task.question_b, questions[instance.panel_index])

    def test_v6_entrypoint_injects_only_the_versioned_prompt_protocol(self):
        sentinel_args = object()
        with (
            patch.object(
                run_round4_semantic_smoke_v6,
                "arguments",
                return_value=sentinel_args,
            ),
            patch.object(run_round4_semantic_smoke_v6, "run_smoke") as run_smoke,
        ):
            run_round4_semantic_smoke_v6.main()

        positional, keywords = run_smoke.call_args
        self.assertEqual(positional, (sentinel_args,))
        self.assertEqual(keywords["prompt_version"], V6_PROMPT_VERSION)
        self.assertEqual(keywords["prompt_template"], V6_PROMPT_TEMPLATE)
        self.assertIs(keywords["prompt_builder"], build_v6_prompt)
        self.assertEqual(
            keywords["artifact_stem"], "semantic_smoke_v6_pattern_reasoning"
        )
        self.assertEqual(
            keywords["controlled_baseline"],
            "round4_semantic_mc_smoke_2048x128_v1",
        )
        self.assertEqual(
            keywords["only_intended_variable"],
            "V6 brief-reasoning judge with canonical candidate-then-reference presentation",
        )
        self.assertEqual(
            keywords["pair_orientation"], "candidate_then_reference_v1"
        )
        self.assertEqual(
            keywords["inference_order"], "candidate_grouped_panel_order_v1"
        )

    def test_candidate_groups_stay_contiguous_and_on_one_worker(self):
        tasks = [
            UniquePairTask(str(index), "q", "r", f"p{index}", candidate, index)
            for index, candidate in enumerate([10, 10, 10, 20, 20, 30])
        ]
        shards = shard_tasks_by_candidate(tasks, 2)
        self.assertEqual(
            [[task.candidate_index for task in shard] for shard in shards],
            [[10, 10, 10, 30], [20, 20]],
        )

    def test_request_level_cached_tokens_are_aggregated(self):
        observation = prefix_cache_observation([
            SimpleNamespace(prompt_token_ids=list(range(100)), num_cached_tokens=80),
            SimpleNamespace(prompt_token_ids=list(range(60)), num_cached_tokens=48),
            SimpleNamespace(prompt_token_ids=list(range(40)), num_cached_tokens=None),
        ])
        self.assertEqual(observation, {
            "observed_request_count": 2,
            "observed_prompt_tokens": 160,
            "hit_tokens": 128,
        })
        aggregate = aggregate_prefix_cache_metrics([{
            "generated_request_count": 3,
            "prefix_cache_observed_request_count": 2,
            "prefix_cache_observed_prompt_tokens": 160,
            "prefix_cache_hit_tokens": 128,
        }])
        self.assertEqual(aggregate["token_hit_rate"], 0.8)
        self.assertFalse(aggregate["metrics_available_for_all_generated_requests"])

    def test_failures_are_retried_only_after_all_first_pass_batches(self):
        tasks = [
            {"cache_key": f"k{index}", "prompt": f"p{index}"}
            for index in range(10)
        ]
        calls = []
        seen = {}

        def generate(prompts):
            calls.append(list(prompts))
            responses = []
            for prompt in prompts:
                seen[prompt] = seen.get(prompt, 0) + 1
                responses.append(
                    "bad"
                    if prompt in {"p1", "p5", "p9"} and seen[prompt] == 1
                    else r"\boxed{DIFFERENT}"
                )
            return responses

        def parse(response):
            return {
                "parsed_label": "DIFFERENT" if "DIFFERENT" in response else None
            }

        results, metrics = generate_with_deferred_retry(
            tasks, generate, parse, batch_size=4
        )
        self.assertEqual(calls, [
            ["p0", "p1", "p2", "p3"],
            ["p4", "p5", "p6", "p7"],
            ["p8", "p9"],
            ["p1", "p5", "p9"],
        ])
        self.assertEqual(metrics, {
            "first_pass_batch_count": 3,
            "first_pass_failure_count": 3,
            "retry_batch_count": 1,
            "retried_request_count": 3,
        })
        self.assertTrue(all(item["parsed_label"] == "DIFFERENT" for item in results.values()))
        self.assertEqual([results[f"k{index}"]["attempts"] for index in (1, 5, 9)], [2, 2, 2])

    def test_cpu_fixture_writes_versioned_v6_manifest_and_fixed_pair_plan(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            input_path = root / "round4.jsonl"
            input_path.write_text(
                "".join(
                    json.dumps({"question": f"question {index}"}) + "\n"
                    for index in range(3)
                ),
                encoding="utf-8",
            )
            output_dir = root / "output"
            args = argparse.Namespace(
                input=input_path,
                output_dir=output_dir,
                model="Qwen/Qwen3-4B-Base",
                expected_count=3,
                candidate_count=3,
                panel_count=2,
                candidate_seed=42,
                panel_seed=43,
                sampling_seed=42,
                max_tokens=1024,
                gpu_ids="2,3",
                gpu_memory_utilization=0.85,
                worker_batch_size=8192,
                local_files_only=True,
                overwrite=False,
            )
            captured_prompts = []

            def fake_gpu(tasks, *_args, **_kwargs):
                captured_prompts.extend(task.prompt for task in tasks)
                return (
                    {
                        task.cache_key: {
                            "parsed_label": "DIFFERENT",
                            "attempts": 1,
                        }
                        for task in tasks
                    },
                    {"wall_seconds": 1.0, "workers": []},
                )

            with (
                patch.object(
                    run_round4_semantic_smoke,
                    "load_generation_config",
                    return_value=(
                        {"temperature": 0.6},
                        "/frozen/generation_config.json",
                        "/frozen/base",
                        "revision",
                    ),
                ),
                patch.object(run_round4_semantic_smoke, "run_gpu_tasks", side_effect=fake_gpu),
                patch.object(run_round4_semantic_smoke, "git_head", return_value="test-head"),
            ):
                run_round4_semantic_smoke.run_smoke(
                    args,
                    prompt_version=V6_PROMPT_VERSION,
                    prompt_template=V6_PROMPT_TEMPLATE,
                    prompt_builder=build_v6_prompt,
                    artifact_stem="semantic_smoke_v6_pattern_reasoning",
                    experiment="round4_semantic_mc_smoke_2048x128_v6_pattern_reasoning",
                    controlled_baseline="round4_semantic_mc_smoke_2048x128_v1",
                    only_intended_variable=(
                        "V6 brief-reasoning judge with canonical "
                        "candidate-then-reference presentation"
                    ),
                    pair_orientation="candidate_then_reference_v1",
                    inference_order="candidate_grouped_panel_order_v1",
                )

            manifest_path = (
                output_dir / "semantic_smoke_v6_pattern_reasoning_manifest.json"
            )
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["prompt_version"], V6_PROMPT_VERSION)
            self.assertEqual(manifest["prompt_template"], V6_PROMPT_TEMPLATE)
            self.assertEqual(manifest["feasibility"]["total_pair_instances"], 4)
            self.assertEqual(
                manifest["pair_protocol"]["orientation"],
                "candidate_then_reference_v1",
            )
            self.assertEqual(
                manifest["pair_protocol"]["inference_order"],
                "candidate_grouped_panel_order_v1",
            )
            self.assertTrue(
                manifest["feasibility"]["prefix_cache"]["enabled_explicitly"]
            )
            self.assertEqual(
                manifest["generation_execution"]["worker_submission_batch_size"],
                8192,
            )
            self.assertEqual(
                manifest["generation_execution"]["retry_policy"],
                "deferred_once_after_all_first_pass_batches",
            )
            self.assertEqual(len(manifest["sampled_row_indices"]), 3)
            self.assertEqual(len(manifest["panel_row_indices"]), 2)
            self.assertTrue(captured_prompts)
            self.assertTrue(all(prompt.endswith("Analysis:") for prompt in captured_prompts))
            per_question = output_dir / (
                "semantic_smoke_v6_pattern_reasoning_per_question.jsonl"
            )
            self.assertEqual(len(per_question.read_text(encoding="utf-8").splitlines()), 3)


if __name__ == "__main__":
    unittest.main()
