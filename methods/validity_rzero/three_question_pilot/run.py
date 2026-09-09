"""Isolated generation and production-equivalent filtering; no training or upload."""
from __future__ import annotations

import argparse
from collections import Counter
import importlib.metadata
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from methods.validity_rzero.three_question_pilot.core import (
    REPO, METHOD, PROVENANCE, atomic_json, atomic_jsonl, distribution, read_jsonl,
    resolve_model, sha, three_messages,
)
from methods.validity_rzero.prepare_solver_dataset import passes_rzero_filter

STORAGE = Path("/engrfs/project/jiaxinh/jinyuan/R-zero-storage")
RUN = "qwen3_4b_validity_rzero_semantic_novelty_gate_k8_4gpu_v1"


def arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questioner", type=Path, default=STORAGE / "models" / (RUN + "_questioner_v4"))
    parser.add_argument("--solver", type=Path, default=STORAGE / "models" / (RUN + "_solver_v3"))
    parser.add_argument("--questioner-step", type=int, default=5)
    parser.add_argument("--solver-step", type=int, default=15)
    parser.add_argument("--gpu-ids", default="0,1,2,3")
    parser.add_argument("--requests-per-gpu", type=int, default=833)
    parser.add_argument("--output-dir", type=Path,
                        default=STORAGE / "rzero_runs/novelty_k8_q4_s3_three_questions_v1")
    parser.add_argument("--eval-timeout-seconds", type=int, default=14400)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="Print protocol and prompt without loading models or writing files")
    args = parser.parse_args()
    args.gpus = [g.strip() for g in args.gpu_ids.split(",")]
    if not args.gpus or any(not g.isdigit() for g in args.gpus) or len(set(args.gpus)) != len(args.gpus):
        parser.error("GPU IDs must be distinct nonnegative integers")
    if min(args.requests_per_gpu, args.eval_timeout_seconds, args.questioner_step, args.solver_step) <= 0:
        parser.error("counts, checkpoint steps and timeout must be positive")
    args.output_dir = args.output_dir.expanduser().resolve()
    return args


def protocol(args):
    dependencies = [REPO / "question_generate/question_generate.py",
                    REPO / "methods/validity_rzero/gating.py",
                    REPO / "methods/validity_rl/validity_reward.py",
                    REPO / "methods/validity_rl/validity_solver.jinja",
                    REPO / "methods/validity_rzero/prepare_solver_dataset.py"]
    dependencies += sorted(METHOD.glob("*.py"))
    return {"protocol": "frozen-q4-s3-three-questions-v1", "gpu_ids": args.gpus,
            "requests_per_gpu": args.requests_per_gpu,
            "total_requests": len(args.gpus) * args.requests_per_gpu,
            "maximum_questions": len(args.gpus) * args.requests_per_gpu * 3,
            "messages": three_messages(),
            "generation": {"max_tokens": 4096, "temperature": 1.0, "top_p": 0.95,
                           "n": 1, "seed": "shard index (0,1,2,3)", "stop": "tokenizer.eos_token_id"},
            "evaluation": {"validity_votes": 9, "invalid_threshold": 5, "math_votes": 9,
                           "max_tokens": 4096, "temperature": 1.0, "top_p": 1.0, "top_k": 40,
                           "min_score": 0.3, "max_score": 0.8,
                           "evaluator_snapshot_from": "b2e2d24", "timeout_seconds": args.eval_timeout_seconds},
            "training": False, "upload": False, "terra_replay": False,
            "source_sha256": {str(p.relative_to(REPO)): sha(p) for p in dependencies}}


def artifact_paths(root, phase, shard):
    if phase == "generate":
        return [root / "generation" / f"shard_{shard}_{name}" for name in
                ("raw.jsonl", "candidates.json", "prompt.json")]
    return [root / "workspace/generated_question" / f"three_questions_{shard}_results.json"]


def completed(root, phase, shard):
    receipt = root / "receipts" / f"{phase}_{shard}.json"
    if not receipt.is_file():
        return False
    expected = json.loads(receipt.read_text())
    paths = artifact_paths(root, phase, shard)
    return expected == {str(p.relative_to(root)): sha(p) for p in paths if p.is_file()} and all(p.is_file() for p in paths)


def mark_completed(root, phase, shard):
    paths = artifact_paths(root, phase, shard)
    # Reject missing/invalid JSON artifacts even when a worker returned zero.
    for path in paths:
        read_jsonl(path) if path.suffix == ".jsonl" else json.loads(path.read_text())
    atomic_json(root / "receipts" / f"{phase}_{shard}.json",
                {str(p.relative_to(root)): sha(p) for p in paths})


def stop_workers(workers):
    for proc, _, _ in workers:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    deadline = time.monotonic() + 5
    while any(p.poll() is None for p, _, _ in workers) and time.monotonic() < deadline:
        time.sleep(0.1)
    for proc, _, _ in workers:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        proc.wait()


def run_phase(args, phase, manifest):
    root, workers, streams = args.output_dir, [], []
    base_env = os.environ.copy()
    # Override inherited experiment toggles inside child processes only.
    for key in list(base_env):
        if key.startswith("VALIDITY_RZERO_") or key.startswith("TERRA_REPLAY_"):
            del base_env[key]
    base_env.update(VALIDITY_RZERO_ENABLED="1", VALIDITY_RZERO_DOMAIN_MODE="none",
                    VALIDITY_RZERO_PROMPT=str(REPO / "methods/validity_rl/validity_solver.jinja"),
                    STORAGE_PATH=str(root / "workspace"), VLLM_DISABLE_COMPILE_CACHE="1",
                    PYTHONPATH=str(REPO) + os.pathsep + base_env.get("PYTHONPATH", ""))
    try:
        for shard, gpu in enumerate(args.gpus):
            if args.resume and completed(root, phase, shard):
                print(f"[resume] {phase} shard {shard} complete", flush=True)
                continue
            if phase == "generate":
                # Any recomputed candidate shard invalidates its downstream evaluator receipt.
                (root / "receipts" / f"evaluate_{shard}.json").unlink(missing_ok=True)
                cmd = [sys.executable, "-m", "methods.validity_rzero.three_question_pilot.generate",
                       "--model", manifest["questioner"], "--output-dir", str(root),
                       "--shard", str(shard), "--requests", str(args.requests_per_gpu)]
            else:
                candidates = json.loads((root / "generation" / f"shard_{shard}_candidates.json").read_text())
                # The frozen evaluator deletes only this disposable input copy.
                atomic_json(root / "workspace/generated_question" / f"three_questions_{shard}.json", candidates)
                result = artifact_paths(root, phase, shard)[0]
                result.unlink(missing_ok=True)
                cmd = [sys.executable, str(METHOD / "evaluate_snapshot.py"),
                       "--model", manifest["solver"], "--suffix", str(shard), "--save_name", "three_questions"]
            log = root / "logs" / f"{phase}_{shard}.log"
            log.parent.mkdir(parents=True, exist_ok=True)
            stream = log.open("a")
            streams.append(stream)
            stream.write(f"\nSTART {time.strftime('%Y-%m-%d %H:%M:%S')} GPU={gpu}\n")
            stream.flush()
            proc = subprocess.Popen(cmd, cwd=REPO, env={**base_env, "CUDA_VISIBLE_DEVICES": gpu},
                                    stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
            workers.append((proc, shard, log))
            print(f"[{phase}] GPU {gpu}, shard {shard}, log={log}", flush=True)
        pending = list(workers)
        started = time.monotonic()
        while pending:
            for worker in pending[:]:
                proc, shard, log = worker
                code = proc.poll()
                if code is None:
                    continue
                if code != 0:
                    raise RuntimeError(f"{phase} shard {shard} failed (exit {code}); inspect {log}")
                mark_completed(root, phase, shard)
                pending.remove(worker)
                print(f"[{phase}] shard {shard} complete", flush=True)
            if phase == "evaluate" and pending and time.monotonic() - started > args.eval_timeout_seconds:
                raise TimeoutError(f"evaluation exceeded {args.eval_timeout_seconds}s; inspect {root / 'logs'}")
            if pending:
                time.sleep(0.25)
    except BaseException:
        stop_workers(workers)
        raise
    finally:
        for stream in streams:
            stream.close()


def collect(root, shards):
    candidates, evaluated, raw = [], [], []
    for shard in range(shards):
        candidates += json.loads((root / "generation" / f"shard_{shard}_candidates.json").read_text())
        raw += read_jsonl(root / "generation" / f"shard_{shard}_raw.jsonl")
        evaluated += json.loads(artifact_paths(root, "evaluate", shard)[0].read_text())
    by_id = {r["sample_id"]: r for r in candidates}
    if len(by_id) != len(candidates):
        raise ValueError("duplicate sample IDs")
    evaluated_by_id = {r["sample_id"]: r for r in evaluated}
    if len(evaluated_by_id) != len(evaluated) or not set(evaluated_by_id) <= set(by_id):
        raise ValueError("invalid evaluator provenance")
    for row in evaluated:
        source = by_id[row["sample_id"]]
        if row["question"] != source["question"] or any(row[k] != source[k] for k in PROVENANCE):
            raise ValueError("evaluator changed question or provenance")
        row["questioner_answer"] = source["answer"]
        row["passed_rzero_filter"] = passes_rzero_filter(row, 0.3, 0.8)
    retained = [r for r in evaluated if r["passed_rzero_filter"]]
    skipped = [{**r, "status": "omitted_by_original_evaluator",
                "note": "Original evaluator skips missing math answers, certain question/answer forms, or grading exceptions; see shard log."}
               for r in candidates if r["sample_id"] not in evaluated_by_id]
    folder = root / "datasets"
    atomic_jsonl(folder / "candidates.jsonl", candidates)
    atomic_jsonl(folder / "round_4_phase_b.jsonl", evaluated)
    atomic_jsonl(folder / "evaluator_skipped.jsonl", skipped)
    atomic_json(folder / "round_4.json", retained)
    atomic_jsonl(folder / "solver_train_rzero.jsonl", [
        {"problem": r["question"], "answer": r["answer"], "score": r["score"], "source": "rzero",
         **{k: r[k] for k in PROVENANCE}} for r in retained])
    report = {"request_count": len(raw), "max_question_count": len(raw) * 3,
              "parsed_question_count": len(candidates), "evaluated_row_count": len(evaluated),
              "omitted_by_original_evaluator_count": len(skipped), "retained_count": len(retained),
              "invalid_count": sum(r.get("discarded_by_validity", False) for r in evaluated),
              "truncated_request_count": sum(r["finish_reason"] == "length" for r in raw),
              "parsed_per_request_histogram": dict(Counter(str(r["parsed_count"]) for r in raw)),
              "extra_blocks_ignored": sum(r["extra_blocks_ignored"] for r in raw),
              "positions": {}}
    for position in (None, 1, 2, 3):
        select = lambda rows: [r for r in rows if position is None or r["question_position"] == position]
        report["positions"][str(position) if position else "all"] = {
            "generated": distribution(select(candidates)), "retained": distribution(select(retained)),
            "evaluated_count": len(select(evaluated)), "evaluator_skipped_count": len(select(skipped))}
    atomic_json(root / "summary.json", report)
    lines = ["# Frozen Q4 + S3: three questions per request", "",
             "Same production validity/math scoring and [0.3, 0.8] filter. No training, upload, Terra mixing, dedup or novelty judging.", "",
             f"Requests: {len(raw)}; parsed questions: {len(candidates)}; evaluated rows: {len(evaluated)}; retained: {len(retained)}.",
             f"Truncated requests: {report['truncated_request_count']}; evaluator omissions: {len(skipped)}.", "",
             "| Position | Parsed | Retained | Retained exact unique | Retained numeric-template unique |",
             "|---|---:|---:|---:|---:|"]
    for key, value in report["positions"].items():
        lines.append(f"| {key} | {value['generated']['count']} | {value['retained']['count']} | "
                     f"{value['retained']['exact_unique_count']} | {value['retained']['numeric_template_unique_count']} |")
    lines += ["", "Numeric normalization is a text proxy, not semantic diversity. These ratios are not an equal-sample-size comparison with historical P0.",
              "Compare datasets/round_4.json with the original K8 round-4 R-Zero-only retained data. Exclude Terra replay rows from both sides.",
              "Full raw completions and prompts are in generation/. Individual IDs and positions survive filtering; omitted rows are separately recorded."]
    (root / "report.md").write_text("\n".join(lines) + "\n")
    return report


def main():
    args = arguments()
    manifest = protocol(args)
    if args.dry_run:
        print(json.dumps({**manifest, "questioner_root": str(args.questioner), "questioner_step": args.questioner_step,
                          "solver_root": str(args.solver), "solver_step": args.solver_step,
                          "output_dir": str(args.output_dir)}, ensure_ascii=False, indent=2))
        return
    manifest["questioner"], manifest["questioner_identity"] = resolve_model(args.questioner, args.questioner_step)
    manifest["solver"], manifest["solver_identity"] = resolve_model(args.solver, args.solver_step)
    manifest["packages"] = {name: importlib.metadata.version(name) for name in ("vllm", "transformers", "torch", "mathruler", "stopit")}
    root = args.output_dir
    # Prevent two simultaneous invocations from reusing or overwriting this experiment.
    root.parent.mkdir(parents=True, exist_ok=True)
    import fcntl
    with (root.parent / (root.name + ".lock")).open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        path = root / "manifest.json"
        if path.exists():
            if not args.resume:
                raise FileExistsError(f"Existing experiment: {root}; use --resume or a new output directory")
            if json.loads(path.read_text()) != manifest:
                raise ValueError("Resume configuration/model/source/package mismatch; use a new output directory")
        else:
            if root.exists() and any(root.iterdir()):
                raise FileExistsError(f"Nonempty output directory without manifest: {root}")
            atomic_json(path, manifest)
        run_phase(args, "generate", manifest)
        run_phase(args, "evaluate", manifest)
        report = collect(root, len(args.gpus))
        atomic_json(root / "_SUCCESS.json", {"manifest_sha256": sha(path), "retained_count": report["retained_count"]})
        print(f"Completed: {root}\nRetained: {report['retained_count']}\nReport: {root / 'report.md'}", flush=True)


if __name__ == "__main__":
    main()
