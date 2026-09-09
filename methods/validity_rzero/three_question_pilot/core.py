"""CPU-only protocol, parsing and artifact helpers for frozen Q4 + S3."""
from __future__ import annotations

import ast
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re

REPO = Path(__file__).resolve().parents[3]
METHOD = Path(__file__).resolve().parent
PROVENANCE = ("sample_id", "request_id", "question_position", "shard", "request_index")


def original_messages():
    """Read the literal production prompt without importing vLLM or loading math data."""
    tree = ast.parse((REPO / "question_generate/question_generate.py").read_text())
    main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
    assignment = next(n for n in main.body if isinstance(n, ast.Assign)
                      and any(isinstance(t, ast.Name) and t.id == "chat" for t in n.targets))
    return ast.literal_eval(assignment.value)


def three_messages():
    chat = original_messages()
    edits = (
        (0, "design a brand-new, non-trivial problem.", "design three brand-new, non-trivial problems."),
        (0, "The problem could come", "Each problem could come"),
        (0, "output **exactly** the following two blocks:",
         "output **exactly** three pairs of the following two blocks, one pair per problem, in order:"),
        (1, "Generate one new, challenging reasoning question now.",
         "Generate three new, challenging reasoning questions now."),
    )
    for i, old, new in edits:
        if chat[i]["content"].count(old) != 1:
            raise ValueError(f"production prompt changed; review this experiment: {old}")
        chat[i]["content"] = chat[i]["content"].replace(old, new)
    return chat


def boxed_answers(text):
    """Only complete balanced boxes count; support nested LaTeX braces."""
    answers = []
    i = 0
    prefix = "\\boxed{"
    while True:
        start = text.find(prefix, i)
        if start < 0:
            return answers
        j, depth = start + len(prefix), 1
        begin = j
        while j < len(text) and depth:
            if text[j] == "{" and (j == 0 or text[j - 1] != "\\"):
                depth += 1
            elif text[j] == "}" and (j == 0 or text[j - 1] != "\\"):
                depth -= 1
            j += 1
        if depth:
            return answers
        answers.append(text[begin:j - 1].strip())
        i = j


def parse_three(text):
    """Pair each of the first three opening tags with its own following answer.

    A malformed/missing earlier answer never borrows the next question's box.
    Positions count opening tags, including broken ones; no dedup or refill.
    """
    starts = list(re.finditer(r"<question>", text))
    parsed, diagnostics = [], []
    for index, start in enumerate(starts[:3]):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        chunk = text[start.end():end]
        close = chunk.find("</question>")
        status = "missing_close"
        if close >= 0:
            question = chunk[:close].strip()
            answers = boxed_answers(chunk[close + len("</question>"):])
            status = "empty_question" if not question else "missing_answer"
            if question and answers and answers[-1]:
                parsed.append({"question": question, "answer": answers[-1], "score": 0,
                               "question_position": index + 1})
                status = "parsed"
        diagnostics.append({"question_position": index + 1, "status": status})
    return parsed, {"opening_tag_count": len(starts), "extra_blocks_ignored": max(0, len(starts) - 3),
                    "blocks": diagnostics, "parsed_count": len(parsed)}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".tmp-{os.getpid()}")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    os.replace(temporary, path)


def atomic_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".tmp-{os.getpid()}")
    with temporary.open("w") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    os.replace(temporary, path)


def read_jsonl(path):
    with Path(path).open() as stream:
        return [json.loads(line) for line in stream if line.strip()]


def resolve_model(root, step):
    root = Path(root).expanduser()
    path = root if (root / "config.json").is_file() else root / f"global_step_{step}/actor/huggingface"
    if not (path / "config.json").is_file():
        raise FileNotFoundError(f"Missing merged HF checkpoint: {path}. Supply an explicit HF directory; no latest-step fallback.")
    weights = sorted(list(path.glob("*.safetensors")) + list(path.glob("pytorch_model*.bin")))
    if not weights:
        raise FileNotFoundError(f"No HF weights in {path}; merge the checkpoint first.")
    metadata = {p.name: sha(p) for p in path.glob("*.json")}
    return str(path.resolve()), {"metadata_sha256": metadata,
                                "weight_files": [{"name": p.name, "size": p.stat().st_size,
                                                  "mtime_ns": p.stat().st_mtime_ns} for p in weights]}


def distribution(rows):
    """Transparent text proxies only, not semantic skill or answer correctness."""
    n = len(rows)
    exact = Counter(r["question"].strip() for r in rows)
    templates = Counter(re.sub(r"\d+(?:\.\d+)?", "#", " ".join(r["question"].lower().split())) for r in rows)
    return {"count": n, "exact_unique_count": len(exact),
            "exact_unique_ratio": len(exact) / n if n else None,
            "exact_repeated_row_share": sum(v for v in exact.values() if v > 1) / n if n else None,
            "numeric_template_unique_count": len(templates),
            "numeric_template_unique_ratio": len(templates) / n if n else None,
            "top10_numeric_template_share": sum(v for _, v in templates.most_common(10)) / n if n else None}
