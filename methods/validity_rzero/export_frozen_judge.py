"""Merge an SFT adapter once into a new, checksum-pinned read-only HF directory."""
import argparse
import json
import os
from pathlib import Path
import shutil
import tempfile
from .frozen_judge import file_hash, verify_frozen


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model")
    p.add_argument("--adapter", type=Path)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--verify-only", action="store_true")
    args = p.parse_args()
    if args.verify_only:
        print(verify_frozen(args.output_dir))
        return
    if not args.model or not args.adapter:
        p.error("--model and --adapter are required for export")
    if args.output_dir.exists():
        raise FileExistsError("Refuse to overwrite frozen judge; verify existing export explicitly")
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel
    from scripts.validate_hf_checkpoint import validate_checkpoint
    run = args.adapter.parent
    completed = json.loads((run / "completed.json").read_text())
    if completed["epochs"] != 3 or args.adapter.name != "epoch_3":
        raise ValueError("Expected the completed epoch_3 adapter")
    manifest = json.loads((run / "manifest.json").read_text())
    if Path(manifest["args"]["model"]).resolve() != Path(args.model).resolve():
        raise ValueError("Base snapshot differs from training")
    args.output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=args.output_dir.name+".staging-", dir=args.output_dir.parent))
    model = AutoModelForCausalLM.from_pretrained(args.model, torch_dtype=torch.bfloat16, local_files_only=True)
    model = PeftModel.from_pretrained(model, args.adapter).merge_and_unload(safe_merge=True)
    model.config.use_cache = True
    model.generation_config.do_sample = False
    model.generation_config.temperature = 1.0
    model.generation_config.top_p = 1.0
    model.generation_config.top_k = 0
    model.save_pretrained(staging, safe_serialization=True, max_shard_size="4GB")
    tokenizer = AutoTokenizer.from_pretrained(args.adapter, local_files_only=True)
    tokenizer.save_pretrained(staging)
    protocol = {"version": "octo-judge-sft-v2-clear-eos-v1", "max_tokens": 256,
                "system_prompt": (run / "system_prompt.txt").read_text(),
                "chat_template": tokenizer.chat_template,
                "base_snapshot": str(Path(args.model).resolve()),
                "adapter_sha256": file_hash(args.adapter / "adapter_model.safetensors"),
                "decoding": "greedy; EOS; no boxed stop; no extra BOS"}
    (staging / "judge_protocol.json").write_text(json.dumps(protocol, indent=2)+"\n")
    shutil.copytree(args.adapter, staging / "source_adapter")
    (staging / "training_provenance").mkdir()
    for name in ("manifest.json", "history.json", "best_adapter.json", "completed.json", "system_prompt.txt"):
        shutil.copy2(run / name, staging / "training_provenance" / name)
    validate_checkpoint(staging)
    files = sorted(x for x in staging.rglob("*") if x.is_file())
    hashes = {str(x.relative_to(staging)): file_hash(x) for x in files}
    (staging / "SHA256SUMS.json").write_text(json.dumps(hashes, indent=2)+"\n")
    digest = verify_frozen(staging)
    for path in staging.rglob("*"):
        path.chmod(0o555 if path.is_dir() else 0o444)
    staging.chmod(0o555)
    os.rename(staging, args.output_dir)
    print(json.dumps({"frozen_model": str(args.output_dir), "manifest_sha256": digest}), flush=True)


if __name__ == "__main__":
    main()
