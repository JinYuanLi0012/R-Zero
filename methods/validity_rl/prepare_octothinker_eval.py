#!/usr/bin/env python3
"""Merge trusted local two-rank checkpoints without changing training artifacts."""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def require_file(path):
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"Missing or empty file: {path}")


def validate_weights(path):
    require_file(path / "config.json")
    require_file(path / "tokenizer_config.json")
    require_file(path / "tokenizer.json")
    for index_name in ("model.safetensors.index.json", "pytorch_model.bin.index.json"):
        index = path / index_name
        if index.exists():
            weight_map = json.loads(index.read_text())["weight_map"]
            if not weight_map:
                raise ValueError(f"Empty weight index: {index}")
            for name in set(weight_map.values()):
                target = (path / name).resolve()
                if target.parent != path.resolve():
                    raise ValueError(f"Invalid weight path in {index}: {name}")
                require_file(target)
            return
    for name in ("model.safetensors", "pytorch_model.bin"):
        if (path / name).exists():
            require_file(path / name)
            return
    raise ValueError(f"No complete merged weights found in {path}")


def source_files(actor):
    shards = [actor / f"model_world_size_2_rank_{rank}.pt" for rank in range(2)]
    for path in shards:
        require_file(path)
    config_dir = actor / "huggingface"
    for name in ("config.json", "tokenizer_config.json", "tokenizer.json"):
        require_file(config_dir / name)
    # Only copy metadata/tokenizer files, never old merged weights.
    metadata = sorted(p for p in config_dir.iterdir() if p.is_file() and
                      p.suffix in {".json", ".jinja", ".model", ".txt"} and
                      not p.name.endswith(".index.json"))
    return shards, metadata


def fingerprint(paths):
    return [{"path": str(p.resolve()), "size": p.stat().st_size,
             "mtime_ns": p.stat().st_mtime_ns} for p in paths]


def prepare(root, output_root, steps):
    # Check ALL requested inputs before doing costly CPU merges.
    sources = {step: source_files(root / f"global_step_{step}" / "actor") for step in steps}
    for step, (shards, metadata) in sources.items():
        destination = output_root / f"global_step_{step}"
        stamp = fingerprint(shards + metadata)
        marker = destination / "merge_source.json"
        if destination.exists():
            if not marker.is_file() or json.loads(marker.read_text()) != stamp:
                raise ValueError(f"Existing merge is unverified or source changed: {destination}. "
                                 "Choose a new VALIDITY_TERRA_MODEL_ROOT; no files were overwritten.")
            validate_weights(destination / "actor" / "huggingface")
            print(f"Reusing completed merge: {destination}", flush=True)
            continue
        output_root.mkdir(parents=True, exist_ok=True)
        # Same filesystem allows publishing only after a successful merge.
        with tempfile.TemporaryDirectory(prefix=f".merge_step_{step}_", dir=output_root) as tmp:
            stage = Path(tmp)
            actor = stage / "actor"
            hf = actor / "huggingface"
            hf.mkdir(parents=True)
            for p in shards:
                (actor / p.name).symlink_to(p.resolve())
            for p in metadata:
                shutil.copy2(p, hf / p.name)
            print(f"Merging step {step} on CPU (original checkpoint unchanged)", flush=True)
            subprocess.run([sys.executable, str(Path(__file__).resolve().parents[2] /
                           "scripts/model_merger.py"), "--local_dir", str(actor)],
                           check=True, env={**os.environ, "CUDA_VISIBLE_DEVICES": ""})
            validate_weights(hf)
            if fingerprint(shards + metadata) != stamp:
                raise ValueError("Checkpoint changed during merging; stop training before evaluating it")
            for p in shards:
                (actor / p.name).unlink()  # Remove only temporary symlinks, never source shards.
            (stage / "merge_source.json").write_text(json.dumps(stamp, indent=2) + "\n")
            stage.rename(destination)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--steps", nargs="+", type=int, choices=[5, 10, 15], required=True)
    args = parser.parse_args()
    if args.run_root.resolve() == args.output_root.resolve():
        parser.error("Output root must differ from the training run root")
    prepare(args.run_root.resolve(), args.output_root.resolve(), args.steps)


if __name__ == "__main__":
    main()
