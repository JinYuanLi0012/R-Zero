#!/usr/bin/env python3
"""Minimal deterministic Gaussian population primitive.

This module deliberately implements only

    theta_i = theta + sigma * epsilon_i, epsilon_i ~ N(0, I).

There is no selection, ES update, voting, distillation, or persistence of
expert checkpoints.  A single CPU anchor is kept per physical model instance;
each logical expert is reconstructed from that anchor before use.
"""

from __future__ import annotations

from typing import Sequence

import torch

if __package__:
    from .population_spec import (
        ExpertSpec,
        allocate_quotas,
        assign_experts,
        make_expert_specs,
        stable_seed,
    )
else:  # Support direct execution from this method directory.
    from population_spec import (
        ExpertSpec,
        allocate_quotas,
        assign_experts,
        make_expert_specs,
        stable_seed,
    )


def _named_unique_parameters(model: torch.nn.Module) -> list[tuple[str, torch.nn.Parameter]]:
    try:
        named = list(model.named_parameters(remove_duplicate=False))
    except TypeError:  # Older torch fallback.
        named = list(model.named_parameters())

    aliases: dict[int, tuple[torch.nn.Parameter, list[str]]] = {}
    for name, parameter in named:
        key = id(parameter)
        if key not in aliases:
            aliases[key] = (parameter, [])
        aliases[key][1].append(name)

    unique = [(min(names), parameter) for parameter, names in aliases.values()]
    unique.sort(key=lambda item: item[0])
    return unique


class GaussianPopulation:
    """Construct ephemeral experts around the model's immutable CPU anchor."""

    def __init__(self, model: torch.nn.Module):
        self.model = model
        self.parameters = _named_unique_parameters(model)
        if not self.parameters:
            raise ValueError("model has no parameters to perturb")
        self.anchor = {
            name: parameter.detach().to(device="cpu", copy=True)
            for name, parameter in self.parameters
        }
        self.active_expert: ExpertSpec | None = None

    @property
    def parameter_names(self) -> list[str]:
        return [name for name, _ in self.parameters]

    def parameter_seed(self, expert: ExpertSpec, parameter_name: str) -> int:
        return stable_seed(
            expert.global_seed,
            expert.role,
            expert.round_index,
            expert.expert_index,
            parameter_name,
        )

    @torch.no_grad()
    def restore(self) -> None:
        for name, parameter in self.parameters:
            parameter.copy_(self.anchor[name], non_blocking=False)
        self.active_expert = None
        if torch.cuda.is_available() and any(p.is_cuda for _, p in self.parameters):
            torch.cuda.synchronize()

    @torch.no_grad()
    def apply(self, expert: ExpertSpec) -> None:
        """Replace current weights with one exact anchor-relative perturbation."""
        for name, parameter in self.parameters:
            base = self.anchor[name].to(device=parameter.device, dtype=torch.float32)
            generator = torch.Generator(device=parameter.device)
            generator.manual_seed(self.parameter_seed(expert, name))
            noise = torch.randn(
                parameter.shape,
                dtype=torch.float32,
                device=parameter.device,
                generator=generator,
            )
            perturbed = base.add(noise, alpha=expert.sigma).to(dtype=parameter.dtype)
            parameter.copy_(perturbed)
            del base, noise, perturbed
        self.active_expert = expert
        if torch.cuda.is_available() and any(p.is_cuda for _, p in self.parameters):
            torch.cuda.synchronize()


def get_vllm_model(llm: object) -> torch.nn.Module:
    """Return the local TP=1 vLLM model with an explicit compatibility error."""
    candidates: Sequence[Sequence[str]] = (
        ("llm_engine", "model_executor", "driver_worker", "worker", "model_runner", "model"),
        ("llm_engine", "model_executor", "driver_worker", "model_runner", "model"),
    )
    for path in candidates:
        value = llm
        try:
            for attribute in path:
                value = getattr(value, attribute)
        except AttributeError:
            continue
        if isinstance(value, torch.nn.Module):
            return value
    raise RuntimeError(
        "Unable to access the local vLLM model. Gaussian Population R-Zero is "
        "validated for the repository's vllm==0.9.1 with tensor_parallel_size=1."
    )
