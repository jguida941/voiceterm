"""Core orphan/check-out schema specs."""

from __future__ import annotations

from .worktree_orphan_schema_support import array, field, object_ref, spec
from .worktree_orphan_types import (
    CHECKOUT_INVENTORY_STATES,
    ORPHAN_RECONCILIATION_ACTIONS,
    ORPHAN_SOURCE_KINDS,
)


def core_schema_specs():
    return (
        _ORPHAN_SOURCE_SPECS
        + _ORPHAN_RECONCILIATION_SPECS
        + _CHECKOUT_INVENTORY_SPECS
        + _ORPHAN_INVENTORY_REPORT_SPECS
    )


_ORPHAN_SOURCE_SPECS = (
    spec(
        "OrphanSourceClassification",
        ("state", "known_governed_auto_sync", "load_bearing"),
        field("state"),
        field("known_governed_auto_sync", "boolean"),
        field("load_bearing", "boolean"),
        field("governance_owner"),
        field("risk"),
        array("notes"),
    ),
    spec(
        "OrphanSource",
        ("source_id", "source_kind", "source_ref", "classification"),
        field("source_id"),
        field("source_kind", enum_values=ORPHAN_SOURCE_KINDS),
        field("source_ref"),
        field("path"),
        field("repo_identity"),
        field("branch"),
        field("head_sha"),
        field("dirty_path_count", "integer"),
        field("untracked_path_count", "integer"),
        array("unpublished_commit_shas"),
        field("status"),
        object_ref("classification", "OrphanSourceClassification"),
        array("evidence_refs"),
        field("metadata", "object"),
    ),
    spec(
        "OrphanSnapshotStats",
        ("total_sources", "unresolved_sources"),
        field("total_sources", "integer"),
        field("unresolved_sources", "integer"),
        field("dirty_sources", "integer"),
        field("unpublished_sources", "integer"),
        field("prunable_sources", "integer"),
        field("load_bearing_sources", "integer"),
    ),
    spec(
        "OrphanSnapshot",
        (
            "schema_version",
            "contract_id",
            "snapshot_id",
            "scan_at_utc",
            "scan_trigger",
            "scan_scope_applied",
            "primary_repo_identity",
            "sources",
            "stats",
            "load_bearing",
        ),
        field("schema_version", "integer"),
        field("contract_id", const_value="OrphanSnapshot"),
        field("snapshot_id"),
        field("scan_at_utc"),
        field("scan_trigger"),
        field("scan_scope_applied"),
        field("primary_repo_identity"),
        array("sources", item_ref="OrphanSource"),
        object_ref("stats", "OrphanSnapshotStats"),
        field("load_bearing", "boolean"),
        field("snapshot_hash"),
        field("derived_from", "object"),
        field("ledger_ref"),
        field("lease_source"),
        field("freshness_requirement"),
    ),
)

_ORPHAN_RECONCILIATION_SPECS = (
    spec(
        "OrphanSourceDecision",
        ("source_ref", "chosen_action", "action_args"),
        field("source_ref"),
        field("chosen_action", enum_values=ORPHAN_RECONCILIATION_ACTIONS),
        field("action_args", "object"),
        field("rationale"),
    ),
    spec(
        "OrphanReconciliationDecision",
        (
            "schema_version",
            "contract_id",
            "decision_id",
            "responds_to_snapshot_hash",
            "per_source_decisions",
            "operator_identity",
            "authorization_receipt_ref",
            "governed_execution_plan_id",
        ),
        field("schema_version", "integer"),
        field("contract_id", const_value="OrphanReconciliationDecision"),
        field("decision_id"),
        field("responds_to_snapshot_hash"),
        array("per_source_decisions", item_ref="OrphanSourceDecision"),
        field("operator_identity"),
        field("authorization_receipt_ref"),
        field("governed_execution_plan_id"),
        field("decided_at_utc"),
        field("plan_scope_hint"),
        field("confirmed_issue_id"),
    ),
)

_CHECKOUT_INVENTORY_SPECS = (
    spec(
        "CheckoutInventoryClassification",
        ("known_governed_auto_sync",),
        field("known_governed_auto_sync", "boolean"),
        field("ownership"),
        field("reason"),
        array("evidence_refs"),
    ),
    spec(
        "CheckoutInventoryRow",
        (
            "row_id",
            "state",
            "checkout_path",
            "checkout_fingerprint",
            "classification",
        ),
        field("row_id"),
        field("state", enum_values=CHECKOUT_INVENTORY_STATES),
        field("checkout_path"),
        field("checkout_fingerprint"),
        field("repo_identity"),
        field("origin_url"),
        field("branch"),
        field("head_sha"),
        field("git_dir"),
        field("ledger_header_ref"),
        array("source_refs"),
        object_ref("classification", "CheckoutInventoryClassification"),
    ),
    spec(
        "CheckoutInventory",
        (
            "schema_version",
            "contract_id",
            "inventory_id",
            "generated_at_utc",
            "inventory_scope",
            "filesystem_scan_ref",
            "ledger_headers_ref",
            "rows",
        ),
        field("schema_version", "integer"),
        field("contract_id", const_value="CheckoutInventory"),
        field("inventory_id"),
        field("generated_at_utc"),
        field("inventory_scope"),
        field("filesystem_scan_ref"),
        field("ledger_headers_ref"),
        array("rows", item_ref="CheckoutInventoryRow"),
    ),
)

_ORPHAN_INVENTORY_REPORT_SPECS = (
    spec(
        "OrphanInventoryReport",
        (
            "schema_version",
            "contract_id",
            "report_id",
            "generated_at_utc",
            "scan_scope",
            "primary_repo_identity",
            "checkout_inventory",
            "sources",
            "stats",
            "report_only",
            "gates_evaluated",
        ),
        field("schema_version", "integer"),
        field("contract_id", const_value="OrphanInventoryReport"),
        field("report_id"),
        field("generated_at_utc"),
        field("scan_scope"),
        field("primary_repo_identity"),
        object_ref("checkout_inventory", "CheckoutInventory"),
        array("sources", item_ref="OrphanSource"),
        object_ref("stats", "OrphanSnapshotStats"),
        field("report_only", "boolean"),
        field("gates_evaluated", "boolean"),
        array("warnings"),
        array("errors"),
    ),
)


__all__ = ["core_schema_specs"]
