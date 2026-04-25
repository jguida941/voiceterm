"""Connectivity-registry closure proof for platform contract checks."""

from __future__ import annotations

from dev.scripts.devctl.config import REPO_ROOT
from dev.scripts.devctl.governance.surfaces import SurfacePolicy
from dev.scripts.devctl.platform.connectivity_registry import (
    CONNECTIVITY_REGISTRY_READER_IDS,
    build_connectivity_registry_snapshot,
    summarize_connectivity_registry,
)


def check_connectivity_registry_closure(
    policy: SurfacePolicy,
) -> tuple[dict[str, object], tuple[dict[str, object], ...]]:
    governed_surface_ids = tuple(surface.surface_id for surface in policy.surfaces)
    registry = build_connectivity_registry_snapshot(
        repo_root=REPO_ROOT,
        governed_surface_ids=governed_surface_ids,
    )
    summary = summarize_connectivity_registry(registry)
    missing_reader_ids = tuple(
        reader_id
        for reader_id in CONNECTIVITY_REGISTRY_READER_IDS
        if reader_id not in summary.reader_ids
    )
    ok = not missing_reader_ids and summary.zero_reader_field_count == 0
    coverage = {
        "kind": "connectivity_registry_closure",
        "contract_id": registry.contract_id,
        "source_contract_count": summary.source_contract_count,
        "connected_contract_count": summary.connected_contract_count,
        "source_field_count": summary.source_field_count,
        "zero_reader_field_count": summary.zero_reader_field_count,
        "required_reader_ids": CONNECTIVITY_REGISTRY_READER_IDS,
        "observed_reader_ids": summary.reader_ids,
        "ok": ok,
        "detail": (
            "ConnectivityRegistrySnapshot has startup, session, graph, render, and SYSTEM_MAP consumers."
            if ok
            else "ConnectivityRegistrySnapshot is missing required consumers or has zero-reader fields."
        ),
    }
    if ok:
        return coverage, ()
    return coverage, _connectivity_registry_violations(
        contract_id=registry.contract_id,
        missing_reader_ids=missing_reader_ids,
        zero_reader_field_count=summary.zero_reader_field_count,
    )


def _connectivity_registry_violations(
    *,
    contract_id: str,
    missing_reader_ids: tuple[str, ...],
    zero_reader_field_count: int,
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
                "detail": "ConnectivityRegistrySnapshot contains field rows with no reader ids.",
            }
        )
    return tuple(violations)
