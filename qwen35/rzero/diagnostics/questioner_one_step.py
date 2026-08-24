"""Run only the real one-step Questioner GRPO thinking-off gate."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from types import SimpleNamespace

from qwen35.rzero.pipeline.orchestrator import Pipeline
from qwen35.rzero.pipeline.state import Artifact, validate_artifact


def configure_node_caches() -> Path:
    scope = os.environ.get("SLURM_JOB_ID", "interactive")
    root = Path(
        os.environ.get("RZERO_NODE_CACHE_ROOT", f"/tmp/rzero-qwen35-{os.getuid()}/{scope}")
    )
    defaults = {
        "XDG_CACHE_HOME": root / "xdg",
        "TRITON_CACHE_DIR": root / "triton",
        "TORCHINDUCTOR_CACHE_DIR": root / "torchinductor",
        "CUDA_CACHE_PATH": root / "cuda",
        "VLLM_CACHE_ROOT": root / "vllm",
        "FLASHINFER_WORKSPACE_BASE": root / "flashinfer",
        "TMPDIR": root / "tmp",
    }
    for key, path in defaults.items():
        os.environ[key] = str(path)
        path.mkdir(parents=True, exist_ok=True)
    return root


def _run_stage(pipeline: Pipeline, key: str, artifacts: list[Artifact], inputs: list[Artifact], action) -> None:
    if pipeline.args.resume and pipeline.state.is_complete(key, artifacts, inputs):
        print(f"[skip] {key}")
        return
    for artifact in inputs:
        validate_artifact(artifact)
    print(f"[run]  {key}")
    action()
    pipeline.state.commit(key, artifacts, inputs=inputs)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-run-dir", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    cache_root = configure_node_caches()
    print(f"node_cache_root={cache_root}")

    pipeline_args = SimpleNamespace(
        run_dir=args.run_dir,
        config=str(args.config),
        resume=args.resume,
        from_stage=None,
        dry_run=False,
        round=1,
    )
    pipeline = Pipeline(pipeline_args)
    diagnostics = pipeline.config.get("diagnostics", {})
    if diagnostics.get("questioner_enable_thinking") is not False:
        raise RuntimeError("gate config must disable Questioner thinking")
    if not diagnostics.get("capture_questioner_rollouts"):
        raise RuntimeError("gate config must capture actual verl rollouts")

    source = args.source_run_dir.expanduser().resolve()
    model = source / "models" / "base"
    revision_receipt = model / "RZERO_MODEL_REVISION"
    seed_data = source / "data" / "seed"
    if not revision_receipt.is_file():
        raise RuntimeError(f"missing immutable model revision receipt: {revision_receipt}")
    revision = revision_receipt.read_text(encoding="utf-8").strip()
    if revision != pipeline.config["model"]["revision"]:
        raise RuntimeError(
            f"source model revision mismatch: found {revision!r}, expected {pipeline.config['model']['revision']!r}"
        )
    pipeline.base_model = model
    pipeline.seed_data = seed_data
    snapshot = {key: value for key, value in pipeline.config.items() if not key.startswith("_")}
    pipeline.state.initialize(snapshot)

    round_dir = pipeline._round_dir(1)
    checkpoint_root = round_dir / "questioner" / "checkpoints"
    actor = pipeline._checkpoint_actor(checkpoint_root, 1)
    export = round_dir / "questioner" / "export"
    train_file = seed_data / "questioner_train.parquet"
    val_file = seed_data / "questioner_val.parquet"
    model_input = Artifact(model, "model")
    train_inputs = [model_input, Artifact(revision_receipt), Artifact(train_file), Artifact(val_file)]

    _run_stage(
        pipeline,
        "questioner_train",
        [Artifact(actor, "checkpoint")],
        train_inputs,
        lambda: pipeline._train_questioner(1, model, model, "questioner_train"),
    )

    rollout_dump = round_dir / "diagnostics" / "training_rollouts" / "1.jsonl"
    rollout_summary = round_dir / "diagnostics" / "training_rollout_summary.json"
    population = (
        pipeline.config["algorithm"]["questioner_prompt_batch_size"]
        * pipeline.config["algorithm"]["questioner_rollouts"]
    )
    _run_stage(
        pipeline,
        "analyze_training_rollouts",
        [Artifact(rollout_summary, "json")],
        [Artifact(rollout_dump)],
        lambda: pipeline._run(
            [
                sys.executable,
                "-m",
                "qwen35.rzero.diagnostics.analyze_questioner_rollouts",
                "--input",
                str(rollout_dump),
                "--model",
                str(model),
                "--output",
                str(rollout_summary),
                "--expected-rows",
                str(population),
                "--max-tokens",
                str(pipeline.config["data"]["max_response_length"]),
            ],
            round_dir / "logs" / "analyze_training_rollouts.log",
        ),
    )

    _run_stage(
        pipeline,
        "questioner_export",
        [Artifact(export, "model")],
        [Artifact(actor, "checkpoint")],
        lambda: pipeline._export(checkpoint_root, 1, export, round_dir / "logs" / "questioner_export.log"),
    )

    post_dir = round_dir / "diagnostics" / "post_train_candidates"
    raw = post_dir / "qwen35_questioner_step1_thinking_off_raw_64.json"
    summary = post_dir / "qwen35_questioner_step1_thinking_off_summary.json"
    samples = int(diagnostics["post_train_samples"])
    _run_stage(
        pipeline,
        "post_train_candidates",
        [Artifact(raw, "json", samples), Artifact(summary, "json")],
        [Artifact(export, "model")],
        lambda: pipeline._run(
            [
                sys.executable,
                "-m",
                "qwen35.rzero.diagnostics.post_train_questioner",
                "--model",
                str(export),
                "--output-dir",
                str(post_dir),
                "--samples",
                str(samples),
                "--seed",
                "0",
                "--temperature",
                str(pipeline.config["generation"]["temperature"]),
                "--top-p",
                str(pipeline.config["generation"]["top_p"]),
                "--max-tokens",
                str(pipeline.config["generation"]["max_tokens"]),
            ],
            round_dir / "logs" / "post_train_candidates.log",
            env={"CUDA_VISIBLE_DEVICES": "0", "VLLM_USE_V1": "1"},
        ),
    )
    print("RZERO_QUESTIONER_THINKING_OFF_ONE_STEP_OK")


if __name__ == "__main__":
    main()
