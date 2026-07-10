"""Projection helpers for worktree-orphan snapshots."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import replace
from pathlib import Path
from typing import Protocol, runtime_checkable

from ..config import REPO_ROOT
from .session_lease_contracts import SessionLease
from .work_publication_ledger_contracts import WorkPublicationLedger
from .worktree_orphan_inventory_builder import build_orphan_inventory_report
from .worktree_orphan_inventory_report import OrphanInventoryReport
from .worktree_orphan_inventory_support import inventory_stats
from .worktree_orphan_snapshot import OrphanSnapshot, OrphanSource

_EPHEMERAL_SOURCE_METADATA_KEYS = frozenset(
    {
        "inventory_generated_at_utc",
        "inventory_report_id",
        "snapshot_projection",
    }
)


@runtime_checkable
class SupportsToDict(Protocol):
    """Typed review-state values that can project themselves to a mapping."""

    def to_dict(self) -> Mapping[str, object]: ...


def build_orphan_snapshot_projection(
    *,
    repo_root: Path = REPO_ROOT,
    review_state: Mapping[str, object] | SupportsToDict | None = None,
    scan_scope: str = "bounded_local",
    scan_trigger: str = "startup_context",
    freshness_requirement: str = "fresh_scan_required",
) -> OrphanSnapshot:
    """Build a fresh bounded orphan snapshot for read-side consumers."""
    inventory = build_orphan_inventory_report(
        repo_root=repo_root,
        review_state=_review_state_mapping(review_state),
        scan_scope=scan_scope,
    )
    return compute_orphan_snapshot(
        inventory,
        ledger=None,
        leases=(),
        scan_trigger=scan_trigger,
        freshness_requirement=freshness_requirement,
    )


def compute_orphan_snapshot(
    inventory: OrphanInventoryReport,
    ledger: WorkPublicationLedger | None = None,
    leases: Sequence[SessionLease] | None = None,
    *,
    scan_trigger: str = "read_projection",
    freshness_requirement: str = "fresh_scan_required",
) -> OrphanSnapshot:
    """Derive a deterministic OrphanSnapshot from an inventory report.

    This is intentionally pure: callers own the inventory scan and any
    ledger/lease loading. Slice 3 keeps empty ledger/lease inputs explicit so
    later enforcement slices can distinguish "not loaded yet" from "clean."
    """
    lease_rows = tuple(leases or ())
    lease_source = _lease_source(lease_rows)
    ledger_ref = _ledger_ref(ledger)
    sources = tuple(
        _enriched_source(
            source,
            inventory=inventory,
            ledger_ref=ledger_ref,
            lease_source=lease_source,
            lease_rows=lease_rows,
        )
        for source in sorted(inventory.sources, key=_source_sort_key)
    )
    stats = inventory_stats(list(sources))
    derived_from = _derived_from(
        inventory=inventory,
        ledger_ref=ledger_ref,
        lease_source=lease_source,
        lease_count=len(lease_rows),
    )
    hash_basis = {
        "derived_from": derived_from,
        "freshness_requirement": freshness_requirement,
        "ledger_ref": ledger_ref,
        "lease_source": lease_source,
    }
    snapshot_hash = _snapshot_hash(
        inventory=inventory,
        sources=sources,
        stats=stats.to_dict(),
        basis=hash_basis,
    )
    return OrphanSnapshot(
        snapshot_id=f"orphan-snapshot-{snapshot_hash.removeprefix('sha256:')[:12]}",
        scan_at_utc=inventory.generated_at_utc,
        scan_trigger=scan_trigger,
        scan_scope_applied=inventory.scan_scope,
        primary_repo_identity=inventory.primary_repo_identity,
        sources=sources,
        stats=stats,
        load_bearing=stats.load_bearing_sources > 0,
        snapshot_hash=snapshot_hash,
        derived_from=derived_from,
        ledger_ref=ledger_ref,
        lease_source=lease_source,
        freshness_requirement=freshness_requirement,
    )


def _review_state_mapping(
    review_state: Mapping[str, object] | SupportsToDict | None,
) -> Mapping[str, object] | None:
    if review_state is None:
        return None
    if isinstance(review_state, Mapping):
        return review_state
    payload: dict[str, object] = {}
    for field_name in (
        "coordination",
        "collaboration",
        "delegated_work",
        "coordination_state",
    ):
        value = getattr(review_state, field_name, None)
        if value:
            payload[field_name] = value
    return payload or None


def _enriched_source(
    source: OrphanSource,
    *,
    inventory: OrphanInventoryReport,
    ledger_ref: str,
    lease_source: str,
    lease_rows: tuple[SessionLease, ...],
) -> OrphanSource:
    metadata = dict(source.metadata)
    metadata["inventory_report_id"] = inventory.report_id
    metadata["inventory_generated_at_utc"] = inventory.generated_at_utc
    metadata["ledger_ref"] = ledger_ref
    metadata["lease_source"] = lease_source
    metadata["lease_ids"] = [lease.lease_id for lease in lease_rows]
    metadata["snapshot_projection"] = "compute_orphan_snapshot"
    return replace(source, metadata=metadata)


def _derived_from(
    *,
    inventory: OrphanInventoryReport,
    ledger_ref: str,
    lease_source: str,
    lease_count: int,
) -> dict[str, object]:
    return {
        "inventory_report_id": inventory.report_id,
        "checkout_inventory_id": inventory.checkout_inventory.inventory_id,
        "ledger_ref": ledger_ref,
        "lease_source": lease_source,
        "lease_count": lease_count,
    }


def _snapshot_hash(
    *,
    inventory: OrphanInventoryReport,
    sources: tuple[OrphanSource, ...],
    stats: dict[str, object],
    basis: Mapping[str, object],
) -> str:
    derived_from = basis.get("derived_from")
    derived_mapping = derived_from if isinstance(derived_from, Mapping) else {}
    ledger_ref = str(basis.get("ledger_ref") or "")
    lease_source = str(basis.get("lease_source") or "")
    stable_derived = {
        "ledger_ref": ledger_ref,
        "lease_count": derived_mapping.get("lease_count", 0),
        "lease_source": lease_source,
    }
    payload: dict[str, object] = {}
    payload["scan_scope_applied"] = inventory.scan_scope
    payload["primary_repo_identity"] = inventory.primary_repo_identity
    payload["sources"] = [_stable_source_payload(source) for source in sources]
    payload["stats"] = stats
    payload["derived_from"] = stable_derived
    payload["freshness_requirement"] = str(basis.get("freshness_requirement") or "")
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _stable_source_payload(source: OrphanSource) -> dict[str, object]:
    payload = source.to_dict()
    metadata = dict(payload.get("metadata") or {})
    for key in _EPHEMERAL_SOURCE_METADATA_KEYS:
        metadata.pop(key, None)
    payload["metadata"] = metadata
    return payload


def _source_sort_key(source: OrphanSource) -> tuple[str, str, str]:
    return (source.source_kind, source.source_ref, source.source_id)


def _ledger_ref(ledger: WorkPublicationLedger | None) -> str:
    if ledger is None:
        return "ledger:not_loaded"
    if ledger.header.ledger_id:
        return ledger.header.ledger_id
    if ledger.header.checkout_fingerprint:
        return f"ledger:{ledger.header.checkout_fingerprint}"
    return "ledger:unknown"


def _lease_source(leases: tuple[SessionLease, ...]) -> str:
    return "runtime_lease" if leases else "backfill_pending"


__all__ = [
    "build_orphan_snapshot_projection",
    "compute_orphan_snapshot",
]
