"""Reusable AI-governance platform blueprint surfaces."""

from .blueprint import build_platform_blueprint
from .contracts import (
    ArtifactSchemaSpec,
    CallerAuthoritySpec,
    ContractField,
    ContractSpec,
    FrontendSurfaceSpec,
    PlatformBlueprint,
    PlatformLayerSpec,
    PortabilityStatusSpec,
    RepoBoundarySpec,
    ServiceLifecycleSpec,
)
from .render import render_platform_blueprint_markdown

__all__ = [
    "ArtifactSchemaSpec",
    "ContractField",
    "ContractSpec",
    "CallerAuthoritySpec",
    "FrontendSurfaceSpec",
    "PlatformBlueprint",
    "PlatformLayerSpec",
    "PortabilityStatusSpec",
    "RepoBoundarySpec",
    "ServiceLifecycleSpec",
    "build_platform_blueprint",
    "render_platform_blueprint_markdown",
]
