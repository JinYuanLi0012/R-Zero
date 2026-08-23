import numpy as np
import torch

from verl.protocol import DataProto
from verl.utils.dataset import RLHFDataset


def dataset_for_messages():
    dataset = RLHFDataset.__new__(RLHFDataset)
    dataset.prompt_key = "problem"
    dataset.image_key = "images"
    dataset.format_prompt = "solver_format"
    dataset.format_prompt_source_key = "source"
    dataset.default_source = "rzero"
    dataset.format_prompt_by_source = {
        "rzero": "solver_format",
        "terra": "{{ content }}\nReturn INVALID only when the problem is invalid.",
    }
    return dataset


def test_routes_prompt_by_source():
    dataset = dataset_for_messages()
    rzero = dataset._build_messages({"problem": "2+2?", "source": "rzero"})
    terra = dataset._build_messages({"problem": "2+2?", "source": "terra"})
    assert rzero[0]["role"] == "system"
    assert rzero[1]["content"] == "2+2?"
    assert terra == [{"role": "user", "content": "2+2?\nReturn INVALID only when the problem is invalid."}]


def test_missing_source_uses_baseline_prompt():
    dataset = dataset_for_messages()
    messages = dataset._build_messages({"problem": "2+2?"})
    assert messages[0]["role"] == "system"


def test_source_stays_aligned_when_rollouts_repeat():
    data = DataProto.from_dict(
        tensors={"input_ids": torch.zeros((2, 1), dtype=torch.long)},
        non_tensors={"source": np.array(["rzero", "terra"], dtype=object)},
    )
    repeated = data.repeat(repeat_times=3, interleave=True)
    assert repeated.non_tensor_batch["source"].tolist() == [
        "rzero", "rzero", "rzero", "terra", "terra", "terra"
    ]
