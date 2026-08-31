#!/usr/bin/env python3
"""Run a matched P0/P1 frozen-Questioner history-context prompt pilot."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
import os
from pathlib import Path
import random
import re
import subprocess
import time
from typing import Any, Iterable


DEFAULT_MODEL = Path(
    "/engrfs/project/jiaxinh/jinyuan/R-zero-storage/models/"
    "qwen3_4b_validity_rzero_clean_formal_r10_initstep15_divlambda5_v1_"
    "questioner_v4/global_step_5/actor/huggingface"
)
DEFAULT_ARCHIVE = Path(
    "/engrfs/project/jiaxinh/jinyuan/R-zero-storage/rzero_runs/"
    "qwen3_4b_validity_rzero_clean_formal_r10_initstep15_v1/"
    "datasets/round_4_phase_b.jsonl"
)
PROMPT_VERSION = "history-context-pilot-v1"

SYSTEM_PROMPT = (
    "You are an expert competition-math problem setter.\n"
    "FIRST, in your private scratch-pad, think step-by-step to design a brand-new, non-trivial problem. "
    "The problem could come from any field of mathematics, including but not limited to algebra, geometry, "
    "number theory, combinatorics, prealgebra, probability, statistics, and calculus. "
    "Aim for a difficulty such that fewer than 30 % of advanced high-school students could solve it. "
    "Avoid re-using textbook clichés or famous contest problems.\n"
    "THEN, without revealing any of your private thoughts, output **exactly** the following two blocks:\n\n"
    "<question>\n"
    "{The full problem statement on one or more lines}\n"
    "</question>\n\n"
    r"\boxed{final_answer}"
    "\n\n"
    "Do NOT output anything else—no explanations, no extra markup."
)
BASELINE_USER_PROMPT = (
    "Generate one new, challenging reasoning question now. "
    "Remember to format the output exactly as instructed."
)
CONTRASTIVE_HEADER = """The following previously generated problems are negative references,
not examples to imitate.

Generate one new, valid, challenging competition-math problem whose primary
mathematical object and core solution method are meaningfully different from
every reference below.

Changing only numbers, notation, variable names, surface wording, or story
setting does not count as meaningfully different. Do not discuss the references
in your output. Remember to format the output exactly as instructed."""


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--expected-archive-count", type=int, default=9633)
    parser.add_argument("--group-count", type=int, default=512)
    parser.add_argument("--references-per-group", type=int, default=3)
    parser.add_argument("--rollouts-per-prompt", type=int, default=4)
    parser.add_argument("--reference-seed", type=int, default=43)
    parser.add_argument("--sampling-seed", type=int, default=42)
    parser.add_argument("--review-seed", type=int, default=44)
    parser.add_argument("--review-group-count", type=int, default=32)
    parser.add_argument("--max-reference-tokens", type=int, default=384)
    parser.add_argument("--max-prompt-tokens", type=int, default=2048)
    parser.add_argument("--max-new-tokens", type=int, default=4096)
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--top-p", type=float, default=0.99)
    parser.add_argument("--gpu-id", default="0")
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.85)
    parser.add_argument("--local-files-only", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_head() -> str | None:
    result = subprocess.run(
        ["git", "-C", str(Path(__file__).resolve().parents[3]), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def atomic_json(path: Path, value: Any) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    os.replace(temporary, path)


def atomic_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    os.replace(temporary, path)


def read_archive(path: Path, expected_count: int | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for row_index, line in enumerate(handle):
            if not line.strip():
                continue
            row = json.loads(line)
            row["_row_index"] = row_index
            rows.append(row)
    if expected_count and len(rows) != expected_count:
        raise ValueError(f"expected {expected_count} archive rows, found {len(rows)}")
    return rows


def eligible_archive_rows(
    rows: list[dict[str, Any]], tokenizer: Any, max_reference_tokens: int
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    counters = Counter()
    eligible = []
    for row in rows:
        question = str(row.get("question", "")).strip()
        if not question:
            counters["empty_question"] += 1
            continue
        if row.get("validity_decision") != "VALID":
            counters["not_valid"] += 1
            continue
        if row.get("passed_rzero_filter") is not True:
            counters["not_phase_b_passed"] += 1
            continue
        token_count = len(tokenizer.encode(question, add_special_tokens=False))
        if token_count > max_reference_tokens:
            counters["over_reference_token_limit"] += 1
            continue
        eligible.append({
            "row_index": int(row["_row_index"]),
            "question": question,
            "question_tokens": token_count,
        })
    counters["eligible"] = len(eligible)
    counters["total"] = len(rows)
    return eligible, dict(counters)


def sample_reference_groups(
    eligible: list[dict[str, Any]], group_count: int, references_per_group: int, seed: int
) -> list[list[dict[str, Any]]]:
    if references_per_group < 1:
        raise ValueError("references_per_group must be positive")
    if len(eligible) < references_per_group:
        raise ValueError("not enough eligible archive rows for one reference group")
    rng = random.Random(seed)
    return [rng.sample(eligible, references_per_group) for _ in range(group_count)]


def contrastive_user_prompt(references: list[dict[str, Any]]) -> str:
    blocks = [CONTRASTIVE_HEADER]
    for position, reference in enumerate(references, 1):
        blocks.append(f"[Negative reference {position}]\n{reference['question']}")
    return "\n\n".join(blocks)


def messages(user_prompt: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


def render_prompt(tokenizer: Any, user_prompt: str) -> str:
    chat = messages(user_prompt)
    if tokenizer.chat_template:
        return tokenizer.apply_chat_template(
            chat, tokenize=False, add_generation_prompt=True, add_special_tokens=True
        )
    return f"system: {SYSTEM_PROMPT}\nuser: {user_prompt}"


def build_requests(
    tokenizer: Any,
    reference_groups: list[list[dict[str, Any]]],
    max_prompt_tokens: int,
    sampling_seed: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    groups = []
    requests = []
    baseline_prompt = render_prompt(tokenizer, BASELINE_USER_PROMPT)
    baseline_tokens = len(tokenizer.encode(baseline_prompt, add_special_tokens=False))
    if baseline_tokens > max_prompt_tokens:
        raise ValueError(f"baseline prompt has {baseline_tokens} tokens, limit is {max_prompt_tokens}")
    for group_index, references in enumerate(reference_groups):
        treatment_prompt = render_prompt(tokenizer, contrastive_user_prompt(references))
        treatment_tokens = len(tokenizer.encode(treatment_prompt, add_special_tokens=False))
        if treatment_tokens > max_prompt_tokens:
            indices = [item["row_index"] for item in references]
            raise ValueError(
                f"P1 group {group_index} has {treatment_tokens} prompt tokens, limit is "
                f"{max_prompt_tokens}; reference rows={indices}"
            )
        request_seed = sampling_seed + group_index
        group = {
            "group_index": group_index,
            "request_seed": request_seed,
            "references": references,
            "p0_prompt_sha256": sha256_bytes(baseline_prompt.encode("utf-8")),
            "p0_prompt_tokens": baseline_tokens,
            "p1_prompt_sha256": sha256_bytes(treatment_prompt.encode("utf-8")),
            "p1_prompt_tokens": treatment_tokens,
        }
        groups.append(group)
        requests.extend([
            {
                "condition": "P0_fixed_prompt",
                "group_index": group_index,
                "prompt": baseline_prompt,
                "prompt_sha256": group["p0_prompt_sha256"],
                "prompt_tokens": baseline_tokens,
                "request_seed": request_seed,
            },
            {
                "condition": "P1_history_context",
                "group_index": group_index,
                "prompt": treatment_prompt,
                "prompt_sha256": group["p1_prompt_sha256"],
                "prompt_tokens": treatment_tokens,
                "request_seed": request_seed,
            },
        ])
    return groups, requests


def extract_last_boxed(text: str) -> str | None:
    results = []
    prefix = r"\boxed{"
    position = 0
    while True:
        start = text.find(prefix, position)
        if start < 0:
            break
        cursor = start + len(prefix)
        depth = 1
        while cursor < len(text) and depth:
            if text[cursor] == "{":
                depth += 1
            elif text[cursor] == "}":
                depth -= 1
            cursor += 1
        if depth == 0:
            results.append(text[start + len(prefix): cursor - 1].strip())
        position = max(cursor, start + len(prefix))
    return results[-1] if results else None


def parse_completion(text: str) -> tuple[str, str, bool]:
    questions = re.findall(r"<question>(.*?)</question>", text, flags=re.DOTALL)
    answer = extract_last_boxed(text)
    question = questions[-1].strip() if questions else ""
    return question, answer or "", bool(question and answer is not None)


def normalized_template(question: str) -> str:
    value = question.lower()
    value = re.sub(r"\\[a-zA-Z]+", " CMD ", value)
    value = re.sub(r"\d+(?:\.\d+)?", " NUM ", value)
    value = re.sub(r"[^a-z]+", " ", value)
    return " ".join(value.split())


def word_ngrams(question: str, width: int = 4) -> set[tuple[str, ...]]:
    words = re.findall(r"[a-z]+", question.lower())
    return {tuple(words[index:index + width]) for index in range(max(0, len(words) - width + 1))}


def jaccard(left: set[Any], right: set[Any]) -> float:
    union = left | right
    return len(left & right) / len(union) if union else 0.0


def percentile(values: list[float], probability: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower, upper = math.floor(position), math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] * (upper - position) + ordered[upper] * (position - lower)


def condition_metrics(
    rows: list[dict[str, Any]], archive_rows: list[dict[str, Any]]
) -> dict[str, Any]:
    parsed = [row for row in rows if row["format_ok"]]
    questions = [row["question"] for row in parsed]
    templates = [normalized_template(question) for question in questions]
    exact_archive = {row["question"] for row in archive_rows}
    template_archive = {normalized_template(row["question"]) for row in archive_rows}
    counts = Counter(templates)
    top = counts.most_common(10)
    top_families = []
    for template, count in top:
        examples = []
        for question in questions:
            if normalized_template(question) == template and question not in examples:
                examples.append(question)
            if len(examples) == 3:
                break
        top_families.append({"count": count, "share": count / len(parsed), "examples": examples})
    reference_similarities = [
        float(row["max_reference_4gram_jaccard"])
        for row in parsed
    ]
    return {
        "completion_count": len(rows),
        "format_success_count": len(parsed),
        "format_success_rate": len(parsed) / len(rows),
        "length_finish_count": sum(row.get("finish_reason") == "length" for row in rows),
        "length_finish_rate": (
            sum(row.get("finish_reason") == "length" for row in rows) / len(rows)
        ),
        "exact_unique_count": len(set(questions)),
        "exact_unique_rate": len(set(questions)) / len(parsed) if parsed else 0.0,
        "normalized_template_unique_count": len(counts),
        "normalized_template_unique_rate": len(counts) / len(parsed) if parsed else 0.0,
        "top_1_template_share": top[0][1] / len(parsed) if top and parsed else 0.0,
        "top_10_template_share": sum(count for _, count in top) / len(parsed) if parsed else 0.0,
        "exact_archive_overlap_rate": (
            sum(question in exact_archive for question in questions) / len(parsed) if parsed else 0.0
        ),
        "normalized_archive_overlap_rate": (
            sum(template in template_archive for template in templates) / len(parsed) if parsed else 0.0
        ),
        "reference_4gram_jaccard": {
            "mean": sum(reference_similarities) / len(reference_similarities)
            if reference_similarities else None,
            "p50": percentile(reference_similarities, 0.5) if reference_similarities else None,
            "p90": percentile(reference_similarities, 0.9) if reference_similarities else None,
            "max": max(reference_similarities) if reference_similarities else None,
        },
        "top_normalized_families": top_families,
    }


def build_review_sample(
    groups: list[dict[str, Any]],
    generations: list[dict[str, Any]],
    count: int,
    seed: int,
) -> list[dict[str, Any]]:
    if count < 0 or count > len(groups):
        raise ValueError(f"review_group_count must be between 0 and {len(groups)}")
    selected = sorted(random.Random(seed).sample(range(len(groups)), count))
    by_group_condition: dict[tuple[int, str], list[dict[str, Any]]] = {}
    for row in generations:
        by_group_condition.setdefault((row["group_index"], row["condition"]), []).append(row)
    review = []
    for group_index in selected:
        group = groups[group_index]
        review.append({
            "group_index": group_index,
            "references": group["references"],
            "P0_fixed_prompt": [
                {key: row[key] for key in ("completion_index", "format_ok", "question", "answer")}
                for row in sorted(
                    by_group_condition[(group_index, "P0_fixed_prompt")],
                    key=lambda item: item["completion_index"],
                )
            ],
            "P1_history_context": [
                {key: row[key] for key in ("completion_index", "format_ok", "question", "answer")}
                for row in sorted(
                    by_group_condition[(group_index, "P1_history_context")],
                    key=lambda item: item["completion_index"],
                )
            ],
        })
    return review


def write_report(path: Path, manifest: dict[str, Any], metrics: dict[str, Any]) -> None:
    def metric_lines(name: str, item: dict[str, Any]) -> list[str]:
        lines = [f"### {name}", ""]
        for key in (
            "completion_count", "format_success_count", "format_success_rate",
            "length_finish_count", "length_finish_rate",
            "exact_unique_rate", "normalized_template_unique_rate",
            "top_1_template_share", "top_10_template_share",
            "exact_archive_overlap_rate", "normalized_archive_overlap_rate",
        ):
            value = item[key]
            rendered = f"{value:.6%}" if key.endswith("rate") or key.endswith("share") else f"{value:,}"
            lines.append(f"- {key}: {rendered}")
        similarity = item["reference_4gram_jaccard"]
        if similarity["mean"] is not None:
            lines.extend([
                f"- max-reference 4-gram Jaccard mean: {similarity['mean']:.6f}",
                f"- max-reference 4-gram Jaccard p50/p90/max: "
                f"{similarity['p50']:.6f} / {similarity['p90']:.6f} / {similarity['max']:.6f}",
            ])
        lines.append("")
        lines.append("Top normalized families:")
        lines.append("")
        for index, family in enumerate(item["top_normalized_families"], 1):
            excerpt = " ".join(family["examples"][0].split())[:180]
            lines.append(
                f"{index}. {family['count']:,} ({family['share']:.4%}): {excerpt}"
            )
        lines.append("")
        return lines

    lines = [
        "# Frozen Questioner history-context prompt pilot", "",
        "## Integrity", "",
        f"- Git HEAD: `{manifest['git_head']}`",
        f"- Model: `{manifest['model']}`",
        f"- Archive: `{manifest['archive']}`",
        f"- Eligible archive rows: {manifest['archive_filter_counts']['eligible']:,}",
        f"- Prompt groups per condition: {manifest['group_count']:,}",
        f"- Rollouts per prompt: {manifest['rollouts_per_prompt']:,}",
        f"- Expected completions per condition: {manifest['expected_completions_per_condition']:,}",
        f"- P0/P1 share the same per-group request seed: {manifest['paired_request_seeds']}",
        f"- GPU generation wall time: {manifest['generation_wall_seconds']:.2f} s", "",
        "The normalized-template and 4-gram measurements are transparent "
        "surface diagnostics, not semantic labels.", "",
        "## Results", "",
    ]
    lines.extend(metric_lines("P0 fixed prompt", metrics["P0_fixed_prompt"]))
    lines.extend(metric_lines("P1 history context", metrics["P1_history_context"]))
    lines.extend([
        "## Interpretation guardrails", "",
        "- This pilot changes only the Questioner prompt and does not train any model.",
        "- It does not run a validity gate, Solver frontier scoring, or Phase-B filtering.",
        "- Inspect `pilot_generations.jsonl` before deciding whether to run the scored follow-up.", "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def validate_args(args: argparse.Namespace) -> None:
    if args.group_count < 1 or args.rollouts_per_prompt < 1:
        raise ValueError("group_count and rollouts_per_prompt must be positive")
    if args.temperature <= 0 or not 0 < args.top_p <= 1:
        raise ValueError("temperature must be positive and top_p must be in (0, 1]")
    if args.max_reference_tokens < 1 or args.max_prompt_tokens < 1:
        raise ValueError("token limits must be positive")
    if not 0 <= args.review_group_count <= args.group_count:
        raise ValueError("review_group_count must be between zero and group_count")


def main() -> None:
    args = arguments()
    validate_args(args)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    artifacts = [
        args.output_dir / "pilot_manifest.json",
        args.output_dir / "pilot_groups.jsonl",
        args.output_dir / "pilot_generations.jsonl",
        args.output_dir / "pilot_review_sample.jsonl",
        args.output_dir / "pilot_report.md",
    ]
    existing = [str(path) for path in artifacts if path.exists()]
    if existing and not args.overwrite:
        raise FileExistsError(f"refusing to overwrite existing artifacts: {existing}")
    if args.local_files_only:
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["CUDA_VISIBLE_DEVICES"] = str(args.gpu_id)

    from transformers import AutoTokenizer
    import transformers
    import vllm
    from vllm import LLM, SamplingParams

    tokenizer = AutoTokenizer.from_pretrained(
        str(args.model), local_files_only=args.local_files_only
    )
    archive = read_archive(args.archive, args.expected_archive_count)
    eligible, filter_counts = eligible_archive_rows(
        archive, tokenizer, args.max_reference_tokens
    )
    reference_groups = sample_reference_groups(
        eligible, args.group_count, args.references_per_group, args.reference_seed
    )
    groups, requests = build_requests(
        tokenizer, reference_groups, args.max_prompt_tokens, args.sampling_seed
    )
    sampling = [
        SamplingParams(
            n=args.rollouts_per_prompt,
            max_tokens=args.max_new_tokens,
            temperature=args.temperature,
            top_p=args.top_p,
            seed=request["request_seed"],
            stop_token_ids=[tokenizer.eos_token_id],
        )
        for request in requests
    ]
    model = LLM(
        model=str(args.model),
        tokenizer=str(args.model),
        seed=args.sampling_seed,
        gpu_memory_utilization=args.gpu_memory_utilization,
    )
    started = time.monotonic()
    outputs = model.generate(
        [request["prompt"] for request in requests], sampling_params=sampling, use_tqdm=True
    )
    generation_wall_seconds = time.monotonic() - started
    if len(outputs) != len(requests):
        raise RuntimeError(f"expected {len(requests)} request outputs, found {len(outputs)}")

    generations = []
    for request, output in zip(requests, outputs):
        if output.prompt != request["prompt"]:
            raise RuntimeError(
                f"vLLM output/prompt order mismatch for {request['condition']} "
                f"group {request['group_index']}"
            )
        group = groups[request["group_index"]]
        references = group["references"]
        reference_ngrams = [word_ngrams(item["question"]) for item in references]
        if len(output.outputs) != args.rollouts_per_prompt:
            raise RuntimeError(
                f"request {request['condition']} group {request['group_index']} returned "
                f"{len(output.outputs)} rollouts, expected {args.rollouts_per_prompt}"
            )
        for completion_index, completion in enumerate(output.outputs):
            question, answer, format_ok = parse_completion(completion.text)
            candidate_ngrams = word_ngrams(question)
            max_reference_similarity = (
                max(jaccard(candidate_ngrams, item) for item in reference_ngrams)
                if question else 0.0
            )
            generations.append({
                "condition": request["condition"],
                "group_index": request["group_index"],
                "completion_index": completion_index,
                "request_seed": request["request_seed"],
                "prompt_sha256": request["prompt_sha256"],
                "prompt_tokens": request["prompt_tokens"],
                "reference_row_indices": [item["row_index"] for item in references],
                "question": question,
                "answer": answer,
                "format_ok": format_ok,
                "normalized_template": normalized_template(question) if question else "",
                "max_reference_4gram_jaccard": max_reference_similarity,
                "completion_tokens": len(completion.token_ids),
                "finish_reason": completion.finish_reason,
                "raw_completion": completion.text,
            })

    by_condition = {
        condition: [row for row in generations if row["condition"] == condition]
        for condition in ("P0_fixed_prompt", "P1_history_context")
    }
    expected_per_condition = args.group_count * args.rollouts_per_prompt
    if any(len(rows) != expected_per_condition for rows in by_condition.values()):
        raise RuntimeError("condition output counts are not balanced")
    metrics = {
        condition: condition_metrics(rows, eligible)
        for condition, rows in by_condition.items()
    }
    review_sample = build_review_sample(
        groups, generations, args.review_group_count, args.review_seed
    )
    config_path = args.model / "config.json"
    model_index_path = args.model / "model.safetensors.index.json"
    manifest = {
        "git_head": git_head(),
        "model": str(args.model),
        "model_config_sha256": sha256_file(config_path) if config_path.is_file() else None,
        "model_index_sha256": (
            sha256_file(model_index_path) if model_index_path.is_file() else None
        ),
        "archive": str(args.archive),
        "archive_sha256": sha256_file(args.archive),
        "archive_filter_counts": filter_counts,
        "group_count": args.group_count,
        "references_per_group": args.references_per_group,
        "rollouts_per_prompt": args.rollouts_per_prompt,
        "expected_completions_per_condition": expected_per_condition,
        "total_completions": len(generations),
        "reference_seed": args.reference_seed,
        "sampling_seed": args.sampling_seed,
        "review_seed": args.review_seed,
        "review_group_count": args.review_group_count,
        "paired_request_seeds": True,
        "max_reference_tokens": args.max_reference_tokens,
        "max_prompt_tokens": args.max_prompt_tokens,
        "max_new_tokens": args.max_new_tokens,
        "temperature": args.temperature,
        "top_p": args.top_p,
        "gpu_id": str(args.gpu_id),
        "gpu_memory_utilization": args.gpu_memory_utilization,
        "generation_wall_seconds": generation_wall_seconds,
        "transformers_version": transformers.__version__,
        "vllm_version": vllm.__version__,
        "conditions": {
            "P0_fixed_prompt": "Original fixed Questioner prompt",
            "P1_history_context": "K=3 row-uniform negative references from the filtered Round-4 archive",
        },
        "prompt": {
            "version": PROMPT_VERSION,
            "system": SYSTEM_PROMPT,
            "baseline_user": BASELINE_USER_PROMPT,
            "contrastive_header": CONTRASTIVE_HEADER,
        },
        "metrics": metrics,
    }
    atomic_jsonl(args.output_dir / "pilot_groups.jsonl", groups)
    atomic_jsonl(args.output_dir / "pilot_generations.jsonl", generations)
    atomic_jsonl(args.output_dir / "pilot_review_sample.jsonl", review_sample)
    atomic_json(args.output_dir / "pilot_manifest.json", manifest)
    write_report(args.output_dir / "pilot_report.md", manifest, metrics)
    print(json.dumps({
        "output_dir": str(args.output_dir),
        "total_completions": len(generations),
        "per_condition": expected_per_condition,
        "format_success_rate": {
            condition: item["format_success_rate"] for condition, item in metrics.items()
        },
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
