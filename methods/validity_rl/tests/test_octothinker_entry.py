"""CPU checks for the real shell argv/config path; no Ray or GPU required."""
import json
import os
from pathlib import Path
import subprocess
import sys

from datasets import Dataset, DatasetDict
from jinja2 import Template
from omegaconf import OmegaConf
import pytest

from methods.validity_rl import prepare_dataset as prepare

METHOD = Path(__file__).resolve().parents[1]


def run_entry(tmp_path, mode=None, gpus="0,1"):
    # Intercept python only at process boundary, preserving real bash expansion
    # and real OmegaConf parsing of the trainer's arguments.
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake = bin_dir / "python3"
    fake.write_text(
        f"#!{sys.executable}\nimport json,sys,os\n"
        "if sys.argv[1].endswith('resume_checkpoint.py'):\n"
        f"    os.execv({sys.executable!r}, [{sys.executable!r}] + sys.argv[1:])\n"
        "print('ARGV:'+json.dumps(sys.argv[1:]))\n"
    )
    fake.chmod(0o755)
    env = {k: v for k, v in os.environ.items() if not k.startswith("VALIDITY_")}
    env.update(PATH=str(bin_dir) + os.pathsep + env["PATH"],
               STORAGE_PATH=str(tmp_path / "storage"), VALIDITY_GPU_IDS=gpus)
    command = ["bash", str(METHOD / "train_octothinker_grpo.sh")]
    if mode:
        command.append(mode)
    return subprocess.run(command, env=env, text=True, capture_output=True)


@pytest.mark.parametrize("mode,steps,batch,n", [(None,15,512,8), ("--smoke",1,2,2)])
def test_real_launch_arguments(tmp_path, mode, steps, batch, n):
    result = run_entry(tmp_path, mode)
    assert result.returncode == 0, result.stderr
    calls = [json.loads(line[5:]) for line in result.stdout.splitlines() if line.startswith("ARGV:")]
    prep, trainer = calls
    assert prep[prep.index("--dataset") + 1] == prepare.CLEAN_DATASET
    assert ("--full" in prep) == (mode is None)
    cfg = OmegaConf.from_cli(trainer[2:])
    assert cfg.worker.actor.model.model_path == "OctoThinker/OctoThinker-3B-Hybrid-Base"
    assert cfg.trainer.n_gpus_per_node == cfg.worker.rollout.tensor_parallel_size == 2
    assert cfg.trainer.max_steps == steps
    assert cfg.data.rollout_batch_size == batch
    assert cfg.worker.rollout.n == n
    assert cfg.data.train_files.endswith("/data/train.parquet")
    assert cfg.data.val_files.endswith("/data/validation.parquet")
    assert ("_smoke/" in cfg.data.train_files) == (mode == "--smoke")
    prompt = Template((METHOD / "validity_solver.jinja").read_text()).render(content="What is 2+2?")
    rendered = Template(cfg.data.override_chat_template).render(
        bos_token="<|begin_of_text|>", messages=[{"role":"user","content":prompt}], add_generation_prompt=True)
    assert rendered.startswith("<|begin_of_text|>user: What is 2+2?")
    assert "Do not output INVALID merely" in rendered
    assert rendered.endswith("assistant:\n")
    assert rendered.count("<|begin_of_text|>") == 1


def test_reject_four_gpus_before_launch(tmp_path):
    result = run_entry(tmp_path, gpus="0,1,2,3")
    assert result.returncode == 2
    assert "ARGV:" not in result.stdout


def row(identifier, split, valid=True):
    return dict(id=identifier, split=split, round="v1", question="What is 2+2?",
                terra_validity="VALID" if valid else "INVALID",
                validity_rl_target="4" if valid else "INVALID",
                canonical_final_answer="4" if valid else None,
                answer_verified=True if valid else None)


def test_clean_file_selection_and_audit(monkeypatch):
    def load(name, **kwargs):
        assert name == prepare.CLEAN_DATASET
        assert kwargs == {"data_files":{"train":"train.jsonl", "validation":"validation.jsonl"}}
        return DatasetDict(train=Dataset.from_list([row("a","train"),row("b","train",False)]),
                           validation=Dataset.from_list([row("c","validation")]))
    monkeypatch.setattr(prepare, "load_dataset", load)
    _, report = prepare.audit_dataset(prepare.CLEAN_DATASET)
    assert report["splits"]["train"]["validity_counts"] == {"VALID":1,"INVALID":1}


def test_audit_rejects_split_leakage(monkeypatch):
    monkeypatch.setattr(prepare, "load_dataset", lambda *a,**k: DatasetDict(
        train=Dataset.from_list([row("a","train")]),
        validation=Dataset.from_list([row("a","validation")])) )
    with pytest.raises(ValueError, match="overlap"):
        prepare.audit_dataset(prepare.CLEAN_DATASET)


def recovery_fixture(tmp_path):
    root = tmp_path / "storage/models/octothinker_3b_hybrid_validity_rl_terra_clean_v1"
    actor = root / "global_step_10/actor"
    actor.mkdir(parents=True)
    for rank in range(2):
        for kind in ("model", "optim", "extra_state"):
            (actor / f"{kind}_world_size_2_rank_{rank}.pt").write_bytes(b"fixture")
    (actor.parent / "dataloader.pt").write_bytes(b"fixture")
    (root / "latest_global_step.txt").write_text("10")
    (root / "data").mkdir()
    for name in ("train.parquet", "validation.parquet"):
        (root / "data" / name).write_bytes(b"original dataset fixture")
    (root / "data/audit.json").write_text(json.dumps({"dataset":prepare.CLEAN_DATASET}))
    (root / "global_step_15/actor").mkdir(parents=True)
    (root / "global_step_15/actor/model_world_size_2_rank_0.pt").write_bytes(b"partial")
    return root


def test_resume_uses_committed_10_skips_dataset_preparation(tmp_path):
    root = recovery_fixture(tmp_path)
    result = run_entry(tmp_path, "--resume", "0,3")
    assert result.returncode == 0, result.stderr
    calls = [json.loads(line[5:]) for line in result.stdout.splitlines() if line.startswith("ARGV:")]
    assert len(calls) == 1  # trainer only; original dataset never regenerated
    cfg = OmegaConf.from_cli(calls[0][2:])
    assert cfg.trainer.load_checkpoint_path == str(root / "global_step_10")
    assert cfg.trainer.max_steps == 15
    assert (root / "global_step_15/actor/model_world_size_2_rank_0.pt").read_bytes() == b"partial"


@pytest.mark.parametrize("missing", ["global_step_10/actor/optim_world_size_2_rank_1.pt", "data/train.parquet"])
def test_resume_rejects_missing_state_or_data(tmp_path, missing):
    root = recovery_fixture(tmp_path)
    (root / missing).unlink()
    result = run_entry(tmp_path, "--resume")
    assert result.returncode != 0
    assert "ARGV:" not in result.stdout


def test_resume_rejects_wrong_dataset(tmp_path):
    root = recovery_fixture(tmp_path)
    (root / "data/audit.json").write_text(json.dumps({"dataset":"different"}))
    result = run_entry(tmp_path, "--resume")
    assert result.returncode != 0
    assert "Dataset differs" in result.stderr
