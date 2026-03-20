"""Markdown rendering for reusable-platform blueprints."""

from __future__ import annotations

from .contracts import ArtifactSchemaSpec, ContractField, ContractSpec, PlatformBlueprint


def _render_field(field: ContractField) -> str:
    return f"  - {field.name}: {field.type_hint} — {field.description}"


def _render_contract(contract: ContractSpec) -> list[str]:
    lines = [
        (
            f"- {contract.contract_id}: owner_layer={contract.owner_layer}; "
            f"{contract.purpose}"
        )
    ]
    if contract.runtime_model:
        lines.append(f"  - runtime_model: {contract.runtime_model}")
    if contract.startup_surface_tokens:
        lines.append(
            "  - startup_surface_tokens: "
            + ", ".join(contract.startup_surface_tokens)
        )
    lines.extend(_render_field(field) for field in contract.required_fields)
    return lines


def _render_artifact_schema(spec: ArtifactSchemaSpec) -> list[str]:
    return [
        (
            f"- {spec.contract_id}: owner_layer={spec.owner_layer}; "
            f"schema_version={spec.schema_version}; {spec.purpose}"
        ),
        f"  - emitter_path: {spec.emitter_path}",
        (
            "  - constants: "
            f"{spec.constants_module}.{spec.contract_id_attr} / "
            f"{spec.constants_module}.{spec.schema_version_attr}"
        ),
        f"  - compatibility_window: {spec.compatibility_window}",
        f"  - migration_path: {spec.migration_path}",
        f"  - rollback_path: {spec.rollback_path}",
    ]


def render_platform_blueprint_markdown(blueprint: PlatformBlueprint) -> str:
    """Render the platform blueprint in maintainer-friendly markdown."""
    lines = ["# devctl platform-contracts", ""]
    lines.append(f"- command: {blueprint.command}")
    lines.append(f"- schema_version: {blueprint.schema_version}")
    lines.append(f"- layer_count: {len(blueprint.layers)}")
    lines.append(f"- shared_contract_count: {len(blueprint.shared_contracts)}")
    lines.append(f"- artifact_schema_count: {len(blueprint.artifact_schemas)}")
    lines.append(f"- frontend_surface_count: {len(blueprint.frontend_surfaces)}")
    lines.append(f"- service_lifecycle_count: {len(blueprint.service_lifecycle)}")
    lines.append(f"- caller_authority_count: {len(blueprint.caller_authority)}")
    lines.append(f"- repo_boundary_count: {len(blueprint.repo_local_boundaries)}")
    lines.extend(["", "## Thesis", "", blueprint.thesis, "", "## Platform Layers", ""])
    for layer in blueprint.layers:
        lines.append(
            f"- {layer.layer_id}: {layer.purpose} Current home: {layer.current_home}"
        )
    lines.extend(["", "## Shared Contracts", ""])
    for contract in blueprint.shared_contracts:
        lines.extend(_render_contract(contract))
    lines.extend(["", "## Artifact Schema Matrix", ""])
    for spec in blueprint.artifact_schemas:
        lines.extend(_render_artifact_schema(spec))
    lines.extend(["", "## Frontend Surfaces", ""])
    for surface in blueprint.frontend_surfaces:
        contracts = ", ".join(surface.consumes_contracts)
        lines.append(
            f"- {surface.surface_id}: authority={surface.authority}; "
            f"consumes={contracts}; {surface.notes}"
        )
    lines.extend(["", "## Service Lifecycle", ""])
    for spec in blueprint.service_lifecycle:
        launch = ", ".join(spec.launch_entrypoints)
        discovery = ", ".join(spec.discovery_fields)
        health = ", ".join(spec.health_signals)
        shutdown = ", ".join(spec.shutdown_entrypoints)
        lines.append(
            f"- {spec.service_id}: launch={launch}; discovery={discovery}; "
            f"health={health}; shutdown={shutdown}; {spec.notes}"
        )
    lines.extend(["", "## Caller Authority", ""])
    for spec in blueprint.caller_authority:
        allowed = ", ".join(spec.allowed_actions) or "none"
        stage_only = ", ".join(spec.stage_only_actions) or "none"
        approval = ", ".join(spec.approval_required_actions) or "none"
        forbidden = ", ".join(spec.forbidden_actions) or "none"
        lines.append(
            f"- {spec.caller_id}: allowed={allowed}; stage_only={stage_only}; "
            f"approval_required={approval}; forbidden={forbidden}"
        )
    lines.extend(["", "## Repo-Local Boundaries", ""])
    for boundary in blueprint.repo_local_boundaries:
        lines.append(
            f"- {boundary.boundary_id}: lives_in={boundary.lives_in}; {boundary.reason}"
        )
    lines.extend(["", "## Adoption Flow", ""])
    for step in blueprint.adoption_flow:
        lines.append(f"- {step}")
    lines.extend(["", "## Current Portability Status", ""])
    for status in blueprint.portability_status:
        lines.append(
            f"- {status.surface_id}: status={status.status}; "
            f"owner={status.current_owner}; next_step={status.next_step}"
        )
    return "\n".join(lines)
