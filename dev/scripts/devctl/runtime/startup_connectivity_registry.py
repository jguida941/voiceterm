"""Startup projection for the ConnectivityRegistry closure summary."""

from __future__ import annotations

from pathlib import Path

from ..platform.connectivity_reader_verification import find_missing_connection_findings
from ..platform.connectivity_registry import (
    CONNECTIVITY_REGISTRY_READER_IDS,
    CONNECTIVITY_REGISTRY_ROW_READER_IDS,
    build_connectivity_registry_snapshot,
    summarize_connectivity_registry,
)
from ..platform.connectivity_registry_models import (
    ConnectivityRegistrySnapshot,
    ConnectivityRegistrySummary,
)


def startup_connectivity_registry(repo_root: Path) -> dict[str, object]:
    """Project the connectivity registry summary into the startup payload."""
    registry = build_connectivity_registry_snapshot(repo_root=repo_root)
    missing_connection_findings = find_missing_connection_findings(
        registry=registry,
        required_reader_ids=CONNECTIVITY_REGISTRY_READER_IDS,
        row_reader_ids=CONNECTIVITY_REGISTRY_ROW_READER_IDS,
        repo_root=repo_root,
    )
    return _connectivity_registry_summary_dict(
        summarize_connectivity_registry(
            registry,
            missing_connection_findings=missing_connection_findings,
        ),
        registry=registry,
    )


def _connectivity_registry_summary_dict(
    summary: ConnectivityRegistrySummary,
    *,
    registry: ConnectivityRegistrySnapshot,
) -> dict[str, object]:
    payload = summary.to_dict()
    payload["connected_contract_ids"] = tuple(
        contract.contract_id for contract in registry.connected_contracts
    )
    return payload
