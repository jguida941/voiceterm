"""Typed report model for worktree-orphan inventory scans."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from .checkout_inventory_contracts import CheckoutInventory
from .worktree_orphan_snapshot import OrphanSnapshotStats, OrphanSource


@dataclass(frozen=True, slots=True)
class OrphanInventoryReport:
    """Read-only inventory report emitted before gate/projection slices."""

    report_id: str
    generated_at_utc: str
    scan_scope: str
    primary_repo_identity: str
    checkout_inventory: CheckoutInventory
    sources: tuple[OrphanSource, ...] = ()
    stats: OrphanSnapshotStats = field(default_factory=OrphanSnapshotStats)
    report_only: bool = True
    gates_evaluated: bool = False
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    schema_version: int = 1
    contract_id: str = "OrphanInventoryReport"

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["checkout_inventory"] = self.checkout_inventory.to_dict()
        payload["sources"] = [source.to_dict() for source in self.sources]
        payload["stats"] = self.stats.to_dict()
        payload["warnings"] = list(self.warnings)
        payload["errors"] = list(self.errors)
        return payload


__all__ = ["OrphanInventoryReport"]
