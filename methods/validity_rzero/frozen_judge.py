"""Opt-in frozen SFT judge protocol; legacy models keep their original protocol."""
import hashlib
import json
from pathlib import Path
from .semantic_judge_offline.run_pair_judge_v3_vllm import sampling_options


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_protocol(model):
    path = Path(model) / "judge_protocol.json"
    if not path.is_file():
        return None
    value = json.loads(path.read_text())
    if value["version"] != "octo-judge-sft-v2-clear-eos-v1":
        raise ValueError("Unknown frozen judge protocol")
    if value["max_tokens"] != 256 or not value["system_prompt"] or not value["chat_template"]:
        raise ValueError("Invalid frozen judge protocol")
    return value


def judge_sampling(model, max_tokens, seed):
    result = sampling_options(max_tokens, seed)
    protocol = load_protocol(model)
    if protocol:
        if max_tokens != protocol["max_tokens"]:
            raise ValueError("Frozen judge output budget mismatch")
        result.update(temperature=0.0, top_p=1.0, top_k=-1, min_p=0.0,
                      presence_penalty=0.0, frequency_penalty=0.0, repetition_penalty=1.0,
                      stop=[], ignore_eos=False)
    return result


def online_protocol(model, legacy_builder, legacy_version, legacy_template):
    protocol = load_protocol(model)
    if not protocol:
        return legacy_builder, legacy_version, legacy_template, 1024
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(model, local_files_only=True)
    if tokenizer.chat_template != protocol["chat_template"]:
        raise ValueError("Frozen tokenizer template mismatch")
    def build(a, b):
        messages = [{"role": "system", "content": protocol["system_prompt"]},
                    {"role": "user", "content": f"Question A:\n{a}\n\nQuestion B:\n{b}"}]
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    identity = json.dumps(protocol, sort_keys=True)
    return build, protocol["version"], identity, protocol["max_tokens"]


def verify_frozen(root):
    root = Path(root)
    if not load_protocol(root):
        raise ValueError("Expected exported SFT judge, not a base checkpoint")
    hashes = json.loads((root / "SHA256SUMS.json").read_text())
    for name, digest in hashes.items():
        if Path(name).is_absolute() or ".." in Path(name).parts:
            raise ValueError("Unsafe checksum path")
        if file_hash(root / name) != digest:
            raise ValueError(f"Frozen judge checksum mismatch: {name}")
    return file_hash(root / "SHA256SUMS.json")
