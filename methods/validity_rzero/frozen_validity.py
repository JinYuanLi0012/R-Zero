"""Opt-in frozen validity prepass; no model imports in the controller."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time

GATE_KEY = "frozen_validity_gate"


def enabled() -> bool:
    return (os.getenv("VALIDITY_RZERO_ENABLED", "0") == "1"
            and os.getenv("VALIDITY_RZERO_VALIDITY_JUDGE_MODE", "current_solver") == "frozen")


def model_path() -> str:
    path = Path(os.environ["VALIDITY_RZERO_VALIDITY_JUDGE_MODEL"]).resolve()
    if not path.is_dir():
        raise ValueError(f"frozen validity checkpoint missing: {path}")
    return str(path)


def checked_gate(row: dict) -> dict:
    """Require a gate from the configured judge; never fall back to the Solver."""
    from .gating import evaluate_validity_responses
    envelope = row[GATE_KEY]
    if envelope["model"] != model_path() or envelope["question"] != row["question"]:
        raise ValueError("frozen validity question/model mismatch")
    # Recompute from the nine original responses using the unchanged parser.
    gate = evaluate_validity_responses(envelope["responses"])
    return {**gate, "validity_judge_mode": "frozen", "validity_judge_model": envelope["model"]}


def run_workers(rows: list[dict], gpu_ids: list[str], phase: str) -> list[dict]:
    from .semantic_mc_gpu import terminate_process_groups, tail_text
    from .service_handoff import wait_gpus_released
    if phase not in {"a", "b"} or not gpu_ids or len(set(gpu_ids)) != len(gpu_ids):
        raise ValueError("invalid frozen validity phase/GPU IDs")
    model = model_path()
    temp_root = Path(os.environ["STORAGE_PATH"]) / "temp_results"
    temp_root.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix=f"frozen_validity_{phase}_", dir=temp_root))
    processes, handles, outputs = [], [], []
    pid_file = Path(os.environ.get("VALIDITY_RZERO_FROZEN_PID_FILE", str(work / "workers.pids")))
    old_handlers = {}

    def interrupted(signum, frame):
        raise RuntimeError(f"frozen validity controller interrupted by signal {signum}")

    try:
        # The reward manager may call from a non-main thread.
        import threading
        if threading.current_thread() is threading.main_thread():
            for sig in (signal.SIGTERM, signal.SIGINT):
                old_handlers[sig] = signal.signal(sig, interrupted)
        for shard, gpu in enumerate(gpu_ids):
            subset = [{"index": index, "question": row["question"]}
                      for index, row in enumerate(rows) if index % len(gpu_ids) == shard]
            if not subset:
                continue
            source, target, log = (work / f"{shard}.{ext}" for ext in ("input.json", "output.json", "log"))
            source.write_text(json.dumps(subset), encoding="utf-8")
            handle = log.open("w", encoding="utf-8")
            handles.append(handle)
            env = {**os.environ, "CUDA_VISIBLE_DEVICES": gpu, "PYTHONUNBUFFERED": "1"}
            process = subprocess.Popen([
                sys.executable, "-m", "methods.validity_rzero.frozen_validity",
                "--worker-input", str(source), "--worker-output", str(target),
                "--model", model, "--phase", phase, "--seed", str(shard),
            ], env=env, stdout=handle, stderr=subprocess.STDOUT, start_new_session=True)
            processes.append(process)
            outputs.append((target, log))
            pid_file.parent.mkdir(parents=True, exist_ok=True)
            pid_file.write_text("".join(f"{p.pid}\n" for p in processes), encoding="utf-8")
        deadline = time.monotonic() + float(os.getenv("VALIDITY_RZERO_FROZEN_TIMEOUT", "14400"))
        while any(p.poll() is None for p in processes):
            if any(p.poll() not in (None, 0) for p in processes) or time.monotonic() > deadline:
                raise RuntimeError(f"frozen validity worker failure/timeout; logs: {work}")
            time.sleep(0.2)
        if any(p.returncode != 0 for p in processes):
            raise RuntimeError(f"frozen validity worker failed; logs: {work}")
        indexed = {}
        for target, _ in outputs:
            for result in json.loads(target.read_text(encoding="utf-8")):
                index = result.pop("index")
                if index in indexed:
                    raise ValueError("duplicate frozen validity index")
                indexed[index] = result
        if set(indexed) != set(range(len(rows))):
            raise ValueError("incomplete frozen validity output")
        annotated = [{**row, GATE_KEY: indexed[index]} for index, row in enumerate(rows)]
        gates = [checked_gate(row) for row in annotated]
        print("[validity_rzero][frozen_validity] " + json.dumps({
            "phase": phase, "model": model, "questions": len(rows),
            "invalid": sum(g["validity_decision"] == "INVALID" for g in gates),
            "gpu_ids": gpu_ids, "artifacts": str(work),
        }), flush=True)
        return annotated
    except BaseException:
        for _, log in outputs:
            print(f"[frozen_validity] {log}\n{tail_text(log)}", file=sys.stderr, flush=True)
        raise
    finally:
        terminate_process_groups(processes)
        for handle in handles:
            handle.close()
        pid_file.write_text("", encoding="utf-8")
        for sig, handler in old_handlers.items():
            signal.signal(sig, handler)
        wait_gpus_released(tuple(gpu_ids), int(os.getenv("VALIDITY_RZERO_GPU_RELEASE_TIMEOUT", "120")))


def annotate_phase_a(rows: list[dict]) -> list[dict]:
    from .service_handoff import SolverServiceConfig, semantic_gpu_handoff
    positions = [i for i, row in enumerate(rows) if row.get("question") and row.get("answer")]
    if not positions:
        return rows
    config = SolverServiceConfig.from_environment()
    with semantic_gpu_handoff(config):
        annotated = run_workers([rows[i] for i in positions], list(config.gpu_ids), "a")
    output = list(rows)
    for index, row in zip(positions, annotated):
        output[index] = row
    return output


def phase_b_prepass(save_name: str) -> None:
    gpu_ids = os.getenv("QUESTION_GPU_IDS", "0,1,2,3").split(",")
    root = Path(os.environ["STORAGE_PATH"]) / "generated_question"
    paths = [root / f"{save_name}_{i}.json" for i in range(len(gpu_ids))]
    shards = [json.loads(path.read_text()) for path in paths]
    positions = [(s, i) for s, rows in enumerate(shards) for i, row in enumerate(rows)
                 if row.get("score") == 0]
    rows = [shards[s][i] for s, i in positions]
    if rows:
        annotated = run_workers(rows, gpu_ids, "b")
        for (s, i), row in zip(positions, annotated):
            shards[s][i] = row
    for path, rows in zip(paths, shards):
        temporary = path.with_suffix(".frozen.tmp")
        temporary.write_text(json.dumps(rows), encoding="utf-8")
        temporary.replace(path)


def worker(args) -> None:
    import vllm
    from transformers import AutoTokenizer
    from jinja2 import Template
    rows = json.loads(Path(args.worker_input).read_text())
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    options = {"seed": args.seed} if args.phase == "b" else {}
    model = vllm.LLM(model=args.model, tokenizer=args.model,
                     gpu_memory_utilization=0.85 if args.phase == "b" else 0.8,
                     **options)
    template_path = Path(os.getenv("VALIDITY_RZERO_PROMPT", str(Path(__file__).parents[1] / "validity_rl" / "validity_solver.jinja")))
    template = Template(template_path.read_text().strip())
    prompts = []
    for row in rows:
        chat = [{"role": "user", "content": template.render(content=row["question"]).strip()}]
        if tokenizer.chat_template:
            prompt = tokenizer.apply_chat_template(chat, tokenize=False, add_generation_prompt=True, add_special_tokens=True)
        else:
            prompt = f"user: {chat[0]['content']}"
        prompts.append(prompt)
    params = vllm.SamplingParams(
        n=9, max_tokens=int(os.getenv("VLLM_SERVER_MAX_TOKENS", "4096")) if args.phase == "a" else 4096,
        temperature=1.0, top_p=1.0, top_k=40, stop_token_ids=[tokenizer.eos_token_id])
    batch_size = int(os.getenv("VLLM_SERVER_BATCH_SIZE", "0")) if args.phase == "a" else 0
    batch_size = batch_size if batch_size > 0 else max(1, len(prompts))
    responses = []
    for start in range(0, len(prompts), batch_size):
        responses.extend(model.generate(prompts[start:start + batch_size], sampling_params=params, use_tqdm=True))
    if len(responses) != len(rows):
        raise ValueError("frozen validity response count mismatch")
    output = [{**row, "model": args.model, "responses": [out.text for out in response.outputs]}
              for row, response in zip(rows, responses)]
    Path(args.worker_output).write_text(json.dumps(output), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--save-name")
    parser.add_argument("--worker-input")
    parser.add_argument("--worker-output")
    parser.add_argument("--model")
    parser.add_argument("--phase", choices=["a", "b"])
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    if args.worker_input:
        worker(args)
    else:
        if not enabled():
            raise ValueError("frozen validity prepass requires explicit frozen mode")
        phase_b_prepass(args.save_name)
