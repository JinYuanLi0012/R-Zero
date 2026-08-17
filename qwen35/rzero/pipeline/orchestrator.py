"""Five-round, manifest-driven R-Zero orchestration."""

from __future__ import annotations

import argparse
import json
import os
import signal
import shutil
import subprocess
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from qwen35.rzero.config import load_config
from qwen35.rzero.official_verl import build_pythonpath, verl_source_root
from qwen35.rzero.pipeline.state import Artifact, RunState, StateError, atomic_write_json, canonical_hash, validate_artifact


def _process_group_alive(process_group: int) -> bool:
    try:
        os.killpg(process_group, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _terminate_process_groups(processes: list[subprocess.Popen], timeout: float = 30) -> None:
    """Stop service parents and spawned vLLM EngineCore children together."""
    groups = {process.pid: process for process in processes}
    for process_group in groups:
        try:
            os.killpg(process_group, signal.SIGTERM)
        except ProcessLookupError:
            pass

    deadline = time.monotonic() + timeout
    remaining = {process_group for process_group in groups if _process_group_alive(process_group)}
    while remaining and time.monotonic() < deadline:
        for process in groups.values():
            process.poll()
        time.sleep(0.2)
        remaining = {process_group for process_group in remaining if _process_group_alive(process_group)}

    for process_group in remaining:
        try:
            os.killpg(process_group, signal.SIGKILL)
        except ProcessLookupError:
            pass

    for process in groups.values():
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


@dataclass
class Stage:
    key: str
    artifacts: list[Artifact]
    action: Callable[[], None]
    description: str
    inputs: list[Artifact] | None = None


class Pipeline:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.config = load_config(args.config)
        snapshot = {key: value for key, value in self.config.items() if not key.startswith("_")}
        self.fingerprint = canonical_hash(snapshot)
        self.run_dir = args.run_dir.expanduser().resolve()
        self.repo_root = Path(__file__).resolve().parents[3]
        self.verl_root = verl_source_root(self.config["runtime"]["verl_source_root"])
        self.state = RunState(self.run_dir, self.fingerprint)
        self.force_fresh_stages: set[str] = set()
        self.resume_existing = bool(args.resume or args.from_stage)
        self.python = sys.executable
        self.base_model = self.run_dir / "models" / "base"
        self.seed_data = self.run_dir / "data" / "seed"

    def _run(
        self,
        command: list[str],
        log_path: Path,
        env: dict[str, str] | None = None,
        cwd: Path | None = None,
    ) -> None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        merged_env = os.environ.copy()
        if env:
            merged_env.update(env)
        merged_env["VERL_SOURCE_ROOT"] = str(self.verl_root)
        merged_env["PYTHONPATH"] = build_pythonpath(self.verl_root, self.repo_root, merged_env.get("PYTHONPATH"))
        with log_path.open("a", encoding="utf-8") as log:
            log.write(f"$ {' '.join(command)}\n")
            log.flush()
            subprocess.run(command, cwd=cwd or self.repo_root, env=merged_env, stdout=log, stderr=subprocess.STDOUT, check=True)

    def _round_dir(self, round_number: int) -> Path:
        return self.run_dir / f"round_{round_number:02d}"

    def _previous_models(self, round_number: int) -> tuple[Path, Path]:
        if round_number == 1:
            return self.base_model, self.base_model
        previous = self._round_dir(round_number - 1)
        return previous / "questioner" / "export", previous / "solver" / "export"

    def _checkpoint_actor(self, root: Path, step: int) -> Path:
        candidates = [root / f"global_step_{step}" / "actor", root / f"global_steps_{step}" / "actor"]
        for candidate in candidates:
            if candidate.is_dir():
                return candidate
        # Return canonical path for dry-run/artifact declaration.
        return candidates[0]

    def _wait_for_service_receipt(
        self, receipt: Path, process: subprocess.Popen, timeout: float = 900
    ) -> str:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError(f"Solver service exited early with {process.returncode}")
            if receipt.is_file():
                try:
                    payload = json.loads(receipt.read_text(encoding="utf-8"))
                    host = str(payload["host"])
                    port = int(payload["port"])
                    if host != "127.0.0.1" or not 0 < port < 65536:
                        raise ValueError("invalid service address")
                    endpoint = f"http://{host}:{port}"
                    with urllib.request.urlopen(f"{endpoint}/health", timeout=2) as response:
                        if response.status == 200:
                            return endpoint
                except Exception:
                    pass
            time.sleep(2)
        raise TimeoutError(f"Solver service did not become healthy; receipt={receipt}")

    def _train_questioner(
        self, round_number: int, questioner_model: Path, solver_model: Path, stage_key: str
    ) -> None:
        round_dir = self._round_dir(round_number)
        hardware = self.config["hardware"]
        samples = self.config["algorithm"]["questioner_solver_samples"]
        processes: list[tuple[subprocess.Popen, object]] = []
        endpoints: list[str] = []
        try:
            for gpu in hardware["questioner_solver_gpus"]:
                log_path = round_dir / "logs" / f"solver_service_gpu{gpu}.log"
                port_file = round_dir / "logs" / f"solver_service_gpu{gpu}.{os.getpid()}.{time.time_ns()}.json"
                log_path.parent.mkdir(parents=True, exist_ok=True)
                handle = log_path.open("a", encoding="utf-8")
                env = os.environ.copy()
                env.update(
                    {
                        "CUDA_VISIBLE_DEVICES": str(gpu),
                        "PYTHONPATH": build_pythonpath(self.verl_root, self.repo_root, env.get("PYTHONPATH")),
                        "VLLM_USE_V1": "1",
                    }
                )
                process = subprocess.Popen(
                    [
                        self.python,
                        "-m",
                        "qwen35.rzero.solver_service",
                        "--model",
                        str(solver_model),
                        "--port",
                        "0",
                        "--port-file",
                        str(port_file),
                        "--samples",
                        str(samples),
                    ],
                    cwd=self.verl_root,
                    env=env,
                    stdout=handle,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
                processes.append((process, handle))
                endpoints.append(self._wait_for_service_receipt(port_file, process))

            command = [
                self.python,
                "-m",
                "qwen35.rzero.train_grpo",
                "--role",
                "questioner",
                "--config",
                self.config["_config_path"],
                "--model",
                str(questioner_model),
                "--train-file",
                str(self.seed_data / "questioner_train.parquet"),
                "--val-file",
                str(self.seed_data / "questioner_val.parquet"),
                "--output-dir",
                str(round_dir / "questioner" / "checkpoints"),
                "--experiment-name",
                f"round_{round_number:02d}_questioner",
            ]
            if self.resume_existing and stage_key not in self.force_fresh_stages:
                command.append("--resume")
            self._run(
                command,
                round_dir / "logs" / "questioner_train.log",
                env={
                    "CUDA_VISIBLE_DEVICES": ",".join(map(str, hardware["questioner_training_gpus"])),
                    "RZERO_SOLVER_ENDPOINTS": ",".join(endpoints),
                    "VLLM_USE_V1": "1",
                },
                cwd=self.verl_root,
            )
        finally:
            _terminate_process_groups([process for process, _ in processes])
            for _, handle in processes:
                handle.close()

    def _train_solver(self, round_number: int, solver_model: Path, stage_key: str) -> None:
        round_dir = self._round_dir(round_number)
        command = [
            self.python,
            "-m",
            "qwen35.rzero.train_grpo",
            "--role",
            "solver",
            "--config",
            self.config["_config_path"],
            "--model",
            str(solver_model),
            "--train-file",
            str(round_dir / "dataset" / "train.parquet"),
            "--val-file",
            str(self.seed_data / "solver_val.parquet"),
            "--output-dir",
            str(round_dir / "solver" / "checkpoints"),
            "--experiment-name",
            f"round_{round_number:02d}_solver",
        ]
        if self.resume_existing and stage_key not in self.force_fresh_stages:
            command.append("--resume")
        self._run(
            command,
            round_dir / "logs" / "solver_train.log",
            env={"CUDA_VISIBLE_DEVICES": "0,1,2,3", "VLLM_USE_V1": "1"},
            cwd=self.verl_root,
        )

    def _export(self, checkpoint_root: Path, step: int, target: Path, log: Path) -> None:
        temporary = target.with_name(f".{target.name}.tmp")
        if temporary.exists():
            shutil.rmtree(temporary)
        command = [
            self.python,
            "-m",
            "qwen35.rzero.export_model",
            "--checkpoint-root",
            str(checkpoint_root),
            "--step",
            str(step),
            "--target-dir",
            str(temporary),
        ]
        self._run(command, log, cwd=self.verl_root)
        backup = target.with_name(f".{target.name}.previous")
        if backup.exists():
            shutil.rmtree(backup)
        if target.exists():
            os.replace(target, backup)
        os.replace(temporary, target)
        if backup.exists():
            shutil.rmtree(backup)

    def _skip_benchmark(self, target: Path) -> None:
        target.mkdir(parents=True, exist_ok=True)
        (target / "skipped.json").write_text(
            json.dumps({"status": "skipped", "profile": self.config.get("profile")}, indent=2) + "\n",
            encoding="utf-8",
        )

    def stages(self) -> list[Stage]:
        cfg = self.config
        stages: list[Stage] = []
        stages.append(
            Stage(
                "resolve_model",
                [Artifact(self.base_model, "model"), Artifact(self.base_model / "RZERO_MODEL_REVISION", "file")],
                lambda: self._run(
                    [
                        self.python,
                        "-m",
                        "qwen35.rzero.resolve_model",
                        "--repo-id",
                        cfg["model"]["id"],
                        "--revision",
                        cfg["model"]["revision"],
                        "--output-dir",
                        str(self.base_model),
                    ],
                    self.run_dir / "logs" / "resolve_model.log",
                ),
                "resolve immutable Qwen3.5 checkpoint",
            )
        )
        seed_artifacts = [
            Artifact(self.seed_data / "questioner_train.parquet"),
            Artifact(self.seed_data / "questioner_val.parquet"),
            Artifact(self.seed_data / "solver_val.parquet"),
            Artifact(self.seed_data / "seed_data.json", "json"),
        ]
        stages.append(
            Stage(
                "prepare_seed_data",
                seed_artifacts,
                lambda: self._run(
                    [
                        self.python,
                        "-m",
                        "qwen35.rzero.data",
                        "--dataset-id",
                        cfg["data"]["seed_dataset"],
                        "--train-split",
                        cfg["data"]["seed_train_split"],
                        "--val-split",
                        cfg["data"]["seed_val_split"],
                        "--output-dir",
                        str(self.seed_data),
                    ],
                    self.run_dir / "logs" / "prepare_seed_data.log",
                ),
                "prepare official verl Parquet inputs",
            )
        )
        smoke_output = self.run_dir / "environment.json"
        stages.append(
            Stage(
                "environment_smoke",
                [Artifact(smoke_output, "json")],
                lambda: self._run(
                    [
                        self.python,
                        "-m",
                        "qwen35.rzero.validation.environment",
                        "--model",
                        str(self.base_model),
                        "--output",
                        str(smoke_output),
                        "--expected-verl-root",
                        str(self.verl_root),
                        "--expected-verl-ref",
                        cfg["runtime"]["verl_ref"],
                        "--expected-vllm-version",
                        cfg["runtime"]["vllm"],
                        "--expected-transformers-version",
                        cfg["runtime"]["transformers"],
                        "--expected-torch-version",
                        cfg["runtime"]["torch"],
                        "--expected-cuda-version",
                        cfg["runtime"]["cuda"],
                        "--load-vllm",
                    ],
                    self.run_dir / "logs" / "environment_smoke.log",
                    env={"CUDA_VISIBLE_DEVICES": "0,1,2,3"},
                    cwd=self.verl_root,
                ),
                "validate qwen3_5, four GPUs and vLLM text-only load",
                [Artifact(self.base_model, "model")],
            )
        )

        for round_number in range(1, cfg["algorithm"]["rounds"] + 1):
            round_dir = self._round_dir(round_number)
            questioner_model, solver_model = self._previous_models(round_number)
            q_checkpoints = round_dir / "questioner" / "checkpoints"
            q_actor = self._checkpoint_actor(q_checkpoints, cfg["algorithm"]["questioner_steps"])
            q_export = round_dir / "questioner" / "export"
            s_checkpoints = round_dir / "solver" / "checkpoints"
            s_actor = self._checkpoint_actor(s_checkpoints, cfg["algorithm"]["solver_steps"])
            s_export = round_dir / "solver" / "export"
            prefix = f"round_{round_number:02d}"

            q_stage_key = f"{prefix}.questioner_train"
            stages.append(Stage(q_stage_key, [Artifact(q_actor, "checkpoint")], lambda n=round_number, q=questioner_model, s=solver_model, key=q_stage_key: self._train_questioner(n, q, s, key), "train Questioner with 2+2 GPU topology", [Artifact(questioner_model, "model"), Artifact(solver_model, "model"), Artifact(self.seed_data / "questioner_train.parquet")]))
            stages.append(Stage(f"{prefix}.questioner_export", [Artifact(q_export, "model")], lambda root=q_checkpoints, target=q_export, rd=round_dir: self._export(root, cfg["algorithm"]["questioner_steps"], target, rd / "logs" / "questioner_export.log"), "merge Questioner FSDP checkpoint", [Artifact(q_actor, "checkpoint")]))

            for shard in range(cfg["generation"]["shards"]):
                output = round_dir / "generated" / f"shard_{shard}.json"
                stages.append(
                    Stage(
                        f"{prefix}.generate.{shard}",
                        [Artifact(output, "json", cfg["generation"]["samples_per_shard"])],
                        lambda shard=shard, output=output, model=q_export, rd=round_dir: self._run(
                            [
                                self.python, "-m", "qwen35.rzero.generate_candidates",
                                "--model", str(model), "--output", str(output),
                                "--samples", str(cfg["generation"]["samples_per_shard"]),
                                "--seed", str(shard),
                                "--temperature", str(cfg["generation"]["temperature"]),
                                "--top-p", str(cfg["generation"]["top_p"]),
                                "--max-tokens", str(cfg["generation"]["max_tokens"]),
                            ],
                            rd / "logs" / f"generate_{shard}.log",
                            env={"CUDA_VISIBLE_DEVICES": str(shard), "VLLM_USE_V1": "1"},
                        ),
                        f"generate candidate shard {shard}",
                        [Artifact(q_export, "model")],
                    )
                )
            for shard in range(cfg["generation"]["shards"]):
                source = round_dir / "generated" / f"shard_{shard}.json"
                output = round_dir / "scored" / f"shard_{shard}.json"
                stages.append(
                    Stage(
                        f"{prefix}.evaluate.{shard}",
                        [Artifact(output, "json")],
                        lambda shard=shard, source=source, output=output, model=solver_model, rd=round_dir: self._run(
                            [
                                self.python, "-m", "qwen35.rzero.evaluate_candidates",
                                "--model", str(model), "--input", str(source), "--output", str(output),
                                "--samples", str(cfg["algorithm"]["candidate_vote_samples"]),
                                "--seed", str(shard),
                            ],
                            rd / "logs" / f"evaluate_{shard}.log",
                            env={"CUDA_VISIBLE_DEVICES": str(shard), "VLLM_USE_V1": "1"},
                        ),
                        f"score candidate shard {shard}",
                        [Artifact(source, "json", cfg["generation"]["samples_per_shard"]), Artifact(solver_model, "model")],
                    )
                )

            dataset = round_dir / "dataset" / "train.parquet"
            metadata = round_dir / "dataset" / "curation.json"
            curate_command = [self.python, "-m", "qwen35.rzero.curate_dataset"]
            for shard in range(cfg["generation"]["shards"]):
                curate_command.extend(["--input", str(round_dir / "scored" / f"shard_{shard}.json")])
            curate_command.extend([
                "--output", str(dataset), "--metadata", str(metadata),
                "--min-score", str(cfg["algorithm"]["difficulty_min"]),
                "--max-score", str(cfg["algorithm"]["difficulty_max"]),
                "--minimum-rows", str(cfg["algorithm"]["solver_prompt_batch_size"]),
            ])
            if cfg.get("profile", "formal") != "formal":
                curate_command.append("--repeat-to-minimum")
            if cfg.get("curation", {}).get("deduplicate_questions", False):
                curate_command.append("--deduplicate-questions")
            if cfg.get("curation", {}).get("allow_smoke_fallback", False):
                curate_command.extend(["--fallback", str(self.seed_data / "solver_val.parquet")])
            scored_inputs = [Artifact(round_dir / "scored" / f"shard_{shard}.json", "json") for shard in range(cfg["generation"]["shards"])]
            stages.append(Stage(f"{prefix}.curate", [Artifact(dataset), Artifact(metadata, "json")], lambda command=curate_command, rd=round_dir: self._run(command, rd / "logs" / "curate.log"), "merge and filter local Parquet while preserving released ordering", scored_inputs))
            s_stage_key = f"{prefix}.solver_train"
            stages.append(Stage(s_stage_key, [Artifact(s_actor, "checkpoint")], lambda n=round_number, model=solver_model, key=s_stage_key: self._train_solver(n, model, key), "train Solver on all four GPUs", [Artifact(dataset), Artifact(solver_model, "model"), Artifact(self.seed_data / "solver_val.parquet")]))
            stages.append(Stage(f"{prefix}.solver_export", [Artifact(s_export, "model")], lambda root=s_checkpoints, target=s_export, rd=round_dir: self._export(root, cfg["algorithm"]["solver_steps"], target, rd / "logs" / "solver_export.log"), "merge Solver FSDP checkpoint", [Artifact(s_actor, "checkpoint")]))
            benchmark = round_dir / "evaluation"
            benchmark_enabled = cfg.get("benchmark", {}).get("enabled", True)
            benchmark_action = (
                (lambda model=s_export, target=benchmark, rd=round_dir: self._run([self.python, "-m", "qwen35.rzero.run_benchmark", "--repo-root", str(self.repo_root), "--model", str(model), "--output-dir", str(target)], rd / "logs" / "benchmark.log", env={"CUDA_VISIBLE_DEVICES": "0,1,2,3", "VLLM_USE_V1": "1"}))
                if benchmark_enabled
                else (lambda target=benchmark: self._skip_benchmark(target))
            )
            benchmark_description = (
                "run unchanged upstream evaluation in isolated directory"
                if benchmark_enabled
                else "record deferred benchmark skip marker"
            )
            stages.append(Stage(f"{prefix}.benchmark", [Artifact(benchmark, "directory")], benchmark_action, benchmark_description, [Artifact(s_export, "model")]))
        return stages

    def _prepare_recompute(self, stages: list[Stage], first_key: str) -> None:
        keys = [stage.key for stage in stages]
        if first_key not in keys:
            raise StateError(f"unknown --from-stage {first_key!r}")
        affected = stages[keys.index(first_key) :]
        training_stages = [stage for stage in affected if stage.key.endswith((".questioner_train", ".solver_train"))]
        self.force_fresh_stages = {stage.key for stage in training_stages}

        event_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{time.time_ns()}"
        backup_root = self.run_dir / "recompute_backups" / event_id
        moved: list[dict[str, str]] = []
        for stage in training_stages:
            checkpoint_artifact = next((item for item in stage.artifacts if item.kind == "checkpoint"), None)
            if checkpoint_artifact is None:
                raise StateError(f"training stage has no checkpoint artifact: {stage.key}")
            checkpoint_root = checkpoint_artifact.path.parents[1]
            if not checkpoint_root.exists():
                continue
            destination = backup_root / stage.key / "checkpoints"
            destination.parent.mkdir(parents=True, exist_ok=True)
            os.replace(checkpoint_root, destination)
            moved.append({"stage": stage.key, "source": str(checkpoint_root), "backup": str(destination)})

        atomic_write_json(
            self.run_dir / "manifests" / "recomputations" / f"{event_id}.json",
            {
                "schema_version": 1,
                "requested_from_stage": first_key,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "forced_fresh_training_stages": sorted(self.force_fresh_stages),
                "moved_checkpoint_roots": moved,
            },
        )

    def run(self) -> None:
        stages = self.stages()
        selected_round = self.args.round
        if selected_round and self.args.from_stage:
            raise StateError("--round cannot be combined with --from-stage because downstream lineage would be stale")
        if selected_round:
            allowed_prefix = f"round_{selected_round:02d}."
            stages = [stage for stage in stages if not stage.key.startswith("round_") or stage.key.startswith(allowed_prefix)]
        keys = [stage.key for stage in stages]

        if self.args.dry_run:
            forced = set(keys[keys.index(self.args.from_stage) :]) if self.args.from_stage in keys else set()
            if self.args.from_stage and not forced:
                raise StateError(f"unknown --from-stage {self.args.from_stage!r}")
            for stage in stages:
                status = "SKIP" if stage.key not in forced and self.state.is_complete(stage.key, stage.artifacts, stage.inputs) else "RUN "
                print(f"{status} {stage.key:32} {stage.description}")
            return

        self.state.initialize({key: value for key, value in self.config.items() if not key.startswith("_")})
        if self.args.from_stage:
            self._prepare_recompute(stages, self.args.from_stage)
            self.state.invalidate_from(keys, self.args.from_stage)
        elif not self.args.resume and any(self.state.stage_manifest(key).exists() for key in keys):
            raise StateError("existing stage manifests found; pass --resume or use a new --run-dir")

        index = 0
        while index < len(stages):
            stage = stages[index]
            shard_group = ".generate." in stage.key or ".evaluate." in stage.key
            if shard_group:
                group_name = stage.key.rsplit(".", 1)[0]
                group: list[Stage] = []
                while index < len(stages) and stages[index].key.rsplit(".", 1)[0] == group_name:
                    group.append(stages[index])
                    index += 1
                pending = []
                for item in group:
                    if self.resume_existing and self.state.is_complete(item.key, item.artifacts, item.inputs):
                        print(f"[skip] {item.key}")
                    else:
                        pending.append(item)
                if pending:
                    with ThreadPoolExecutor(max_workers=len(pending)) as executor:
                        for item in pending:
                            for artifact in item.inputs or []:
                                validate_artifact(artifact)
                        futures = {executor.submit(item.action): item for item in pending}
                        first_error: BaseException | None = None
                        for future in as_completed(futures):
                            item = futures[future]
                            try:
                                future.result()
                                self.state.commit(item.key, item.artifacts, inputs=item.inputs)
                                print(f"[done] {item.key}")
                            except BaseException as error:
                                first_error = first_error or error
                        if first_error:
                            raise first_error
                continue

            complete = self.state.is_complete(stage.key, stage.artifacts, stage.inputs)
            if complete and self.resume_existing:
                print(f"[skip] {stage.key}")
                index += 1
                continue
            print(f"[run]  {stage.key}: {stage.description}")
            for artifact in stage.inputs or []:
                validate_artifact(artifact)
            stage.action()
            self.state.commit(stage.key, stage.artifacts, inputs=stage.inputs)
            index += 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the isolated Qwen3.5 R-Zero pipeline")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--from-stage")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--round", type=int, choices=range(1, 6))
    return parser


def main() -> None:
    Pipeline(build_parser().parse_args()).run()


if __name__ == "__main__":
    main()
