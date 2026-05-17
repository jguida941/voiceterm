"""Parse worktree-orphan inventory report payloads."""

from __future__ import annotations

from .checkout_inventory_contracts import checkout_inventory_from_mapping
from .value_coercion import (
    coerce_bool,
    coerce_int,
    coerce_mapping,
    coerce_mapping_items,
    coerce_string,
    coerce_string_items,
)
from .worktree_orphan_inventory_report import OrphanInventoryReport
from .worktree_orphan_snapshot import (
    OrphanSnapshotStats,
    OrphanSource,
    orphan_snapshot_stats_from_mapping,
    orphan_source_from_mapping,
)


def orphan_inventory_report_from_mapping(
    value: object,
) -> OrphanInventoryReport | None:
    """Restore an OrphanInventoryReport from a mapping."""
    payload = coerce_mapping(value)
    if not payload:
        return None

    inventory = checkout_inventory_from_mapping(payload.get("checkout_inventory"))
    if inventory is None:
        return None

    return OrphanInventoryReport(
        schema_version=coerce_int(payload.get("schema_version")) or 1,
        contract_id=report_contract_id(payload),
        report_id=coerce_string(payload.get("report_id")),
        generated_at_utc=coerce_string(payload.get("generated_at_utc")),
        scan_scope=coerce_string(payload.get("scan_scope")),
        primary_repo_identity=coerce_string(payload.get("primary_repo_identity")),
        checkout_inventory=inventory,
        sources=parsed_orphan_sources(payload.get("sources")),
        stats=report_stats(payload.get("stats")),
        report_only=report_only_flag(payload),
        gates_evaluated=coerce_bool(payload.get("gates_evaluated")),
        warnings=coerce_string_items(payload.get("warnings")),
        errors=coerce_string_items(payload.get("errors")),
    )


def report_contract_id(payload: dict[str, object]) -> str:
    return coerce_string(payload.get("contract_id")) or "OrphanInventoryReport"


def report_only_flag(payload: dict[str, object]) -> bool:
    if "report_only" not in payload:
        return True
    return coerce_bool(payload.get("report_only"))


def report_stats(value: object) -> OrphanSnapshotStats:
    return orphan_snapshot_stats_from_mapping(value)


def parsed_orphan_sources(value: object) -> tuple[OrphanSource, ...]:
    sources: list[OrphanSource] = []
    for item in coerce_mapping_items(value):
        source = orphan_source_from_mapping(item)
        if source is not None:
            sources.append(source)
    return tuple(sources)


__all__ = ["orphan_inventory_report_from_mapping"]
