"""Platform contract rows for worktree-orphan governance contracts."""

from __future__ import annotations

from dataclasses import fields

from ..runtime.checkout_inventory_contracts import (
    CheckoutInventory,
    CheckoutInventoryClassification,
    CheckoutInventoryRow,
)
from ..runtime.session_lease_contracts import SessionLease
from ..runtime.work_publication_ledger_contracts import (
    PublicationEpisode,
    WorkPublicationLedger,
    WorkPublicationLedgerEvent,
    WorkPublicationLedgerHeader,
    WorktreeBaseline,
)
from ..runtime.worktree_orphan_reconciliation import (
    AcceptAllOrphansAction,
    AcceptAllOrphansReceipt,
    OrphanReconciliationDecision,
    OrphanSourceDecision,
)
from ..runtime.worktree_orphan_inventory import OrphanInventoryReport
from ..runtime.worktree_orphan_snapshot import (
    OrphanSnapshot,
    OrphanSnapshotStats,
    OrphanSource,
    OrphanSourceClassification,
)
from .contracts import ContractField, ContractSpec

_METADATA_FIELDS = frozenset(("schema_version", "contract_id"))

_WORKTREE_ORPHAN_CONTRACT_ROWS = (
    (
        OrphanSourceClassification,
        "Policy classification attached to one orphan source, including governed auto-sync state.",
    ),
    (
        OrphanSource,
        "One discriminated source row for dirty, unpublished, stale, prunable, or sibling-copy work.",
    ),
    (
        OrphanSnapshotStats,
        "Aggregated counters for a bounded orphan snapshot.",
    ),
    (
        OrphanSnapshot,
        "AuthoritySnapshot-peer projection over all orphanable work sources for one scan.",
    ),
    (
        OrphanSourceDecision,
        "One operator reconciliation choice for a source in an orphan snapshot.",
    ),
    (
        OrphanReconciliationDecision,
        "Typed operator decision packet that authorizes per-source orphan reconciliation.",
    ),
    (
        AcceptAllOrphansAction,
        "Bulk operator override request for classifying known orphan debt in a bounded scope.",
    ),
    (
        AcceptAllOrphansReceipt,
        "Receipt proving how many orphan sources an accept-all override affected.",
    ),
    (
        CheckoutInventoryClassification,
        "Classification attached to one checkout inventory row.",
    ),
    (
        CheckoutInventoryRow,
        "One managed, registered, planned, sibling, or deep-scan checkout inventory row.",
    ),
    (
        CheckoutInventory,
        "Bounded inventory over current checkout, worktrees, planned workers, and sibling copies.",
    ),
    (
        OrphanInventoryReport,
        "Report-only bounded inventory scan output before orphan snapshots/gates are enforced.",
    ),
    (
        WorkPublicationLedgerHeader,
        "Stable publication-ledger header for one checkout fingerprint.",
    ),
    (
        WorkPublicationLedgerEvent,
        "Append-only event row for commit, receipt, push, and reconciliation publication state.",
    ),
    (
        PublicationEpisode,
        "Derived publication episode keyed by content commit and governed pipeline id.",
    ),
    (
        WorkPublicationLedger,
        "Current publication ledger state for one checkout.",
    ),
    (
        WorktreeBaseline,
        "Managed baseline emitted at governed commit/session boundaries.",
    ),
    (
        SessionLease,
        "Runtime session lease binding an agent/session to a baseline and declared scope.",
    ),
)


def worktree_orphan_contracts() -> tuple[ContractSpec, ...]:
    """Return platform rows for the worktree-orphan slice-one contract set."""
    return tuple(
        _contract_spec(model=model, purpose=purpose)
        for model, purpose in _WORKTREE_ORPHAN_CONTRACT_ROWS
    )


def _contract_spec(*, model: type[object], purpose: str) -> ContractSpec:
    return ContractSpec(
        contract_id=model.__name__,
        owner_layer="governance_runtime",
        purpose=purpose,
        required_fields=_contract_fields(model),
        runtime_model=f"{model.__module__}:{model.__name__}",
        startup_surface_tokens=("orphan-snapshot", "checkout-inventory"),
    )


def _contract_fields(model: type[object]) -> tuple[ContractField, ...]:
    return tuple(
        ContractField(
            item.name,
            _type_hint(item.type),
            f"{model.__name__}.{item.name}",
        )
        for item in fields(model)
        if item.name not in _METADATA_FIELDS
    )


def _type_hint(value: object) -> str:
    if isinstance(value, str):
        return value

    if isinstance(value, type):
        return value.__name__

    return str(value)


__all__ = ["worktree_orphan_contracts"]
