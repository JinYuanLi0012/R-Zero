#!/usr/bin/env python3
"""Run the paired P0/PLOPE frozen Semantic-MC Round-2 Questioner experiment."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import random
import re
import subprocess
import sys
import time
from typing import Any, Callable, Iterable

if __package__ in {None, ""}:  # Support the documented direct-script command.
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from methods.validity_rzero.frozen_lope_pilot.lorem_compat import get_word


DEFAULT_MODEL = Path(
    "/engrfs/project/jiaxinh/jinyuan/R-zero-storage/models/"
    "qwen3_4b_validity_rzero_semantic_mc_4gpu_v1_questioner_v2/"
    "global_step_5/actor/huggingface"
)
PROMPT_VERSION = "frozen-questioner-lope-v1"
BOUNDARY = "Follow the task instruction below."
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
USER_PROMPT = (
    "Generate one new, challenging reasoning question now. "
    "Remember to format the output exactly as instructed."
)


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--request-count", type=int, default=8000)
    parser.add_argument("--generation-seed-base", type=int, default=10000)
    parser.add_argument("--perturbation-seed-base", type=int, default=50000)
    parser.add_argument("--lorem-min-tokens", type=int, default=100)
    parser.add_argument("--lorem-max-tokens", type=int, default=300)
    parser.add_argument("--max-prompt-tokens", type=int, default=1024)
    parser.add_argument("--max-new-tokens", type=int, default=4096)
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--top-p", type=float, default=0.95)
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


def render_prompt(tokenizer: Any, system_prompt: str) -> str:
    chat = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": USER_PROMPT},
    ]
    if tokenizer.chat_template:
        return tokenizer.apply_chat_template(
            chat, tokenize=False, add_generation_prompt=True, add_special_tokens=True
        )
    return f"system: {system_prompt}\nuser: {USER_PROMPT}"


def generate_lorem_perturbation(
    tokenizer: Any,
    seed: int,
    min_tokens: int,
    max_tokens: int,
    word_generator: Callable[..., str],
) -> tuple[str, int]:
    """Generate deterministic python-lorem text with an exact uniform token target."""
    rng = random.Random(seed)
    target_tokens = rng.randint(min_tokens, max_tokens)
    global_state = random.getstate()
    random.seed(seed)
    try:
        word_count = target_tokens * 2
        for _ in range(6):
            source = word_generator(count=word_count)
            source_ids = tokenizer.encode(source, add_special_tokens=False)
            if len(source_ids) < target_tokens:
                word_count *= 2
                continue
            perturbation = tokenizer.decode(
                source_ids[:target_tokens],
                skip_special_tokens=True,
                clean_up_tokenization_spaces=False,
            )
            actual_tokens = len(tokenizer.encode(perturbation, add_special_tokens=False))
            if actual_tokens == target_tokens:
                return perturbation, actual_tokens
            word_count *= 2
    finally:
        random.setstate(global_state)
    raise RuntimeError(
        f"could not construct a round-trip-stable {target_tokens}-token Lorem perturbation"
    )


def build_requests(
    tokenizer: Any,
    request_count: int,
    generation_seed_base: int,
    perturbation_seed_base: int,
    lorem_min_tokens: int,
    lorem_max_tokens: int,
    max_prompt_tokens: int,
    word_generator: Callable[..., str],
) -> list[dict[str, Any]]:
    fixed_prompt = render_prompt(tokenizer, SYSTEM_PROMPT)
    fixed_prompt_tokens = len(tokenizer.encode(fixed_prompt, add_special_tokens=False))
    if fixed_prompt_tokens > max_prompt_tokens:
        raise ValueError(
            f"fixed prompt has {fixed_prompt_tokens} tokens, limit is {max_prompt_tokens}"
        )
    requests = []
    for zero_based_id in range(request_count):
        request_id = zero_based_id + 1
        generation_seed = generation_seed_base + request_id
        perturbation_seed = perturbation_seed_base + request_id
        perturbation_text, perturbation_token_count = generate_lorem_perturbation(
            tokenizer,
            perturbation_seed,
            lorem_min_tokens,
            lorem_max_tokens,
            word_generator,
        )
        lope_system_prompt = f"{perturbation_text}\n\n{BOUNDARY}\n\n{SYSTEM_PROMPT}"
        lope_prompt = render_prompt(tokenizer, lope_system_prompt)
        lope_prompt_tokens = len(tokenizer.encode(lope_prompt, add_special_tokens=False))
        if lope_prompt_tokens > max_prompt_tokens:
            raise ValueError(
                f"LOPE request {request_id} has {lope_prompt_tokens} prompt tokens, "
                f"limit is {max_prompt_tokens}"
            )
        requests.extend([
            {
                "request_id": request_id,
                "condition": "fixed",
                "generation_seed": generation_seed,
                "perturbation_seed": None,
                "perturbation_token_count": None,
                "perturbation_text": None,
                "prompt": fixed_prompt,
                "prompt_token_count": fixed_prompt_tokens,
                "prompt_sha256": sha256_bytes(fixed_prompt.encode("utf-8")),
            },
            {
                "request_id": request_id,
                "condition": "lope",
                "generation_seed": generation_seed,
                "perturbation_seed": perturbation_seed,
                "perturbation_token_count": perturbation_token_count,
                "perturbation_text": perturbation_text,
                "prompt": lope_prompt,
                "prompt_token_count": lope_prompt_tokens,
                "prompt_sha256": sha256_bytes(lope_prompt.encode("utf-8")),
            },
        ])
    return requests


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


def surface_key(question: str) -> str:
    return " ".join(question.lower().split())


def numeric_template_key(question: str) -> str:
    return re.sub(r"\d+(?:\.\d+)?", "<NUM>", surface_key(question))


def repeated_member_share(counts: Counter[str], denominator: int) -> float:
    return sum(count for count in counts.values() if count >= 2) / denominator if denominator else 0.0


def condition_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    parsed = [row for row in rows if row["parsed_question_success"]]
    surface_counts = Counter(surface_key(row["parsed_question"]) for row in parsed)
    template_counts = Counter(numeric_template_key(row["parsed_question"]) for row in parsed)
    top_five = template_counts.most_common(5)
    return {
        "completion_count": len(rows),
        "parsed_question_count": len(parsed),
        "parsed_question_success_rate": len(parsed) / len(rows) if rows else 0.0,
        "surface_duplicate_share": repeated_member_share(surface_counts, len(parsed)),
        "numeric_normalized_repeated_template_share": repeated_member_share(
            template_counts, len(parsed)
        ),
        "top_5_normalized_template_mass": (
            sum(count for _, count in top_five) / len(parsed) if parsed else 0.0
        ),
        "surface_unique_count": len(surface_counts),
        "normalized_template_unique_count": len(template_counts),
        "top_5_normalized_templates": [
            {"template": template, "count": count, "share": count / len(parsed)}
            for template, count in top_five
        ],
    }


def write_report(path: Path, manifest: dict[str, Any], metrics: dict[str, Any]) -> None:
    fixed = metrics["fixed"]
    lope = metrics["lope"]
    rows = [
        ("Numeric-normalized repeated-template share", "numeric_normalized_repeated_template_share"),
        ("Surface duplicate share", "surface_duplicate_share"),
        ("Top-5 normalized-template mass", "top_5_normalized_template_mass"),
        ("Parsed-question success", "parsed_question_success_rate"),
    ]
    lines = [
        "# Frozen Semantic-MC Round-2 Questioner LOPE test",
        "",
        "## Integrity",
        "",
        f"- Git HEAD: `{manifest['git_head']}`",
        f"- Model: `{manifest['model']}`",
        f"- Requests per condition: {manifest['request_count']:,}",
        f"- Total completions: {manifest['total_completions']:,}",
        f"- Paired generation seeds: {manifest['paired_generation_seeds']}",
        f"- Lorem length: uniform integer target in [{manifest['lorem_min_tokens']}, "
        f"{manifest['lorem_max_tokens']}] Qwen tokens",
        f"- Boundary: `{manifest['boundary']}`",
        f"- GPU generation wall time: {manifest['generation_wall_seconds']:.2f} s",
        "",
        "Duplicate metrics use successfully parsed questions as their denominator; parse success is reported separately.",
        "",
        "## Results",
        "",
        "| Metric | Fixed prompt | Random-Lorem | Delta (pp) |",
        "|---|---:|---:|---:|",
    ]
    for label, key in rows:
        delta = (lope[key] - fixed[key]) * 100
        lines.append(f"| {label} | {fixed[key]:.4%} | {lope[key]:.4%} | {delta:+.2f} |")
    lines.extend([
        "",
        "## Reference collapsed-dataset values",
        "",
        "The existing filtered Semantic-MC Round-2 dataset had surface duplicate share 74.3%, "
        "numeric-normalized repeated-template share 80.3%, and Top-5 normalized-template mass 45.4%. "
        "Those values describe a filtered training dataset; the frozen pilot above measures parsed raw generations.",
        "",
        "## Top normalized templates",
        "",
    ])
    for condition in ("fixed", "lope"):
        lines.extend([f"### {condition}", ""])
        for index, item in enumerate(metrics[condition]["top_5_normalized_templates"], 1):
            lines.append(
                f"{index}. {item['count']:,} ({item['share']:.4%}): `{item['template'][:300]}`"
            )
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def validate_args(args: argparse.Namespace) -> None:
    if args.request_count < 1:
        raise ValueError("request_count must be positive")
    if args.generation_seed_base < 0 or args.perturbation_seed_base < 0:
        raise ValueError("seed bases must be nonnegative")
    if not 1 <= args.lorem_min_tokens <= args.lorem_max_tokens:
        raise ValueError("Lorem token bounds must satisfy 1 <= min <= max")
    if args.max_prompt_tokens < 1 or args.max_new_tokens < 1:
        raise ValueError("token limits must be positive")
    if args.temperature <= 0 or not 0 < args.top_p <= 1:
        raise ValueError("temperature must be positive and top_p must be in (0, 1]")
    if not 0 < args.gpu_memory_utilization < 1:
        raise ValueError("gpu_memory_utilization must be in (0, 1)")


def main() -> None:
    args = arguments()
    validate_args(args)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    artifacts = [
        args.output_dir / "pilot_manifest.json",
        args.output_dir / "pilot_generations.jsonl",
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
    requests = build_requests(
        tokenizer=tokenizer,
        request_count=args.request_count,
        generation_seed_base=args.generation_seed_base,
        perturbation_seed_base=args.perturbation_seed_base,
        lorem_min_tokens=args.lorem_min_tokens,
        lorem_max_tokens=args.lorem_max_tokens,
        max_prompt_tokens=args.max_prompt_tokens,
        word_generator=get_word,
    )
    sampling = [
        SamplingParams(
            n=1,
            max_tokens=args.max_new_tokens,
            temperature=args.temperature,
            top_p=args.top_p,
            seed=request["generation_seed"],
            stop_token_ids=[tokenizer.eos_token_id],
        )
        for request in requests
    ]
    model = LLM(
        model=str(args.model),
        tokenizer=str(args.model),
        seed=args.generation_seed_base,
        gpu_memory_utilization=args.gpu_memory_utilization,
        enable_prefix_caching=True,
    )
    started = time.monotonic()
    outputs = model.generate(
        [request["prompt"] for request in requests], sampling_params=sampling, use_tqdm=True
    )
    generation_wall_seconds = time.monotonic() - started
    if len(outputs) != len(requests):
        raise RuntimeError(f"expected {len(requests)} outputs, found {len(outputs)}")

    generations = []
    for request, output in zip(requests, outputs):
        if output.prompt != request["prompt"]:
            raise RuntimeError(
                f"vLLM output order mismatch for request {request['request_id']} "
                f"condition {request['condition']}"
            )
        if len(output.outputs) != 1:
            raise RuntimeError(
                f"request {request['request_id']} condition {request['condition']} returned "
                f"{len(output.outputs)} completions"
            )
        completion = output.outputs[0]
        question, answer, parse_ok = parse_completion(completion.text)
        generations.append({
            "request_id": request["request_id"],
            "condition": request["condition"],
            "generation_seed": request["generation_seed"],
            "perturbation_seed": request["perturbation_seed"],
            "perturbation_token_count": request["perturbation_token_count"],
            "perturbation_text": request["perturbation_text"],
            "prompt_sha256": request["prompt_sha256"],
            "prompt_token_count": request["prompt_token_count"],
            "raw_completion": completion.text,
            "parsed_question": question,
            "parsed_answer": answer,
            "parsed_question_success": parse_ok,
            "surface_key": surface_key(question) if parse_ok else "",
            "numeric_template_key": numeric_template_key(question) if parse_ok else "",
            "completion_token_count": len(completion.token_ids),
            "finish_reason": completion.finish_reason,
        })

    by_condition = {
        condition: [row for row in generations if row["condition"] == condition]
        for condition in ("fixed", "lope")
    }
    if any(len(rows) != args.request_count for rows in by_condition.values()):
        raise RuntimeError("condition output counts are not balanced")
    for fixed, lope in zip(by_condition["fixed"], by_condition["lope"]):
        if fixed["request_id"] != lope["request_id"] or fixed["generation_seed"] != lope["generation_seed"]:
            raise RuntimeError("paired request IDs or generation seeds do not match")
    metrics = {
        condition: condition_metrics(rows) for condition, rows in by_condition.items()
    }
    config_path = args.model / "config.json"
    model_index_path = args.model / "model.safetensors.index.json"
    manifest = {
        "experiment": "frozen_semantic_mc_round2_questioner_lope_v1",
        "git_head": git_head(),
        "model": str(args.model),
        "model_config_sha256": sha256_file(config_path) if config_path.is_file() else None,
        "model_index_sha256": sha256_file(model_index_path) if model_index_path.is_file() else None,
        "request_count": args.request_count,
        "total_completions": len(generations),
        "generation_seed_base": args.generation_seed_base,
        "perturbation_seed_base": args.perturbation_seed_base,
        "paired_generation_seeds": True,
        "lorem_generator": "vendored python-lorem 1.3.0.post3-compatible get_word",
        "lorem_min_tokens": args.lorem_min_tokens,
        "lorem_max_tokens": args.lorem_max_tokens,
        "lorem_length_sampling": "uniform_integer_exact_qwen_token_count",
        "perturbation_placement": "prepend_to_original_system_prompt",
        "boundary": BOUNDARY,
        "max_prompt_tokens": args.max_prompt_tokens,
        "max_new_tokens": args.max_new_tokens,
        "temperature": args.temperature,
        "top_p": args.top_p,
        "stop_token_ids": [tokenizer.eos_token_id],
        "gpu_id": str(args.gpu_id),
        "gpu_memory_utilization": args.gpu_memory_utilization,
        "generation_wall_seconds": generation_wall_seconds,
        "transformers_version": transformers.__version__,
        "vllm_version": vllm.__version__,
        "prompt": {
            "version": PROMPT_VERSION,
            "system": SYSTEM_PROMPT,
            "user": USER_PROMPT,
        },
        "conditions": {
            "fixed": "Original fixed Questioner prompt",
            "lope": "Independent 100-300-token python-lorem prefix, boundary, original prompt",
        },
        "metric_denominator": "successfully_parsed_questions_per_condition",
        "metrics": metrics,
    }
    atomic_jsonl(args.output_dir / "pilot_generations.jsonl", generations)
    atomic_json(args.output_dir / "pilot_manifest.json", manifest)
    write_report(args.output_dir / "pilot_report.md", manifest, metrics)
    print(json.dumps({
        "output_dir": str(args.output_dir),
        "total_completions": len(generations),
        "metrics": metrics,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
