"""Observe Base Questioner behavior without training or prompt changes."""

from __future__ import annotations

import argparse
import hashlib
import re
from collections import Counter
from pathlib import Path
from typing import Any

from qwen35.rzero.generate_candidates import atomic_json
from qwen35.rzero.prompts import QUESTIONER_MESSAGES
from qwen35.rzero.rewards.common import parse_questioner_response


PLACEHOLDER_QUESTION_PATTERN = re.compile(r"full\s+problem\s+statement|problem\s+statement", re.IGNORECASE)
META_REASONING_PATTERNS = (
    re.compile(
        r"\b(?:we|i)\s+(?:need|must|should|will)\s+(?:to\s+)?"
        r"(?:design|create|generate|craft|formulate)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(?:brainstorm|candidate problem|problem setter|the prompt|the instructions?)\b", re.IGNORECASE),
)
THINKING_OFF_GENERATION_SUFFIX = "<|im_start|>assistant\n<think>\n\n</think>\n\n"


def _is_placeholder_question(question: str) -> bool:
    stripped = question.strip()
    return bool(
        PLACEHOLDER_QUESTION_PATTERN.search(stripped)
        or stripped in {"...", "…", "{...}", "{…}"}
    )


def _has_meta_reasoning(text: str) -> bool:
    return any(pattern.search(text) for pattern in META_REASONING_PATTERNS)


def validate_rendered_prompt(prompt: str, enable_thinking: bool | None) -> None:
    """Fail closed if the pinned template ignores the diagnostic override."""

    if enable_thinking is False and not prompt.endswith(THINKING_OFF_GENERATION_SUFFIX):
        raise RuntimeError(
            "enable_thinking=False was not rendered as the expected empty thinking block; "
            "refusing to run a mislabeled diagnostic"
        )


def build_record(index: int, output: Any, max_tokens: int) -> dict[str, Any]:
    raw_response = output.text
    parsed = parse_questioner_response(raw_response)
    finish_reason = str(output.finish_reason) if output.finish_reason is not None else None
    token_count = len(output.token_ids)
    literal_final_answer = parsed["answer"].strip().lower() == "final_answer"
    placeholder_question = _is_placeholder_question(parsed["question"])
    heuristic_meta_reasoning = _has_meta_reasoning(raw_response)
    parse_success = bool(parsed["question"] and parsed["answer"])
    think_end = raw_response.rfind("</think>")
    question_start = raw_response.rfind("<question>")
    question_end = raw_response.rfind("</question>")
    answer_start = raw_response.rfind(r"\boxed{")
    valid_formatted_completion = bool(
        parse_success
        and 0 <= think_end < question_start < question_end < answer_start
    )
    heuristic_real_question = bool(
        parse_success
        and not literal_final_answer
        and not placeholder_question
        and not heuristic_meta_reasoning
    )
    stop_reason = output.stop_reason
    if stop_reason is not None and not isinstance(stop_reason, (str, int, float, bool)):
        stop_reason = str(stop_reason)
    return {
        "index": index,
        "raw_response": raw_response,
        "finish_reason": finish_reason,
        "stop_reason": stop_reason,
        "token_count": token_count,
        "parsed_question": parsed["question"],
        "parsed_answer": parsed["answer"],
        "closed_think": "</think>" in raw_response,
        "parse_success": parse_success,
        "valid_formatted_completion": valid_formatted_completion,
        "literal_final_answer": literal_final_answer,
        "placeholder_question": placeholder_question,
        # These two fields are triage hints, not ground-truth labels. The raw
        # file remains authoritative and all 128 records should be reviewed.
        "heuristic_meta_reasoning": heuristic_meta_reasoning,
        "heuristic_real_question": heuristic_real_question,
        "hit_max_tokens": finish_reason == "length" or token_count >= max_tokens,
        "manual_classification": None,
    }


def _representatives(records: list[dict[str, Any]], key: str, limit: int = 5) -> list[dict[str, Any]]:
    return [
        {"index": record["index"], "raw_response": record["raw_response"]}
        for record in records
        if record[key]
    ][:limit]


def summarize(records: list[dict[str, Any]], provenance: dict[str, Any]) -> dict[str, Any]:
    finish_reasons = Counter(str(record["finish_reason"]) for record in records)
    summary = {
        "provenance": provenance,
        "total": len(records),
        "finish_reasons": dict(sorted(finish_reasons.items())),
        "finish_reason_length": sum(record["finish_reason"] == "length" for record in records),
        "hit_4096": sum(record["hit_max_tokens"] for record in records),
        "closed_think": sum(record["closed_think"] for record in records),
        "parse_success": sum(record["parse_success"] for record in records),
        "valid_formatted_completion": sum(record["valid_formatted_completion"] for record in records),
        "literal_final_answer": sum(record["literal_final_answer"] for record in records),
        "placeholder_question": sum(record["placeholder_question"] for record in records),
        "heuristic_meta_reasoning": sum(record["heuristic_meta_reasoning"] for record in records),
        "heuristic_real_question": sum(record["heuristic_real_question"] for record in records),
        "manual_review": {
            "required": True,
            "reason": "meta_reasoning and real_question require human review of raw_response",
            "unclassified_indices": [record["index"] for record in records],
        },
        "representative_candidates": {
            "placeholder": _representatives(records, "placeholder_question"),
            "max_token_meta": [
                {"index": record["index"], "raw_response": record["raw_response"]}
                for record in records
                if record["hit_max_tokens"] and record["heuristic_meta_reasoning"]
            ][:5],
            "real_question": _representatives(records, "heuristic_real_question"),
        },
    }
    return summary


def build_parser(default_samples: int = 128) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--expected-revision", default="1001bb4")
    parser.add_argument("--samples", type=int, default=default_samples)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--top-p", type=float, default=0.95)
    parser.add_argument("--max-tokens", type=int, default=4096)
    return parser


def run_diagnostic(
    args: argparse.Namespace,
    questioner_messages: list[dict[str, str]],
    raw_filename: str,
    summary_filename: str,
    prompt_variant: str,
    enable_thinking: bool | None = None,
) -> None:

    revision_path = args.model / "RZERO_MODEL_REVISION"
    if not revision_path.is_file():
        raise RuntimeError(f"missing immutable model revision receipt: {revision_path}")
    revision = revision_path.read_text(encoding="utf-8").strip()
    if revision != args.expected_revision:
        raise RuntimeError(f"model revision mismatch: found {revision!r}, expected {args.expected_revision!r}")

    from transformers import AutoConfig, AutoTokenizer
    from vllm import LLM, SamplingParams

    config = AutoConfig.from_pretrained(args.model)
    if config.model_type != "qwen3_5":
        raise RuntimeError(f"expected qwen3_5 Base model, found {config.model_type!r}")
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    template_kwargs: dict[str, Any] = {}
    if enable_thinking is not None:
        template_kwargs["enable_thinking"] = enable_thinking
    prompt = tokenizer.apply_chat_template(
        questioner_messages,
        tokenize=False,
        add_generation_prompt=True,
        **template_kwargs,
    )
    validate_rendered_prompt(prompt, enable_thinking)

    model = LLM(
        model=str(args.model),
        tokenizer=str(args.model),
        seed=args.seed,
        language_model_only=True,
    )
    sampling = SamplingParams(
        max_tokens=args.max_tokens,
        temperature=args.temperature,
        top_p=args.top_p,
        n=1,
        # Deliberately preserve the current formal generation behavior. This
        # diagnostic must not combine the Base test with an EOS migration fix.
        stop_token_ids=[tokenizer.eos_token_id],
    )
    completions = model.generate([prompt] * args.samples, sampling_params=sampling, use_tqdm=True)
    if len(completions) != args.samples:
        raise RuntimeError(f"generated {len(completions)} rows, expected {args.samples}")

    records = [
        build_record(index, completion.outputs[0], args.max_tokens)
        for index, completion in enumerate(completions)
    ]
    provenance = {
        "model_id": "Qwen/Qwen3.5-4B-Base",
        "model_path": str(args.model),
        "model_revision": revision,
        "model_type": config.model_type,
        "model_state": "immutable_untrained_base",
        "prompt_variant": prompt_variant,
        # None means no template override was supplied and therefore preserves
        # the exact behavior used by the two earlier diagnostic baselines.
        "enable_thinking_override": enable_thinking,
        "samples": args.samples,
        "seed": args.seed,
        "temperature": args.temperature,
        "top_p": args.top_p,
        "n": 1,
        "max_tokens": args.max_tokens,
        "stop_token_ids": [tokenizer.eos_token_id],
        "eos_token": tokenizer.eos_token,
        "eos_token_id": tokenizer.eos_token_id,
        "im_end_token_id": tokenizer.convert_tokens_to_ids("<|im_end|>"),
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "rendered_prompt": prompt,
        "questioner_messages": questioner_messages,
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = args.output_dir / raw_filename
    summary_path = args.output_dir / summary_filename
    atomic_json(raw_path, records)
    atomic_json(summary_path, summarize(records, provenance))
    print(f"raw_output={raw_path}")
    print(f"summary_output={summary_path}")


def main() -> None:
    args = build_parser().parse_args()
    run_diagnostic(
        args,
        QUESTIONER_MESSAGES,
        "qwen35_base_questioner_raw_128.json",
        "qwen35_base_questioner_summary.json",
        "released_rzero",
    )


if __name__ == "__main__":
    main()
