"""Canonical reusable-platform blueprint builder."""

from __future__ import annotations

from .contracts import PlatformBlueprint
from .definitions import (
    adoption_flow,
    artifact_schemas,
    caller_authority,
    frontend_surfaces,
    platform_layers,
    portability_status,
    repo_local_boundaries,
    service_lifecycle,
    shared_contracts,
)

THESIS = (
    "Executable local governance is the authority: the CLI/runtime owns typed "
    "actions, guards, artifacts, and approvals; frontends and adapters consume "
    "those contracts instead of replacing them."
)


def build_platform_blueprint() -> PlatformBlueprint:
    """Return the canonical shared-platform blueprint for repo and UI adopters."""
    return PlatformBlueprint(
        command="platform-contracts",
        schema_version=1,
        thesis=THESIS,
        layers=platform_layers(),
        shared_contracts=shared_contracts(),
        artifact_schemas=artifact_schemas(),
        frontend_surfaces=frontend_surfaces(),
        service_lifecycle=service_lifecycle(),
        caller_authority=caller_authority(),
        repo_local_boundaries=repo_local_boundaries(),
        adoption_flow=adoption_flow(),
        portability_status=portability_status(),
    )
