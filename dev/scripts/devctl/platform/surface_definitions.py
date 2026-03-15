"""Layer, surface, and portability definitions for the platform blueprint."""

from __future__ import annotations

from .contracts import (
    FrontendSurfaceSpec,
    PlatformLayerSpec,
    PortabilityStatusSpec,
    RepoBoundarySpec,
)


def platform_layers() -> tuple[PlatformLayerSpec, ...]:
    return (
        PlatformLayerSpec(
            layer_id="governance_core",
            purpose=(
                "Portable guard/probe engine, policy resolution, bootstrap, "
                "export, review ledger, and evaluation artifacts."
            ),
            current_home="dev/scripts/checks/ and dev/scripts/devctl/",
        ),
        PlatformLayerSpec(
            layer_id="governance_runtime",
            purpose=(
                "Typed runtime state, action execution, run records, and "
                "artifact-store contracts shared by CLI/UI surfaces."
            ),
            current_home="emerging under dev/scripts/devctl/ (not extracted yet)",
        ),
        PlatformLayerSpec(
            layer_id="governance_adapters",
            purpose=(
                "Provider, workflow, CI, VCS, and notifier integrations over "
                "the shared runtime."
            ),
            current_home="distributed across dev/scripts/devctl/ and workflows/",
        ),
        PlatformLayerSpec(
            layer_id="governance_frontends",
            purpose=(
                "CLI, PyQt6, overlay/TUI, phone/mobile, and optional MCP "
                "surfaces over one backend."
            ),
            current_home="devctl CLI plus repo-local UI surfaces",
        ),
        PlatformLayerSpec(
            layer_id="repo_packs",
            purpose=(
                "Repo-local policy, workflow defaults, docs templates, and "
                "bounded repo-specific glue."
            ),
            current_home="dev/config/ plus target-repo generated assets",
        ),
    )


def frontend_surfaces() -> tuple[FrontendSurfaceSpec, ...]:
    return (
        FrontendSurfaceSpec(
            surface_id="cli",
            authority="canonical execution surface",
            consumes_contracts=("RepoPack", "TypedAction", "RunRecord", "ArtifactStore"),
            notes="`devctl` remains the default operator and AI execution path.",
        ),
        FrontendSurfaceSpec(
            surface_id="pyqt6_operator_console",
            authority="thin client",
            consumes_contracts=("ControlState", "TypedAction", "ArtifactStore"),
            notes="Desktop UI must project typed backend state, not become a second backend.",
        ),
        FrontendSurfaceSpec(
            surface_id="overlay_tui",
            authority="thin client",
            consumes_contracts=("ControlState", "TypedAction"),
            notes="VoiceTerm overlay may observe and dispatch typed actions only.",
        ),
        FrontendSurfaceSpec(
            surface_id="phone_mobile",
            authority="thin client",
            consumes_contracts=("ControlState", "RunRecord", "ArtifactStore"),
            notes="Phone-safe projections should reuse the same state model as desktop and CLI.",
        ),
        FrontendSurfaceSpec(
            surface_id="mcp",
            authority="optional adapter",
            consumes_contracts=("ControlState", "RunRecord"),
            notes="MCP remains additive transport, not the release/safety authority.",
        ),
    )


def repo_local_boundaries() -> tuple[RepoBoundarySpec, ...]:
    return (
        RepoBoundarySpec(
            boundary_id="canonical_docs_and_release_policy",
            lives_in="repo pack policy and repo docs",
            reason="Canonical doc sets, branch rules, and release paths differ per repo.",
        ),
        RepoBoundarySpec(
            boundary_id="repo_layout_thresholds_and_allowlists",
            lives_in="repo policy and repo pack defaults",
            reason="Path/layout constraints and allowlists must be swappable without patching the engine.",
        ),
        RepoBoundarySpec(
            boundary_id="product_specific_frontend_branding",
            lives_in="product integration layer",
            reason="VoiceTerm UI/branding should not leak into portable platform logic.",
        ),
    )


def adoption_flow() -> tuple[str, ...]:
    return (
        "Install the reusable platform package and CLI entrypoint.",
        "Run governance-bootstrap against the target repo.",
        "Generate or select a RepoPack and repo policy.",
        "Run quality-policy to inspect the resolved guard/probe surface.",
        "Run check --adoption-scan and probe-report for first-pass intake.",
        "Enable the desired frontend clients over the same backend contracts.",
    )


def portability_status() -> tuple[PortabilityStatusSpec, ...]:
    return (
        PortabilityStatusSpec(
            surface_id="governance_core",
            status="portable-ready",
            current_owner="quality policy, checks, probes, bootstrap, export",
            next_step="Package the core cleanly so it can ship outside VoiceTerm.",
        ),
        PortabilityStatusSpec(
            surface_id="review_channel_and_control_state",
            status="partial",
            current_owner="review-channel and control-plane packages inside devctl",
            next_step="Move review and control-state payloads onto the shared runtime contracts.",
        ),
        PortabilityStatusSpec(
            surface_id="ralph_loop",
            status="partial",
            current_owner="repo-local workflow/control-plane logic",
            next_step="Replace VoiceTerm-specific workflow assumptions with WorkflowAdapter contracts.",
        ),
        PortabilityStatusSpec(
            surface_id="mutation_loop",
            status="partial",
            current_owner="repo-local mutation tooling and workflow glue",
            next_step="Split mutation execution/reporting from repo-pack defaults and branch policy.",
        ),
        PortabilityStatusSpec(
            surface_id="process_hygiene",
            status="partial",
            current_owner="repo-local host cleanup/audit commands",
            next_step="Extract reusable host-process contracts while keeping repo-specific kill policy in repo packs.",
        ),
        PortabilityStatusSpec(
            surface_id="pyqt6_and_mobile_clients",
            status="frontend-ready_after_runtime",
            current_owner="repo-local UI/control-plane surfaces",
            next_step="Point all UI clients at one shared ControlState and TypedAction backend.",
        ),
    )
