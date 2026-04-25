"""Build the typed connectivity registry used by map and closure guards."""

from __future__ import annotations

from pathlib import Path

from ..config import REPO_ROOT
from .blueprint import build_platform_blueprint
from .connectivity_registry_models import (
    ConnectivityContractRow,
    ConnectivityFieldRow,
    ConnectivityRegistrySnapshot,
    ConnectivityWriterRow,
)
from .contracts import ContractSpec, FrontendSurfaceSpec


def build_connectivity_registry_snapshot(
    *,
    repo_root: Path = REPO_ROOT,
    governed_surface_ids: tuple[str, ...] = (),
) -> ConnectivityRegistrySnapshot:
    """Build a single generated source for typed contract connectivity."""
    blueprint = build_platform_blueprint()
    frontend_surfaces = blueprint.frontend_surfaces
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
        governed_surface_ids=tuple(sorted(governed_surface_ids)),
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
    fields = tuple(
        ConnectivityFieldRow(
            field_name=field.name,
            type_hint=field.type_hint,
            field_kind="source",
            writer_ids=(writer.writer_id,),
            reader_ids=projection_ids,
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
        reader_ids=projection_ids,
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


__all__ = ["build_connectivity_registry_snapshot"]
