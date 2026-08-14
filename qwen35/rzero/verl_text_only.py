"""Install the text-only processor policy through verl's external-lib hook.

Qwen3.5 uses a unified conditional-generation checkpoint, so ``hf_processor``
normally returns a multimodal processor even when every sample is text. verl
then constructs unnecessary four-axis M-RoPE IDs; the pinned PyTorch/verl stack
can transpose that 3-D jagged tensor while splitting micro-batches.

Returning ``None`` does not replace the tokenizer or model code:
``HFModelConfig.get_processor()`` falls back to the official tokenizer, and
Qwen3.5 expands ordinary 1-D text positions internally.
"""

from __future__ import annotations

from typing import Any

import verl.workers.config.model as verl_model_config


def _text_only_processor(*_args: Any, **_kwargs: Any) -> None:
    return None


# HFModelConfig imports this module before calling its local hf_processor
# symbol. The assignment is therefore narrow and idempotent per Ray worker.
verl_model_config.hf_processor = _text_only_processor
