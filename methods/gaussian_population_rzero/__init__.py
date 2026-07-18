"""Gaussian-population R-Zero experiment.

Only the two central R-Zero models are trained.  Population members are
ephemeral deterministic Gaussian perturbations used for inference.
"""

from .population import ExpertSpec, GaussianPopulation, allocate_quotas, make_expert_specs

__all__ = ["ExpertSpec", "GaussianPopulation", "allocate_quotas", "make_expert_specs"]
