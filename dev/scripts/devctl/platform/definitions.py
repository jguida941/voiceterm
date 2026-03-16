"""Public reusable-platform definition exports."""

from .contract_definitions import shared_contracts
from .surface_definitions import (
    adoption_flow,
    caller_authority,
    frontend_surfaces,
    platform_layers,
    portability_status,
    repo_local_boundaries,
    service_lifecycle,
)

__all__ = [
    "adoption_flow",
    "caller_authority",
    "frontend_surfaces",
    "platform_layers",
    "portability_status",
    "repo_local_boundaries",
    "service_lifecycle",
    "shared_contracts",
]
