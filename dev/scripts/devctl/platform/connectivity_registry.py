"""Build the typed connectivity registry used by map and closure guards."""

from __future__ import annotations

import json
from pathlib import Path

from ..config import REPO_ROOT
from .blueprint import build_platform_blueprint
from .connectivity_registry_models import (
    ConnectivityContractRow,
    ConnectivityFieldRow,
    ConnectivityRegistrySummary,
    ConnectivityRegistrySnapshot,
    ConnectivityWriterRow,
)
from .contracts import ContractSpec, FrontendSurfaceSpec
from .policy_paths import resolve_repo_policy_path

CONNECTIVITY_REGISTRY_READER_IDS = (
    "context_graph",
    "render_surfaces",
    "session_resume",
    "startup_context",
    "system_map_index",
    "system_map_renderer",
)


def build_connectivity_registry_snapshot(
    *,
    repo_root: Path = REPO_ROOT,
    governed_surface_ids: tuple[str, ...] | None = None,
) -> ConnectivityRegistrySnapshot:
    """Build a single generated source for typed contract connectivity."""
    blueprint = build_platform_blueprint()
    frontend_surfaces = blueprint.frontend_surfaces
    resolved_governed_surface_ids = (
        governed_surface_ids
        if governed_surface_ids is not None
        else resolve_governed_surface_ids(repo_root=repo_root)
    )
    rows = tuple(
        _contract_row(
            contract,
            repo_root=repo_root,
            frontend_surfaces=frontend_surfaces,
        )
        for contract in blueprint.shared_contracts
    )
    warnings = _registry_warnings(rows)
    return ConnectivityRegistrySnapshot(
        schema_version=1,
        contract_id="ConnectivityRegistrySnapshot",
        source_contract_count=len(blueprint.shared_contracts),
        connected_contracts=rows,
        governed_surface_ids=tuple(sorted(resolved_governed_surface_ids)),
        warnings=warnings,
    )


def _contract_row(
    contract: ContractSpec,
    *,
    repo_root: Path,
    frontend_surfaces: tuple[FrontendSurfaceSpec, ...],
) -> ConnectivityContractRow:
    writer = _writer_for_contract(contract, repo_root=repo_root)
    projection_ids = _surface_ids_for_contract(
        contract.contract_id,
        frontend_surfaces=frontend_surfaces,
    )
    reader_ids = _reader_ids(projection_ids)
    fields = tuple(
        ConnectivityFieldRow(
            field_name=field.name,
            type_hint=field.type_hint,
            field_kind="source",
            writer_ids=(writer.writer_id,),
            reader_ids=reader_ids,
            projection_ids=projection_ids,
        )
        for field in contract.required_fields
    )
    return ConnectivityContractRow(
        contract_id=contract.contract_id,
        owner_layer=contract.owner_layer,
        runtime_model=contract.runtime_model,
        writer=writer,
        fields=fields,
        projection_ids=projection_ids,
        reader_ids=reader_ids,
    )


def _writer_for_contract(
    contract: ContractSpec,
    *,
    repo_root: Path,
) -> ConnectivityWriterRow:
    if not contract.runtime_model:
        return ConnectivityWriterRow(
            writer_id=f"contract:{contract.contract_id}:declared",
            path="",
            authority_kind="contract_declaration",
        )
    module_name, _, attr_name = contract.runtime_model.partition(":")
    rel_path = module_name.replace(".", "/") + ".py"
    if rel_path.startswith("dev/scripts/"):
        path = rel_path
    else:
        candidate = repo_root / rel_path
        path = candidate.as_posix() if candidate.exists() else rel_path
    return ConnectivityWriterRow(
        writer_id=f"{module_name}:{attr_name or contract.contract_id}",
        path=path,
        authority_kind="runtime_model",
    )


def _surface_ids_for_contract(
    contract_id: str,
    *,
    frontend_surfaces: tuple[FrontendSurfaceSpec, ...],
) -> tuple[str, ...]:
    return tuple(
        surface.surface_id
        for surface in frontend_surfaces
        if contract_id in surface.consumes_contracts
    )


def _reader_ids(projection_ids: tuple[str, ...]) -> tuple[str, ...]:
    """Return registry consumers plus contract-specific projection readers."""
    return tuple(sorted({*CONNECTIVITY_REGISTRY_READER_IDS, *projection_ids}))


def _registry_warnings(
    rows: tuple[ConnectivityContractRow, ...],
) -> tuple[str, ...]:
    warnings: list[str] = []
    for row in rows:
        for field in row.fields:
            if field.field_kind == "source" and len(field.writer_ids) != 1:
                warnings.append(
                    f"{row.contract_id}.{field.field_name} has "
                    f"{len(field.writer_ids)} source writers"
                )
            if field.field_kind == "derived" and not field.derived_from:
                warnings.append(
                    f"{row.contract_id}.{field.field_name} is derived without source refs"
                )
    return tuple(warnings)


def resolve_governed_surface_ids(
    *,
    repo_root: Path = REPO_ROOT,
    policy_path: str | Path | None = None,
) -> tuple[str, ...]:
    """Return repo-pack governed surface ids from repo policy, if available."""
    resolved_policy_path = resolve_repo_policy_path(
        repo_root=repo_root,
        policy_path=policy_path,
    )
    try:
        payload = json.loads(resolved_policy_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ()
    repo_governance = payload.get("repo_governance")
    if not isinstance(repo_governance, dict):
        return ()
    surface_generation = repo_governance.get("surface_generation")
    if not isinstance(surface_generation, dict):
        return ()
    surfaces = surface_generation.get("surfaces")
    if not isinstance(surfaces, list):
        return ()
    surface_ids: list[str] = []
    for entry in surfaces:
        if not isinstance(entry, dict):
            continue
        surface_id = str(entry.get("id") or "").strip()
        if surface_id and surface_id not in surface_ids:
            surface_ids.append(surface_id)
    return tuple(surface_ids)

def summarize_connectivity_registry(
    registry: ConnectivityRegistrySnapshot,
) -> ConnectivityRegistrySummary:
    """Build the bounded summary shared by startup and render surfaces."""
    field_count = sum(len(contract.fields) for contract in registry.connected_contracts)
    zero_reader_count = sum(
        1
        for contract in registry.connected_contracts
        for field in contract.fields
        if not field.reader_ids
    )
    reader_ids = sorted(
        {
            reader_id
            for contract in registry.connected_contracts
            for reader_id in (*contract.reader_ids, *contract.projection_ids)
            if reader_id
        }
        | {
            reader_id
            for contract in registry.connected_contracts
            for field in contract.fields
            for reader_id in (*field.reader_ids, *field.projection_ids)
            if reader_id
        }
        | set(registry.governed_surface_ids)
    )
    return ConnectivityRegistrySummary(
        schema_version=registry.schema_version,
        contract_id=registry.contract_id,
        source_contract_count=registry.source_contract_count,
        connected_contract_count=len(registry.connected_contracts),
        source_field_count=field_count,
        zero_reader_field_count=zero_reader_count,
        reader_ids=tuple(reader_ids),
        governed_surface_ids=registry.governed_surface_ids,
        warning_count=len(registry.warnings),
        warnings=registry.warnings,
    )


def build_connectivity_registry_summary(
    *,
    repo_root: Path = REPO_ROOT,
    governed_surface_ids: tuple[str, ...] | None = None,
) -> ConnectivityRegistrySummary:
    """Build the bounded connectivity-registry summary for consumers."""
    return summarize_connectivity_registry(
        build_connectivity_registry_snapshot(
            repo_root=repo_root,
            governed_surface_ids=governed_surface_ids,
        )
    )


__all__ = [
    "CONNECTIVITY_REGISTRY_READER_IDS",
    "build_connectivity_registry_snapshot",
    "build_connectivity_registry_summary",
    "resolve_governed_surface_ids",
    "summarize_connectivity_registry",
]
