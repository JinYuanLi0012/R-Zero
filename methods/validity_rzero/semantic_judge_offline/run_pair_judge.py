#!/usr/bin/env python3
"""Run the blind four-condition semantic-pair judge with a frozen base LM."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


PROMPT_VERSION = "semantic-pair-v1"
CANDIDATES = {"A": " A", "B": " B"}
ORDERS = ("q1_q2", "q2_q1")
MAPPINGS = ("A_same", "A_different")

INSTRUCTION = """Decide whether the two math problems have the same underlying solution type.

Treat them as the same type only when a competent solver could reuse essentially
the same central mathematical reduction and solution outline after ignoring
wording, LaTeX formatting, variable names, and routine numerical substitutions.
Sharing a topic, object, keyword, or requested answer format is not sufficient.
"""


def prompt_template(mapping: str) -> str:
    if mapping == "A_same":
        choices = "A. SAME_TYPE\nB. DIFFERENT"
    elif mapping == "A_different":
        choices = "A. DIFFERENT\nB. SAME_TYPE"
    else:
        raise ValueError(f"unknown mapping: {mapping}")
    return (
        f"{INSTRUCTION}\n"
        "Problem 1:\n{q1}\n\n"
        "Problem 2:\n{q2}\n\n"
        f"Choices:\n{choices}\n\n"
        "Answer:"
    )


def build_prompt(q1: str, q2: str, mapping: str) -> str:
    """The only model-visible values supplied by a data row are q1 and q2."""
    return prompt_template(mapping).format(q1=q1, q2=q2)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_blind(path: Path, expected_count: int) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if "gold" in row:
                raise ValueError(f"blind input contains forbidden gold field at line {line_number}")
            missing = {"pair_id", "q1", "q2"} - set(row)
            if missing:
                raise ValueError(f"blind input line {line_number} is missing {sorted(missing)}")
            rows.append({key: str(row[key]) for key in ("pair_id", "q1", "q2")})
    if len(rows) != expected_count:
        raise ValueError(f"expected {expected_count} blind rows, found {len(rows)}")
    ids = [row["pair_id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("blind pair_id values are not unique")
    return rows


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def atomic_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def git_head() -> str | None:
    for parent in Path(__file__).resolve().parents:
        if (parent / ".git").exists():
            result = subprocess.run(
                ["git", "-C", str(parent), "rev-parse", "HEAD"],
                capture_output=True, text=True, check=False,
            )
            return result.stdout.strip() if result.returncode == 0 else None
    return None


def looks_nonbase(model: str) -> bool:
    lowered = model.lower()
    return any(marker in lowered for marker in ("instruct", "global_step", "checkpoint"))


@dataclass(frozen=True)
class Condition:
    pair_id: str
    question_order: str
    mapping: str
    prompt: str


@dataclass(frozen=True)
class CandidateTask:
    condition_index: int
    option: str
    prompt_ids: list[int]
    candidate_ids: list[int]


def make_conditions(rows: list[dict[str, str]]) -> list[Condition]:
    conditions: list[Condition] = []
    for row in rows:
        for order in ORDERS:
            first, second = ((row["q1"], row["q2"]) if order == "q1_q2"
                             else (row["q2"], row["q1"]))
            for mapping in MAPPINGS:
                conditions.append(Condition(
                    pair_id=row["pair_id"], question_order=order, mapping=mapping,
                    prompt=build_prompt(first, second, mapping),
                ))
    return conditions


def resolve_dtype(torch: Any, requested: str, device: str) -> Any:
    if requested == "auto":
        if device.startswith("cuda"):
            return torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
        return torch.float32
    return {
        "bfloat16": torch.bfloat16,
        "float16": torch.float16,
        "float32": torch.float32,
    }[requested]


def score_tasks(
    model: Any,
    torch: Any,
    tasks: list[CandidateTask],
    pad_token_id: int,
    device: str,
    batch_size: int,
) -> dict[tuple[int, str], dict[str, Any]]:
    """Score every candidate continuation token, without generating any text."""
    results: dict[tuple[int, str], dict[str, Any]] = {}
    for start in range(0, len(tasks), batch_size):
        batch = tasks[start:start + batch_size]
        sequences = [task.prompt_ids + task.candidate_ids for task in batch]
        maximum = max(map(len, sequences))
        input_ids = torch.full(
            (len(batch), maximum), pad_token_id, dtype=torch.long, device=device,
        )
        attention_mask = torch.zeros(
            (len(batch), maximum), dtype=torch.long, device=device,
        )
        for index, sequence in enumerate(sequences):
            input_ids[index, :len(sequence)] = torch.tensor(sequence, device=device)
            attention_mask[index, :len(sequence)] = 1
        output = model(input_ids=input_ids, attention_mask=attention_mask, use_cache=False)
        for index, task in enumerate(batch):
            positions = torch.arange(
                len(task.prompt_ids) - 1,
                len(task.prompt_ids) + len(task.candidate_ids) - 1,
                device=device,
            )
            logits = output.logits[index, positions, :].float()
            targets = torch.tensor(task.candidate_ids, dtype=torch.long, device=device)
            token_logprobs = torch.log_softmax(logits, dim=-1).gather(
                1, targets[:, None]
            ).squeeze(1)
            values = [float(value) for value in token_logprobs.cpu().tolist()]
            results[(task.condition_index, task.option)] = {
                "token_logprobs": values,
                "sum": sum(values),
                "mean": sum(values) / len(values),
            }
        del output, input_ids, attention_mask
    return results


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="blind JSONL only")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model", default="Qwen/Qwen3-4B-Base")
    parser.add_argument("--revision", default=None)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument(
        "--dtype", choices=("auto", "bfloat16", "float16", "float32"), default="auto",
    )
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--expected-count", type=int, default=50)
    parser.add_argument("--local-files-only", action="store_true")
    parser.add_argument("--trust-remote-code", action="store_true")
    parser.add_argument("--allow-nonbase-model", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = arguments()
    if args.batch_size < 1:
        raise ValueError("--batch-size must be positive")
    if looks_nonbase(args.model) and not args.allow_nonbase_model:
        raise ValueError(
            "model path looks instruction-tuned or trained; pass the frozen base model, "
            "or explicitly acknowledge the deviation with --allow-nonbase-model"
        )
    output_path = args.output_dir / "predictions.jsonl"
    manifest_path = args.output_dir / "run_manifest.json"
    if not args.overwrite and (output_path.exists() or manifest_path.exists()):
        raise FileExistsError("output already exists; use a new directory or --overwrite")

    blind = read_blind(args.input, args.expected_count)

    import torch
    import transformers
    from transformers import AutoModelForCausalLM, AutoTokenizer

    if args.device.startswith("cuda") and not torch.cuda.is_available():
        raise RuntimeError(f"CUDA device requested but CUDA is unavailable: {args.device}")
    dtype = resolve_dtype(torch, args.dtype, args.device)
    load_options = {
        "revision": args.revision,
        "local_files_only": args.local_files_only,
        "trust_remote_code": args.trust_remote_code,
    }
    tokenizer = AutoTokenizer.from_pretrained(args.model, **load_options)
    model = AutoModelForCausalLM.from_pretrained(
        args.model, torch_dtype=dtype, low_cpu_mem_usage=True, **load_options,
    )
    model.to(args.device)
    model.eval()
    for parameter in model.parameters():
        parameter.requires_grad_(False)

    candidate_ids = {
        option: tokenizer.encode(text, add_special_tokens=False)
        for option, text in CANDIDATES.items()
    }
    if any(not token_ids for token_ids in candidate_ids.values()):
        raise RuntimeError(f"empty candidate tokenization: {candidate_ids}")
    equal_token_lengths = len(candidate_ids["A"]) == len(candidate_ids["B"])
    scoring_rule = (
        "conditional_logprob_sum"
        if equal_token_lengths
        else "length_normalized_conditional_logprob_mean"
    )

    conditions = make_conditions(blind)
    tasks: list[CandidateTask] = []
    maximum_sequence_tokens = 0
    for index, condition in enumerate(conditions):
        prompt_ids = tokenizer.encode(condition.prompt, add_special_tokens=True)
        if not prompt_ids:
            raise RuntimeError(f"empty prompt tokenization for condition {index}")
        for option in ("A", "B"):
            tasks.append(CandidateTask(index, option, prompt_ids, candidate_ids[option]))
            maximum_sequence_tokens = max(
                maximum_sequence_tokens, len(prompt_ids) + len(candidate_ids[option]),
            )
    model_limit = getattr(model.config, "max_position_embeddings", None)
    if model_limit is not None and maximum_sequence_tokens > int(model_limit):
        raise ValueError(
            f"input requires {maximum_sequence_tokens} tokens but model limit is {model_limit}"
        )
    pad_token_id = tokenizer.pad_token_id
    if pad_token_id is None:
        pad_token_id = tokenizer.eos_token_id
    if pad_token_id is None:
        raise RuntimeError("tokenizer has neither pad_token_id nor eos_token_id")

    with torch.inference_mode():
        scores = score_tasks(
            model, torch, tasks, int(pad_token_id), args.device, args.batch_size,
        )

    predictions: list[dict[str, Any]] = []
    for index, condition in enumerate(conditions):
        score_a_raw = scores[(index, "A")]
        score_b_raw = scores[(index, "B")]
        score_a = score_a_raw["sum"] if equal_token_lengths else score_a_raw["mean"]
        score_b = score_b_raw["sum"] if equal_token_lengths else score_b_raw["mean"]
        option = "A" if score_a > score_b else "B"
        if condition.mapping == "A_same":
            predicted_label = "SAME_TYPE" if option == "A" else "DIFFERENT"
        else:
            predicted_label = "DIFFERENT" if option == "A" else "SAME_TYPE"
        predictions.append({
            "pair_id": condition.pair_id,
            "question_order": condition.question_order,
            "mapping": condition.mapping,
            "score_a": score_a,
            "score_b": score_b,
            "score_margin_a_minus_b": score_a - score_b,
            "score_a_sum": score_a_raw["sum"],
            "score_b_sum": score_b_raw["sum"],
            "score_a_mean": score_a_raw["mean"],
            "score_b_mean": score_b_raw["mean"],
            "token_logprobs_a": score_a_raw["token_logprobs"],
            "token_logprobs_b": score_b_raw["token_logprobs"],
            "selected_option": option,
            "predicted_label": predicted_label,
            "model": args.model,
            "model_revision": getattr(model.config, "_commit_hash", None) or args.revision,
            "prompt_version": PROMPT_VERSION,
            "scoring_rule": scoring_rule,
        })

    args.output_dir.mkdir(parents=True, exist_ok=True)
    atomic_jsonl(output_path, predictions)
    gpu_name = None
    if args.device.startswith("cuda"):
        gpu_name = torch.cuda.get_device_name(torch.device(args.device))
    manifest = {
        "experiment": "semantic_judge_offline_50",
        "prompt_version": PROMPT_VERSION,
        "prompt_templates": {mapping: prompt_template(mapping) for mapping in MAPPINGS},
        "prompt_sha256": {
            mapping: sha256_bytes(prompt_template(mapping).encode("utf-8"))
            for mapping in MAPPINGS
        },
        "blind_input": str(args.input.resolve()),
        "blind_input_sha256": sha256_file(args.input),
        "blind_input_fields_visible_to_model": ["q1", "q2"],
        "pair_count": len(blind),
        "condition_count": len(predictions),
        "condition_order": ["pair input order", "question order", "answer mapping"],
        "question_orders": list(ORDERS),
        "answer_mappings": list(MAPPINGS),
        "primary_condition": {"question_order": "q1_q2", "mapping": "A_same"},
        "model_argument": args.model,
        "model_name_or_path": getattr(model, "name_or_path", None),
        "model_revision": getattr(model.config, "_commit_hash", None) or args.revision,
        "model_class": type(model).__name__,
        "tokenizer_class": type(tokenizer).__name__,
        "candidate_text": CANDIDATES,
        "candidate_token_ids": candidate_ids,
        "candidate_token_text": {
            option: [tokenizer.decode([token_id]) for token_id in token_ids]
            for option, token_ids in candidate_ids.items()
        },
        "scoring": {
            "rule": scoring_rule,
            "description": (
                "Sum candidate continuation token log probabilities when A and B have "
                "equal token counts; otherwise compare their mean token log probabilities."
            ),
            "prompt_add_special_tokens": True,
            "candidate_add_special_tokens": False,
            "generation": False,
        },
        "maximum_sequence_tokens": maximum_sequence_tokens,
        "requested_dtype": args.dtype,
        "resolved_dtype": str(dtype),
        "device": args.device,
        "gpu": gpu_name,
        "batch_size": args.batch_size,
        "git_head": git_head(),
        "software": {
            "python": platform.python_version(),
            "torch": torch.__version__,
            "transformers": transformers.__version__,
        },
        "nonbase_model_override": bool(args.allow_nonbase_model),
    }
    atomic_json(manifest_path, manifest)
    print(f"wrote {len(predictions)} conditions to {output_path}")
    print(f"wrote run metadata to {manifest_path}")


if __name__ == "__main__":
    main()
