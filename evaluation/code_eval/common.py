"""Serialization and resume invariants shared by GPU and CPU processes."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
VERSIONS = json.loads((HERE / "versions.json").read_text())
COUNTS = {"humaneval": 164, "mbpp": 378, "livecodebench": 880}


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    temp.replace(path)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def file_digest(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def bind(path, value):
    """Never silently reuse a directory with a different experiment or dataset."""
    path = Path(path)
    if path.exists() and read(path) != value:
        raise ValueError(f"Configuration/data changed: {path}. Use a new output directory.")
    write(path, value)


def align(tasks, outputs):
    ids = [t["task_id"] for t in tasks]
    out_ids = [r["task_id"] for r in outputs]
    if len(set(out_ids)) != len(out_ids) or set(ids) != set(out_ids):
        raise ValueError("Missing, duplicate, or unexpected task IDs in model outputs")
    by_id = {r["task_id"]: r for r in outputs}
    return [by_id[key] for key in ids]


def codegen(model, tasks, existing, params_factory, batch_size, checkpoint):
    """One completion per task. Save each completed batch atomically."""
    expected = {t["task_id"] for t in tasks}
    done = {r["task_id"]: r for r in existing}
    if len(done) != len(existing) or not set(done) <= expected:
        raise ValueError("Invalid partial generation IDs")
    pending = [t for t in tasks if t["task_id"] not in done]
    for start in range(0, len(pending), batch_size):
        batch = pending[start:start + batch_size]
        outputs = model.generate(
            [t["rendered_prompt"] for t in batch],
            sampling_params=[params_factory(t) for t in batch], use_tqdm=True,
        )
        if len(outputs) != len(batch):
            raise ValueError("vLLM returned an incomplete batch")
        for task, output in zip(batch, outputs):
            if len(output.outputs) != 1:
                raise ValueError("Expected exactly one completion per task")
            answer = output.outputs[0]
            done[task["task_id"]] = {
                "task_id": task["task_id"], "response": answer.text,
                "finish_reason": answer.finish_reason,
                "generated_tokens": len(answer.token_ids),
            }
        checkpoint([done[t["task_id"]] for t in tasks if t["task_id"] in done])
    return align(tasks, list(done.values()))
