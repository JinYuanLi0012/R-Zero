"""Parameter-space geometry analysis for task-vector R-Zero runs."""

from .delta_definitions import DeltaSpec, RunInputs, discover_run_inputs
from .geometry import derive_geometry

__all__ = ["DeltaSpec", "RunInputs", "derive_geometry", "discover_run_inputs"]
