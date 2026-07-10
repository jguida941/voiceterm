"""Connectivity-registry closure proof for platform contract checks."""

from __future__ import annotations

from dev.scripts.devctl.config import REPO_ROOT
from dev.scripts.devctl.governance.surfaces import SurfacePolicy
from dev.scripts.devctl.platform.connectivity_registry import (
    CONNECTIVITY_REGISTRY_READER_IDS,
    CONNECTIVITY_REGISTRY_ROW_READER_IDS,
    build_connectivity_registry_snapshot,
    summarize_connectivity_registry,
)
from dev.scripts.devctl.platform.connectivity_reader_verification import (
    find_missing_connection_findings,
)

from .connectivity_reader_verification import reader_verification_violations


def check_connectivity_registry_closure(
    policy: SurfacePolicy,
) -> tuple[dict[str, object], tuple[dict[str, object], ...]]:
    governed_surface_ids = tuple(surface.surface_id for surface in policy.surfaces)
    registry = build_connectivity_registry_snapshot(
        repo_root=REPO_ROOT,
        governed_surface_ids=governed_surface_ids,
    )
    missing_connection_findings = find_missing_connection_findings(
        registry=registry,
        required_reader_ids=CONNECTIVITY_REGISTRY_READER_IDS,
        row_reader_ids=CONNECTIVITY_REGISTRY_ROW_READER_IDS,
        repo_root=REPO_ROOT,
    )
    summary = summarize_connectivity_registry(
        registry,
        missing_connection_findings=missing_connection_findings,
    )
    missing_reader_ids = tuple(
        reader_id
        for reader_id in CONNECTIVITY_REGISTRY_READER_IDS
        if reader_id not in summary.reader_ids
    )
    reader_violations = reader_verification_violations(
        registry=registry,
        policy=policy,
        missing_connection_findings=missing_connection_findings,
    )
    ok = (
        not missing_reader_ids
        and summary.zero_reader_field_count == 0
        and summary.aspirational_gap_count == 0
        and not reader_violations
    )
    coverage = {
        "kind": "connectivity_registry_closure",
        "contract_id": registry.contract_id,
        "source_contract_count": summary.source_contract_count,
        "connected_contract_count": summary.connected_contract_count,
        "source_field_count": summary.source_field_count,
        "zero_reader_field_count": summary.zero_reader_field_count,
        "required_reader_ids": CONNECTIVITY_REGISTRY_READER_IDS,
        "observed_reader_ids": summary.reader_ids,
        "row_reader_ids": CONNECTIVITY_REGISTRY_ROW_READER_IDS,
        "missing_connection_finding_count": (
            summary.missing_connection_finding_count
        ),
        "aspirational_gap_count": summary.aspirational_gap_count,
        "mistakenly_declared_count": summary.mistakenly_declared_count,
        "deferred_consumer_count": summary.deferred_consumer_count,
        "missing_connection_findings": tuple(
            finding.to_dict() for finding in missing_connection_findings
        ),
        "reader_verification_violation_count": len(reader_violations),
        "ok": ok,
        "detail": (
            "ConnectivityRegistrySnapshot has startup, session, graph, render, "
            "and SYSTEM_MAP consumers; aspirational_gap_count is 0; and contract "
            "reader rows are AST-verified."
            if ok
            else (
                "ConnectivityRegistrySnapshot is missing required consumers, "
                "has zero-reader fields, or has unverified declared readers."
            )
        ),
    }
    if ok:
        return coverage, ()
    return coverage, _connectivity_registry_violations(
        contract_id=registry.contract_id,
        missing_reader_ids=missing_reader_ids,
        zero_reader_field_count=summary.zero_reader_field_count,
        reader_violations=reader_violations,
    )


def _connectivity_registry_violations(
    *,
    contract_id: str,
    missing_reader_ids: tuple[str, ...],
    zero_reader_field_count: int,
    reader_violations: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    violations: list[dict[str, object]] = []
    if missing_reader_ids:
        violations.append(
            {
                "kind": "connectivity_registry_closure",
                "contract_id": contract_id,
                "rule": "missing-connectivity-registry-consumer",
                "missing_reader_ids": missing_reader_ids,
                "detail": (
                    "ConnectivityRegistrySnapshot must be consumed by graph, startup, "
                    "session-resume, render-surfaces, and SYSTEM_MAP surfaces."
                ),
            }
        )
    if zero_reader_field_count:
        violations.append(
            {
                "kind": "connectivity_registry_closure",
                "contract_id": contract_id,
                "rule": "zero-reader-connectivity-field",
                "zero_reader_field_count": zero_reader_field_count,
                "detail": (
                    "ConnectivityRegistrySnapshot contains field rows with no reader ids."
                ),
            }
        )
    violations.extend(reader_violations)
    return tuple(violations)
