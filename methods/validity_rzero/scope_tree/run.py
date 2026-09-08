#!/usr/bin/env python3
"""Build a two-level mathematical scope tree using one frozen Qwen3-4B-Base."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from . import prompts
from .core import SchemaError, TreeBuilder, leaf_records, parse_response, response_diagnostics


def atomic_json(path, data):
    path = Path(path)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class BudgetExhausted(RuntimeError):
    pass


class ParseRetriesExhausted(RuntimeError):
    pass


class ContextBudgetExceeded(RuntimeError):
    pass


class StructuredClient:
    """Persist every inference attempt, including analysis and failed parses.

    Request keys and seeds are deterministic. Resume revalidates successful raw
    completions and reuses them; retries and call budgets persist across resumes.
    """

    def __init__(self, backend, output_dir, seed=42, parse_retries=2, max_calls=128):
        self.backend = backend
        self.directory = Path(output_dir) / "requests"
        self.directory.mkdir(parents=True, exist_ok=True)
        self.seed = seed
        self.parse_retries = parse_retries
        self.max_calls = max_calls
        self.calls = len(list(self.directory.glob("*/attempt_*.json")))

    def request(self, label, user_prompt, validator):
        key = digest(label + "\n" + prompts.SYSTEM + "\n" + user_prompt)
        folder = self.directory / key
        folder.mkdir(exist_ok=True)
        atomic_json(folder / "request.json", {"label": label, "system": prompts.SYSTEM, "user": user_prompt, "key": key})
        last_error = None
        for attempt in range(self.parse_retries + 1):
            path = folder / f"attempt_{attempt}.json"
            if path.exists():
                saved = json.loads(path.read_text(encoding="utf-8"))
                if saved.get("status") == "ok":
                    # Validate against the CURRENT parent/sibling state as well.
                    return validator(parse_response(saved["raw_completion"]))
                last_error = saved.get("error", "previous attempt failed")
                continue
            if self.calls >= self.max_calls:
                raise BudgetExhausted(f"global generation budget exhausted ({self.max_calls} calls)")
            seed = (self.seed + int(key[:8], 16) + attempt) % (2**31)
            retry_prompt = user_prompt
            if last_error:
                retry_prompt += (
                    "\nYour preceding attempt did not yield a valid structured result.\n"
                    f"Validation error: {last_error}\n"
                    "Retry the SAME task. First write a concise analysis, then a complete JSON result. "
                    "Follow the exact schema, include every required id/pair, and wrap the final JSON in "
                    "<final_json>...</final_json>. Analysis can be ordinary prose; no analysis tags are required. "
                    "Do not discuss the formatting failure or copy the previous answer.\n"
                )
            saved = {"label": label, "attempt": attempt, "seed": seed, "user": retry_prompt,
                     "status": "started", "started_at": time.time()}
            # An interrupted inference remains visible and consumes its attempt.
            atomic_json(path, saved)
            self.calls += 1
            print(f"[{self.calls}/{self.max_calls}] {label} attempt={attempt + 1}", flush=True)
            started = time.monotonic()
            try:
                output = self.backend.generate(prompts.SYSTEM, retry_prompt, seed)
                saved.update(output)
                saved["diagnostics"] = response_diagnostics(output["raw_completion"])
                data = parse_response(output["raw_completion"])
                result = validator(data)
                saved.update({"status": "ok", "parsed_json": data})
            except (SchemaError, RecursionError) as exc:
                last_error = str(exc)
                saved.update({"status": "parse_error", "error": last_error})
                print(f"  retryable parse/schema error: {last_error}", flush=True)
                print("  output diagnostics: " + json.dumps({
                    "attempt_file": str(path), "finish_reason": saved.get("finish_reason"),
                    "completion_tokens": saved.get("completion_tokens"),
                    **saved.get("diagnostics", {}),
                }, ensure_ascii=False), flush=True)
            except BaseException as exc:
                saved.update({"status": "inference_error", "error": f"{type(exc).__name__}: {exc}"})
                raise
            finally:
                saved["wall_seconds"] = time.monotonic() - started
                atomic_json(path, saved)
            if saved["status"] == "ok":
                return result
        raise ParseRetriesExhausted(f"{label}: no parseable result after {self.parse_retries + 1} attempts: {last_error}")


class VLLMBackend:
    def __init__(self, model_path, args):
        from transformers import AutoTokenizer
        from vllm import LLM, SamplingParams

        self.args = args
        self.sampling_class = SamplingParams
        self.tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
        self.model = LLM(model=model_path, tokenizer=model_path, tensor_parallel_size=1,
                         seed=args.seed, max_model_len=args.max_model_len,
                         gpu_memory_utilization=args.gpu_memory_utilization)

    def generate(self, system, user, seed):
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        if self.tokenizer.chat_template:
            prompt = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            template = "tokenizer_chat_template"
        else:
            prompt = f"system: {system}\nuser: {user}\nassistant:\n"
            template = "plain_role_fallback"
        prompt_tokens = len(self.tokenizer.encode(prompt, add_special_tokens=False))
        if prompt_tokens + self.args.max_new_tokens > self.args.max_model_len:
            raise ContextBudgetExceeded(
                f"prompt {prompt_tokens} + completion budget {self.args.max_new_tokens} exceeds "
                f"max_model_len={self.args.max_model_len}; no siblings or leaves were silently truncated"
            )
        sampling = self.sampling_class(
            n=1, max_tokens=self.args.max_new_tokens, temperature=self.args.temperature,
            top_p=self.args.top_p, top_k=20, seed=seed,
            stop=["</final_json>"], include_stop_str_in_output=True,
        )
        outputs = self.model.generate([prompt], sampling_params=sampling, use_tqdm=False)
        if len(outputs) != 1 or len(outputs[0].outputs) != 1:
            raise RuntimeError("expected exactly one vLLM completion")
        completion = outputs[0].outputs[0]
        return {"raw_completion": completion.text, "rendered_prompt": prompt,
                "prompt_template": template, "prompt_tokens": prompt_tokens,
                "completion_tokens": len(completion.token_ids), "finish_reason": completion.finish_reason}


def arguments(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model", default="Qwen/Qwen3-4B-Base", help="HF repo or local snapshot of the same frozen Base")
    parser.add_argument("--revision", default=None, help="Optional HF revision; resolved snapshot is recorded")
    parser.add_argument("--gpu-id", default="0", help="One physical GPU, e.g. 0 or 2")
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.8)
    parser.add_argument("--local-files-only", action="store_true")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--temperature", type=float, default=0.6)
    parser.add_argument("--top-p", type=float, default=0.95)
    parser.add_argument("--max-new-tokens", type=int, default=8192)
    parser.add_argument("--max-model-len", type=int, default=32768)
    parser.add_argument("--max-repairs", type=int, default=2, help="Local semantic repair rounds per parent; not a width quota")
    parser.add_argument("--parse-retries", type=int, default=2, help="Additional attempts per malformed result")
    parser.add_argument("--max-calls", type=int, default=128, help="Total inference attempts, including retries; safety budget only")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args(argv)
    if args.max_repairs < 0 or args.parse_retries < 0 or args.max_calls < 1:
        parser.error("repair/retry budgets must be nonnegative; max-calls must be positive")
    if not 0 < args.gpu_memory_utilization < 1 or not 0 < args.top_p <= 1 or args.temperature < 0:
        parser.error("invalid sampling or memory parameters")
    if not 0 < args.max_new_tokens < args.max_model_len:
        parser.error("require 0 < max-new-tokens < max-model-len")
    if not args.gpu_id.isdigit():
        parser.error("--gpu-id must name a single nonnegative GPU index")
    return args


def resolve_model(args):
    local = Path(args.model).expanduser()
    if local.is_dir():
        if args.revision is not None:
            raise ValueError("--revision is only valid for a HF repository id")
        return str(local.resolve())
    from huggingface_hub import snapshot_download
    return snapshot_download(args.model, revision=args.revision, local_files_only=args.local_files_only)


def run_config(args, model_path):
    source_dir = Path(__file__).resolve().parent
    # Track immutable HF snapshot path, config/tokenizer contents, and weight file metadata.
    files = []
    for path in sorted(Path(model_path).iterdir()):
        if path.is_file() and path.suffix in (".json", ".jinja", ".safetensors", ".bin", ".model"):
            stat = path.stat()
            entry = {"name": path.name, "bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns}
            if path.suffix in (".json", ".jinja"):
                entry["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            files.append(entry)
    return {"prompt_version": prompts.VERSION, "depth": 2, "model": args.model,
            "resolved_model_path": model_path, "model_files": files,
            "source_hashes": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(source_dir.glob("*.py"))},
            "seed": args.seed, "temperature": args.temperature, "top_p": args.top_p, "top_k": 20,
            "max_new_tokens": args.max_new_tokens, "max_model_len": args.max_model_len,
            "max_repairs": args.max_repairs, "parse_retries": args.parse_retries,
            "max_calls": args.max_calls, "gpu_id": args.gpu_id,
            "gpu_memory_utilization": args.gpu_memory_utilization}


def write_readable(directory, root, status, calls):
    lines = ["# Frozen Base scope tree", "", f"Status: **{status['state']}**", "",
             f"Model calls used (including retries): {calls}", "",
             f"L1 families: {len(root['children'])}; depth-2 leaves: {len(leaf_records(root))}", "",
             "An accepted audit is a same-model judgment, not independent verification of mathematical coverage.", ""]
    for parent in root["children"]:
        lines.extend([f"## {parent['id']}. {parent['name']}", "", parent["scope"], "",
                      f"Partition principle: {parent.get('partition_principle', '(not built)')}", ""])
        for leaf in parent["children"]:
            lines.extend([f"### {leaf['id']} {leaf['name']}", "", leaf["scope"], "",
                          f"Distinguishing feature: {leaf['distinguishing_feature']}", ""])
    (directory / "tree.md").write_text("\n".join(lines), encoding="utf-8")


def main(argv=None):
    args = arguments(argv)
    directory = args.output_dir.expanduser().resolve()
    if args.resume:
        if not (directory / "manifest.json").is_file():
            raise ValueError("--resume requires an existing manifest.json")
    elif directory.exists() and any(p.name != ".run.lock" for p in directory.iterdir()):
        raise ValueError("output directory is not empty; use --resume with identical settings or choose a new directory")
    directory.mkdir(parents=True, exist_ok=True)
    # Hold an advisory process lock throughout model loading and generation.
    import fcntl
    with (directory / ".run.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("another scope-tree process is using this output directory") from exc
        os.environ["CUDA_VISIBLE_DEVICES"] = args.gpu_id
        if args.local_files_only:
            os.environ["HF_HUB_OFFLINE"] = "1"
            os.environ["TRANSFORMERS_OFFLINE"] = "1"
        model_path = resolve_model(args)
        config = run_config(args, model_path)
        manifest_path = directory / "manifest.json"
        if args.resume:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest["config"] != config:
                raise ValueError("resume config/model/source fingerprint differs; use a new output directory")
            if manifest.get("state") == "accepted" and (directory / "tree.json").is_file():
                print(f"Already complete: {directory / 'tree.json'}")
                return 0
        else:
            revision = subprocess.run(["git", "-C", str(Path(__file__).resolve().parents[3]), "rev-parse", "HEAD"],
                                      capture_output=True, text=True, check=False)
            manifest = {"config": config, "git_head": revision.stdout.strip(), "created_at": time.time()}
        manifest.update({"state": "loading", "last_started_at": time.time(), "error": None})
        atomic_json(manifest_path, manifest)
        builder = client = None
        try:
            backend = VLLMBackend(model_path, args)
            import transformers
            import vllm
            manifest["versions"] = {"python": sys.version, "transformers": transformers.__version__, "vllm": vllm.__version__}
            client = StructuredClient(backend, directory, args.seed, args.parse_retries, args.max_calls)

            def checkpoint(root, status):
                atomic_json(directory / "partial_tree.json", root)
                atomic_json(directory / "status.json", status)

            builder = TreeBuilder(client, args.max_repairs, checkpoint)
            accepted = builder.build()
            manifest.update({"state": builder.status["state"], "calls_used": client.calls,
                             "l1_count": len(builder.root["children"]), "leaf_count": len(leaf_records(builder.root))})
            if accepted:
                atomic_json(directory / "tree.json", builder.root)
            write_readable(directory, builder.root, builder.status, client.calls)
            atomic_json(manifest_path, manifest)
            print(json.dumps({"state": manifest["state"], "calls_used": client.calls,
                              "leaf_count": manifest["leaf_count"], "output_dir": str(directory)}, ensure_ascii=False))
            return 0 if accepted else 2
        except BaseException as exc:
            manifest.update({"state": "failed", "error": f"{type(exc).__name__}: {exc}",
                             "calls_used": client.calls if client else 0})
            atomic_json(manifest_path, manifest)
            if builder:
                builder.status.update({"state": "failed", "error": manifest["error"]})
                builder.save()
                write_readable(directory, builder.root, builder.status, client.calls)
            raise


if __name__ == "__main__":
    sys.exit(main())
