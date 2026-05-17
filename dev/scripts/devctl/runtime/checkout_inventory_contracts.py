"""Checkout inventory typed contract models."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field

from .value_coercion import (
    coerce_bool,
    coerce_int,
    coerce_mapping,
    coerce_mapping_items,
    coerce_string,
    coerce_string_items,
)
from .worktree_orphan_types import CHECKOUT_INVENTORY_STATES, enum_value


@dataclass(frozen=True, slots=True)
class CheckoutInventoryClassification:
    """Inventory row classification, including governed auto-sync state."""

    known_governed_auto_sync: bool = False
    ownership: str = ""
    reason: str = ""
    evidence_refs: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["evidence_refs"] = list(self.evidence_refs)
        return payload


@dataclass(frozen=True, slots=True)
class CheckoutInventoryRow:
    """One checkout row produced from filesystem-scan and ledger headers."""

    row_id: str
    state: str
    checkout_path: str
    checkout_fingerprint: str
    repo_identity: str = ""
    origin_url: str = ""
    branch: str = ""
    head_sha: str = ""
    git_dir: str = ""
    ledger_header_ref: str = ""
    source_refs: tuple[str, ...] = ()
    classification: CheckoutInventoryClassification = field(
        default_factory=CheckoutInventoryClassification
    )

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["source_refs"] = list(self.source_refs)
        payload["classification"] = self.classification.to_dict()
        return payload


@dataclass(frozen=True, slots=True)
class CheckoutInventory:
    """Projection over bounded filesystem scan rows and ledger headers."""

    inventory_id: str
    generated_at_utc: str
    inventory_scope: str
    filesystem_scan_ref: str
    ledger_headers_ref: str
    rows: tuple[CheckoutInventoryRow, ...] = ()
    schema_version: int = 1
    contract_id: str = "CheckoutInventory"

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["rows"] = [row.to_dict() for row in self.rows]
        return payload


def checkout_inventory_classification_from_mapping(
    value: object,
) -> CheckoutInventoryClassification:
    payload = coerce_mapping(value)
    return CheckoutInventoryClassification(
        known_governed_auto_sync=coerce_bool(
            payload.get("known_governed_auto_sync")
        ),
        ownership=coerce_string(payload.get("ownership")),
        reason=coerce_string(payload.get("reason")),
        evidence_refs=coerce_string_items(payload.get("evidence_refs")),
    )


def checkout_inventory_row_from_mapping(
    value: object,
) -> CheckoutInventoryRow | None:
    payload = coerce_mapping(value)
    if not payload:
        return None

    required = _checkout_row_required_fields(payload)
    if required is None:
        return None

    row_id, checkout_path, checkout_fingerprint = required
    classification = checkout_inventory_classification_from_mapping(
        payload.get("classification")
    )

    state = enum_value(
        coerce_string(payload.get("state")),
        allowed=CHECKOUT_INVENTORY_STATES,
        default="unmanaged_shadow",
    )

    return CheckoutInventoryRow(
        row_id=row_id,
        state=state,
        checkout_path=checkout_path,
        checkout_fingerprint=checkout_fingerprint,
        repo_identity=coerce_string(payload.get("repo_identity")),
        origin_url=coerce_string(payload.get("origin_url")),
        branch=coerce_string(payload.get("branch")),
        head_sha=coerce_string(payload.get("head_sha")),
        git_dir=coerce_string(payload.get("git_dir")),
        ledger_header_ref=coerce_string(payload.get("ledger_header_ref")),
        source_refs=coerce_string_items(payload.get("source_refs")),
        classification=classification,
    )


def _checkout_row_required_fields(
    payload: Mapping[str, object],
) -> tuple[str, str, str] | None:
    row_id = coerce_string(payload.get("row_id"))
    checkout_path = coerce_string(payload.get("checkout_path"))
    checkout_fingerprint = coerce_string(payload.get("checkout_fingerprint"))

    if not row_id or not checkout_path or not checkout_fingerprint:
        return None

    return row_id, checkout_path, checkout_fingerprint


def checkout_inventory_from_mapping(value: object) -> CheckoutInventory | None:
    payload = coerce_mapping(value)
    if not payload:
        return None
    rows = tuple(_parsed_rows(payload))
    return CheckoutInventory(
        schema_version=coerce_int(payload.get("schema_version")) or 1,
        contract_id=coerce_string(payload.get("contract_id")) or "CheckoutInventory",
        inventory_id=coerce_string(payload.get("inventory_id")),
        generated_at_utc=coerce_string(payload.get("generated_at_utc")),
        inventory_scope=coerce_string(payload.get("inventory_scope")),
        filesystem_scan_ref=coerce_string(payload.get("filesystem_scan_ref")),
        ledger_headers_ref=coerce_string(payload.get("ledger_headers_ref")),
        rows=rows,
    )


def _parsed_rows(payload: Mapping[str, object]) -> tuple[CheckoutInventoryRow, ...]:
    rows: list[CheckoutInventoryRow] = []
    for item in coerce_mapping_items(payload.get("rows")):
        row = checkout_inventory_row_from_mapping(item)
        if row is not None:
            rows.append(row)
    return tuple(rows)


__all__ = [
    "CheckoutInventory",
    "CheckoutInventoryClassification",
    "CheckoutInventoryRow",
    "checkout_inventory_from_mapping",
    "checkout_inventory_row_from_mapping",
]
