"""Reader verification rules for ConnectivityRegistry rows."""

from __future__ import annotations

from dev.scripts.devctl.platform.connectivity_registry import (
    CONNECTIVITY_REGISTRY_READER_IDS,
    CONNECTIVITY_REGISTRY_ROW_READER_IDS,
)
from dev.scripts.devctl.platform.connectivity_registry_models import (
    ConnectivityRegistrySnapshot,
    MissingConnectionFinding,
)
from dev.scripts.devctl.platform.connectivity_reader_verification import (
    find_missing_connection_findings,
    known_connectivity_reader_ids,
)


def reader_verification_violations(
    *,
    registry: ConnectivityRegistrySnapshot,
    policy: object,
    missing_connection_findings: tuple[MissingConnectionFinding, ...] | None = None,
) -> tuple[dict[str, object], ...]:
    del policy
    findings = (
        missing_connection_findings
        if missing_connection_findings is not None
        else find_missing_connection_findings(
            registry=registry,
            required_reader_ids=CONNECTIVITY_REGISTRY_READER_IDS,
            row_reader_ids=CONNECTIVITY_REGISTRY_ROW_READER_IDS,
        )
    )
    known_reader_ids = known_connectivity_reader_ids(
        registry=registry,
        required_reader_ids=CONNECTIVITY_REGISTRY_READER_IDS,
        row_reader_ids=CONNECTIVITY_REGISTRY_ROW_READER_IDS,
    )
    violations: list[dict[str, object]] = []
    for contract in registry.connected_contracts:
        for reader_id in contract.reader_ids:
            if reader_id not in known_reader_ids:
                violations.append(
                    _unknown_reader_violation(
                        contract_id=contract.contract_id,
                        reader_id=reader_id,
                        writer_path=contract.writer.path,
                        runtime_model=contract.runtime_model,
                    )
                )
    for finding in findings:
        if finding.classification != "aspirational_gap":
            continue
        row = _row_for_finding(finding=finding, registry=registry)
        violations.append(
            _missing_connection_violation(
                finding=finding,
                writer_path=row.writer.path if row is not None else "",
                runtime_model=row.runtime_model if row is not None else "",
            )
        )
    return tuple(violations)


def _unknown_reader_violation(
    *,
    contract_id: str,
    reader_id: str,
    writer_path: str,
    runtime_model: str,
) -> dict[str, object]:
    return {
        "kind": "connectivity_registry_closure",
        "contract_id": contract_id,
        "reader_id": reader_id,
        "rule": "unknown-connectivity-reader",
        "writer_path": writer_path,
        "runtime_model": runtime_model,
        "detail": (
            "ConnectivityRegistry row declares a reader id that is not registered "
            "in frontend, repo-pack, or registry-reader policy."
        ),
    }


def _missing_connection_violation(
    *,
    finding: MissingConnectionFinding,
    writer_path: str,
    runtime_model: str,
) -> dict[str, object]:
    return {
        "kind": "connectivity_registry_closure",
        "contract_id": finding.contract_id,
        "reader_id": finding.declared_reader_surface,
        "rule": "aspirational-connectivity-gap",
        "classification": finding.classification,
        "expected_evidence_kind": finding.expected_evidence_kind,
        "suggested_wire_locations": finding.suggested_wire_locations,
        "writer_path": writer_path,
        "runtime_model": runtime_model,
        "detail": (
            "ConnectivityRegistry row declares an aspirational reader connection "
            "without AST-visible evidence. Wire the reader or add a justified "
            "registry-reader override."
        ),
    }


def _row_for_finding(
    *,
    finding: MissingConnectionFinding,
    registry: ConnectivityRegistrySnapshot,
):
    for row in registry.connected_contracts:
        if row.contract_id == finding.contract_id:
            return row
    return None
