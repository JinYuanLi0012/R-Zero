"""Frozen solver, final hidden layer, mean over bare question tokens (B.2.4)."""
from __future__ import annotations

import numpy as np


class SolverFeatures:
    def __init__(self, model_path, batch_size=4, max_length=4096):
        import torch
        from transformers import AutoModel, AutoTokenizer

        self.torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        self.tokenizer.padding_side = "right"
        self.model = AutoModel.from_pretrained(
            model_path, torch_dtype=torch.bfloat16, attn_implementation="sdpa"
        ).to("cuda").eval()
        self.model.requires_grad_(False)
        self.batch_size, self.max_length = batch_size, max_length

    def extract(self, questions):
        torch = self.torch
        features, lengths = [], []
        for start in range(0, len(questions), self.batch_size):
            texts = questions[start:start + self.batch_size]
            # No chat template, BOS/EOS, answer tokens or <question> wrappers.
            lengths.extend(len(ids) for ids in self.tokenizer(texts, add_special_tokens=False)["input_ids"])
            tokens = self.tokenizer(texts, add_special_tokens=False, padding=True,
                                    truncation=True, max_length=self.max_length,
                                    return_tensors="pt").to("cuda")
            if not tokens.attention_mask.sum(dim=1).gt(0).all():
                raise ValueError("empty task tokens in embedding input")
            with torch.inference_mode():
                hidden = self.model(**tokens, use_cache=False).last_hidden_state
                mask = tokens.attention_mask.unsqueeze(-1)
                pooled = (hidden.float() * mask).sum(dim=1) / mask.sum(dim=1)
            features.append(pooled.cpu().numpy())
            del hidden, pooled, tokens
        x = np.concatenate(features) if features else np.empty((0, self.model.config.hidden_size))
        return x, {"count": len(questions), "truncated_questions": sum(n > self.max_length for n in lengths),
                   "max_task_tokens": max(lengths, default=0), "feature_normalization": "none"}
