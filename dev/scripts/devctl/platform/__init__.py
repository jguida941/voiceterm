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
from .extension_bundle_projection import (
    build_extension_bundle_projection,
    render_extension_bundle_projection_markdown,
    resolve_extension_bundle,
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
    "build_extension_bundle_projection",
    "render_platform_blueprint_markdown",
    "render_extension_bundle_projection_markdown",
    "resolve_extension_bundle",
]
