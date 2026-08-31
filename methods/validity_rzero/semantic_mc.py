"""Pure-CPU planning and aggregation for shared-panel semantic MC rewards."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import random
from typing import Any, Callable, Iterable, Mapping

from .semantic_judge_offline.run_pair_judge_v2 import PROMPT_TEMPLATE, build_prompt
from .semantic_judge_offline.run_pair_judge_v3_vllm import PROMPT_VERSION, sampling_options


SEMANTIC_LABELS = {"SAME_TYPE", "DIFFERENT"}


@dataclass(frozen=True)
class PairInstance:
    candidate_index: int
    panel_index: int
    cache_key: str


@dataclass(frozen=True)
class UniquePairTask:
    cache_key: str
    question_a: str
    question_b: str
    prompt: str
    candidate_index: int | None = None
    panel_index: int | None = None


def uniform_sample_indices(population_size: int, sample_size: int, seed: int) -> list[int]:
    if population_size < 0 or sample_size < 0:
        raise ValueError("population_size and sample_size must be nonnegative")
    if sample_size > population_size:
        raise ValueError(f"cannot sample {sample_size} from {population_size}")
    return random.Random(seed).sample(range(population_size), sample_size)


def sample_candidate_and_panel_indices(
    population_size: int,
    candidate_count: int,
    panel_count: int,
    candidate_seed: int,
    panel_seed: int,
) -> tuple[list[int], list[int]]:
    candidates = uniform_sample_indices(population_size, candidate_count, candidate_seed)
    if panel_count > len(candidates):
        raise ValueError("panel_count cannot exceed candidate_count")
    panel = random.Random(panel_seed).sample(candidates, panel_count)
    return candidates, panel


def cache_context(
    model_identity: str,
    max_tokens: int = 1024,
    seed: int = 42,
    *,
    prompt_version: str = PROMPT_VERSION,
    prompt_template: str = PROMPT_TEMPLATE,
    orientation: str = "lexicographic_question_text_v1",
) -> dict[str, Any]:
    if orientation not in {
        "lexicographic_question_text_v1",
        "candidate_then_reference_v1",
    }:
        raise ValueError(f"unsupported semantic pair orientation: {orientation}")
    return {
        "model_identity": model_identity,
        "prompt_version": prompt_version,
        "prompt_template": prompt_template,
        "sampling": sampling_options(max_tokens, seed),
        "orientation": orientation,
    }


def _stable_orientation(question_left: str, question_right: str) -> tuple[str, str]:
    return (
        (question_left, question_right)
        if question_left <= question_right
        else (question_right, question_left)
    )


def _cache_key(context_digest: str, question_a: str, question_b: str) -> str:
    payload = json.dumps(
        {"context": context_digest, "question_a": question_a, "question_b": question_b},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_pair_plan(
    questions: Mapping[int, str],
    candidate_indices: Iterable[int],
    panel_indices: Iterable[int],
    context: Mapping[str, Any],
    *,
    prompt_builder: Callable[[str, str], str] = build_prompt,
) -> tuple[list[PairInstance], dict[str, UniquePairTask]]:
    candidate_indices = list(candidate_indices)
    panel_indices = list(panel_indices)
    context_digest = hashlib.sha256(
        json.dumps(context, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    instances: list[PairInstance] = []
    tasks: dict[str, UniquePairTask] = {}
    for candidate_index in candidate_indices:
        candidate_question = questions[candidate_index]
        for panel_index in panel_indices:
            if candidate_index == panel_index:
                continue
            panel_question = questions[panel_index]
            if context["orientation"] == "candidate_then_reference_v1":
                question_a, question_b = candidate_question, panel_question
            else:
                question_a, question_b = _stable_orientation(
                    candidate_question, panel_question
                )
            key = _cache_key(context_digest, question_a, question_b)
            instances.append(PairInstance(candidate_index, panel_index, key))
            tasks.setdefault(
                key,
                UniquePairTask(
                    key,
                    question_a,
                    question_b,
                    prompt_builder(question_a, question_b),
                    candidate_index,
                    panel_index,
                ),
            )
    return instances, tasks


def aggregate_semantic_penalties(
    candidate_indices: Iterable[int],
    instances: Iterable[PairInstance],
    judgments: Mapping[str, Mapping[str, Any]],
    warn: Callable[[str], None] = print,
) -> dict[int, dict[str, int | float]]:
    aggregates = {
        index: {"same_count": 0, "compared_count": 0, "parse_failure_count": 0}
        for index in candidate_indices
    }
    for instance in instances:
        label = judgments.get(instance.cache_key, {}).get("parsed_label")
        item = aggregates[instance.candidate_index]
        if label not in SEMANTIC_LABELS:
            item["parse_failure_count"] += 1
            continue
        item["compared_count"] += 1
        item["same_count"] += int(label == "SAME_TYPE")
    for index, item in aggregates.items():
        compared = int(item["compared_count"])
        item["semantic_penalty"] = int(item["same_count"]) / compared if compared else 0.0
        if compared == 0:
            warn(
                "[validity_rzero][semantic_mc][WARNING] "
                f"row_index={index} has zero successfully parsed nonself comparisons; penalty=0"
            )
    return aggregates
