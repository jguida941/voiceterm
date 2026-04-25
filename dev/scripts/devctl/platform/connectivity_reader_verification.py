"""Classify declared ConnectivityRegistry reader connections."""

from __future__ import annotations

from pathlib import Path

from ..config import REPO_ROOT
from .blueprint import build_platform_blueprint
from .connectivity_reader_overrides import (
    DEFAULT_READER_OVERRIDE_PATH,
    MISSING_CONNECTION_CLASSIFICATIONS,
    ReaderConnectionOverride,
    load_reader_overrides,
    override_is_usable,
)
from .connectivity_reader_sources import (
    READER_SOURCE_PATHS,
    ReaderSourceEvidence,
    reader_evidence_by_id,
    reader_paths,
    reader_source_evidence,
    relative_reader_path,
)
from .connectivity_registry_models import (
    ConnectivityContractRow,
    ConnectivityRegistrySnapshot,
    MissingConnectionFinding,
)

_REGISTRY_SUMMARY_BUILDERS = frozenset(
    (
        "build_connectivity_registry_snapshot",
        "build_connectivity_registry_summary",
        "summarize_connectivity_registry",
    )
)

_REGISTRY_ROW_ATTRS = frozenset(
    (
        "connected_contracts",
        "contract_id",
        "fields",
        "field_name",
        "projection_ids",
        "reader_ids",
        "required_fields",
        "runtime_model",
        "writer",
        "writer_ids",
    )
)


def find_missing_connection_findings(
    *,
    registry: ConnectivityRegistrySnapshot,
    required_reader_ids: tuple[str, ...],
    row_reader_ids: tuple[str, ...],
    repo_root: Path = REPO_ROOT,
    override_path: str | Path | None = None,
) -> tuple[MissingConnectionFinding, ...]:
    """Return typed findings for declared readers without source evidence."""
    evidence_by_id = reader_evidence_by_id(repo_root=repo_root)
    known_reader_ids = known_connectivity_reader_ids(
        registry=registry,
        required_reader_ids=required_reader_ids,
        row_reader_ids=row_reader_ids,
    )
    overrides = load_reader_overrides(
        repo_root=repo_root,
        override_path=override_path,
    )
    findings: list[MissingConnectionFinding] = []
    for contract in registry.connected_contracts:
        for reader_id in contract.reader_ids:
            if reader_id not in known_reader_ids:
                continue
            evidence = evidence_by_id.get(reader_id, ())
            if reader_has_contract_evidence(
                contract=contract,
                reader_id=reader_id,
                evidence=evidence,
                row_reader_ids=row_reader_ids,
            ):
                continue
            findings.append(
                _missing_connection_finding(
                    contract=contract,
                    reader_id=reader_id,
                    row_reader_ids=row_reader_ids,
                    repo_root=repo_root,
                    override=overrides.get((contract.contract_id, reader_id)),
                )
            )
    return tuple(findings)


def known_connectivity_reader_ids(
    *,
    registry: ConnectivityRegistrySnapshot,
    required_reader_ids: tuple[str, ...],
    row_reader_ids: tuple[str, ...],
) -> frozenset[str]:
    """Return every reader id declared by registry, blueprint, or repo policy."""
    frontend_surface_ids = {
        surface.surface_id for surface in build_platform_blueprint().frontend_surfaces
    }
    return frozenset(
        {
            *required_reader_ids,
            *row_reader_ids,
            *frontend_surface_ids,
            *registry.governed_surface_ids,
        }
    )


def reader_has_contract_evidence(
    *,
    contract: ConnectivityContractRow,
    reader_id: str,
    evidence: tuple[ReaderSourceEvidence, ...],
    row_reader_ids: tuple[str, ...],
) -> bool:
    """Return whether a reader has AST-visible evidence for a contract row."""
    if not evidence:
        return False
    runtime_symbol = _runtime_symbol(contract)
    contract_tokens = frozenset(
        token for token in (contract.contract_id, runtime_symbol) if token
    )
    for item in evidence:
        if (
            contract_tokens & item.names
            or contract_tokens & item.calls
            or contract_tokens & item.strings
        ):
            return True
        if reader_id in row_reader_ids and _has_registry_row_projection(item):
            return True
    return False


def _missing_connection_finding(
    *,
    contract: ConnectivityContractRow,
    reader_id: str,
    row_reader_ids: tuple[str, ...],
    repo_root: Path,
    override: ReaderConnectionOverride | None,
) -> MissingConnectionFinding:
    classification = "aspirational_gap"
    justification = ""
    override_ref = ""
    if override is not None and override_is_usable(override):
        classification = override.classification
        justification = override.justification
        override_ref = override.override_ref
    return MissingConnectionFinding(
        contract_id=contract.contract_id,
        declared_reader_surface=reader_id,
        expected_evidence_kind=_expected_evidence_kind(
            reader_id=reader_id,
            contract=contract,
            row_reader_ids=row_reader_ids,
        ),
        suggested_wire_locations=_suggested_wire_locations(
            reader_id=reader_id,
            repo_root=repo_root,
        ),
        classification=classification,
        justification=justification,
        override_ref=override_ref,
    )


def _expected_evidence_kind(
    *,
    reader_id: str,
    contract: ConnectivityContractRow,
    row_reader_ids: tuple[str, ...],
) -> str:
    if reader_id in row_reader_ids:
        return "registry_row_projection"
    if reader_id in contract.projection_ids:
        return "frontend_contract_projection"
    return "contract_symbol_import_or_literal"


def _suggested_wire_locations(
    *,
    reader_id: str,
    repo_root: Path,
) -> tuple[str, ...]:
    paths = tuple(
        relative_reader_path(path=path, repo_root=repo_root)
        for path in reader_paths(reader_id=reader_id, repo_root=repo_root)
    )
    if paths:
        return paths
    return (f"reader_surface:{reader_id}",)


def _has_registry_row_projection(evidence: ReaderSourceEvidence) -> bool:
    has_registry_loader = bool(
        _REGISTRY_SUMMARY_BUILDERS & (evidence.names | evidence.calls)
    )
    has_contract_model = "ContractSpec" in evidence.names
    projected_attrs = _REGISTRY_ROW_ATTRS & evidence.attrs
    return (
        (has_registry_loader or has_contract_model)
        and "contract_id" in projected_attrs
        and bool(projected_attrs)
    )


def _runtime_symbol(contract: ConnectivityContractRow) -> str:
    _module, _separator, symbol = contract.runtime_model.partition(":")
    return symbol


__all__ = [
    "DEFAULT_READER_OVERRIDE_PATH",
    "MISSING_CONNECTION_CLASSIFICATIONS",
    "READER_SOURCE_PATHS",
    "ReaderConnectionOverride",
    "ReaderSourceEvidence",
    "find_missing_connection_findings",
    "known_connectivity_reader_ids",
    "load_reader_overrides",
    "reader_evidence_by_id",
    "reader_has_contract_evidence",
    "reader_paths",
    "reader_source_evidence",
]
