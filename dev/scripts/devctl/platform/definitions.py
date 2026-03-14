"""Public reusable-platform definition exports."""

from .contract_definitions import shared_contracts
from .surface_definitions import (
    adoption_flow,
    frontend_surfaces,
    platform_layers,
    portability_status,
    repo_local_boundaries,
)

__all__ = [
    "adoption_flow",
    "frontend_surfaces",
    "platform_layers",
    "portability_status",
    "repo_local_boundaries",
    "shared_contracts",
]
