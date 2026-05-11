"""Plan-source snapshot model and builders."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import NamedTuple

from .master_plan_contract import MASTER_PLAN_SCHEMA_VERSION
from .plan_source_retention_anchors import full_plan_anchor_status
from .value_coercion import (
    coerce_int,
    coerce_mapping,
    coerce_string,
    coerce_string_items,
)

PLAN_SOURCE_SNAPSHOT_CONTRACT_ID = "PlanSourceSnapshot"
PLAN_SOURCE_SNAPSHOT_STORE_REL = "dev/state/plan_source_snapshots.jsonl"


@dataclass(frozen=True, slots=True)
class PlanSourceSnapshot:
    """Durable copy of the source material that created a PlanRow."""

    snapshot_id: str
    plan_row_id: str
    source_kind: str
    source_ref: str
    source_hash: str
    body_hash: str
    captured_at_utc: str
    receipt_id: str = ""
    action_id: str = ""
    source_packet_id: str = ""
    packet_expires_at_utc: str = ""
    retention_status: str = "snapshotted"
    source_integrity_status: str = "ok"
    source_completeness_status: str = "not_required"
    required_anchor_count: int = 0
    matched_anchor_count: int = 0
    missing_required_anchors: tuple[str, ...] = ()
    composition_disposition: str = ""
    owning_mp_family: str = ""
    existing_owner_row_refs: tuple[str, ...] = ()
    packet_binding_refs: tuple[str, ...] = ()
    why_not_duplicate: str = ""
    phase_allowed_to_block: str = ""
    phase_allowed_to_mutate: str = ""
    schema_limit_warning: str = ""
    source_text: str = ""
    source_summary: str = ""
    snapshot_path: str = ""
    schema_version: int = MASTER_PLAN_SCHEMA_VERSION
    contract_id: str = PLAN_SOURCE_SNAPSHOT_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_mapping(cls, payload: object) -> "PlanSourceSnapshot":
        mapping = coerce_mapping(payload)
        return cls(
            snapshot_id=coerce_string(mapping.get("snapshot_id")),
            plan_row_id=coerce_string(mapping.get("plan_row_id")),
            source_kind=coerce_string(mapping.get("source_kind")),
            source_ref=coerce_string(mapping.get("source_ref")),
            source_hash=coerce_string(mapping.get("source_hash")),
            body_hash=coerce_string(mapping.get("body_hash")),
            captured_at_utc=coerce_string(mapping.get("captured_at_utc")),
            receipt_id=coerce_string(mapping.get("receipt_id")),
            action_id=coerce_string(mapping.get("action_id")),
            source_packet_id=coerce_string(mapping.get("source_packet_id")),
            packet_expires_at_utc=coerce_string(mapping.get("packet_expires_at_utc")),
            retention_status=coerce_string(mapping.get("retention_status"))
            or "snapshotted",
            source_integrity_status=coerce_string(
                mapping.get("source_integrity_status")
            )
            or "ok",
            source_completeness_status=coerce_string(
                mapping.get("source_completeness_status")
            )
            or "not_required",
            required_anchor_count=coerce_int(mapping.get("required_anchor_count")),
            matched_anchor_count=coerce_int(mapping.get("matched_anchor_count")),
            missing_required_anchors=coerce_string_items(
                mapping.get("missing_required_anchors")
            ),
            composition_disposition=coerce_string(
                mapping.get("composition_disposition")
            ),
            owning_mp_family=coerce_string(mapping.get("owning_mp_family")),
            existing_owner_row_refs=coerce_string_items(
                mapping.get("existing_owner_row_refs")
            ),
            packet_binding_refs=coerce_string_items(
                mapping.get("packet_binding_refs")
            ),
            why_not_duplicate=coerce_string(mapping.get("why_not_duplicate")),
            phase_allowed_to_block=coerce_string(
                mapping.get("phase_allowed_to_block")
            ),
            phase_allowed_to_mutate=coerce_string(
                mapping.get("phase_allowed_to_mutate")
            ),
            schema_limit_warning=coerce_string(mapping.get("schema_limit_warning")),
            source_text=_coerce_source_text(mapping.get("source_text")),
            source_summary=coerce_string(mapping.get("source_summary")),
            snapshot_path=coerce_string(mapping.get("snapshot_path")),
            schema_version=coerce_int(mapping.get("schema_version"))
            or MASTER_PLAN_SCHEMA_VERSION,
        )


class PlanSourceSnapshotInput(NamedTuple):
    """Inputs used to construct a source snapshot."""

    plan_row_id: str
    source_kind: str
    source_ref: str
    source_hash: str
    source_text: str
    captured_at_utc: str
    receipt_id: str = ""
    action_id: str = ""
    source_packet_id: str = ""
    packet_expires_at_utc: str = ""
    composition_disposition: str = ""
    owning_mp_family: str = ""
    existing_owner_row_refs: tuple[str, ...] = ()
    packet_binding_refs: tuple[str, ...] = ()
    why_not_duplicate: str = ""
    phase_allowed_to_block: str = ""
    phase_allowed_to_mutate: str = ""
    schema_limit_warning: str = ""

    @classmethod
    def from_kwargs(cls, values: Mapping[str, object]) -> "PlanSourceSnapshotInput":
        return cls(
            plan_row_id=coerce_string(values.get("plan_row_id")),
            source_kind=coerce_string(values.get("source_kind")),
            source_ref=coerce_string(values.get("source_ref")),
            source_hash=coerce_string(values.get("source_hash")),
            source_text=_coerce_source_text(values.get("source_text")),
            captured_at_utc=coerce_string(values.get("captured_at_utc")),
            receipt_id=coerce_string(values.get("receipt_id")),
            action_id=coerce_string(values.get("action_id")),
            source_packet_id=coerce_string(values.get("source_packet_id")),
            packet_expires_at_utc=coerce_string(values.get("packet_expires_at_utc")),
            composition_disposition=coerce_string(
                values.get("composition_disposition")
            ),
            owning_mp_family=coerce_string(values.get("owning_mp_family")),
            existing_owner_row_refs=coerce_string_items(
                values.get("existing_owner_row_refs")
            ),
            packet_binding_refs=coerce_string_items(values.get("packet_binding_refs")),
            why_not_duplicate=coerce_string(values.get("why_not_duplicate")),
            phase_allowed_to_block=coerce_string(values.get("phase_allowed_to_block")),
            phase_allowed_to_mutate=coerce_string(
                values.get("phase_allowed_to_mutate")
            ),
            schema_limit_warning=coerce_string(values.get("schema_limit_warning")),
        )


def plan_source_body_hash(source_text: str) -> str:
    """Return a stable hash for retained plan source text."""
    return "sha256:" + hashlib.sha256(source_text.encode("utf-8")).hexdigest()


def plan_source_snapshot_id(
    *,
    plan_row_id: str,
    source_kind: str,
    source_ref: str,
    source_hash: str,
) -> str:
    """Return a deterministic source-snapshot id."""
    payload = {
        "plan_row_id": plan_row_id,
        "source_kind": source_kind,
        "source_ref": source_ref,
        "source_hash": source_hash,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return "plan-source-" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]


def build_plan_source_snapshot(**kwargs: object) -> PlanSourceSnapshot:
    """Build one durable source snapshot for a written PlanRow."""
    values = PlanSourceSnapshotInput.from_kwargs(kwargs)
    body_hash = plan_source_body_hash(values.source_text)
    retention_status = "snapshotted" if values.source_text else "missing"
    integrity_status = "ok" if values.source_text else "unknown"
    anchor_status = full_plan_anchor_status(values.plan_row_id, values.source_text)
    return PlanSourceSnapshot(
        snapshot_id=plan_source_snapshot_id(
            plan_row_id=values.plan_row_id,
            source_kind=values.source_kind,
            source_ref=values.source_ref,
            source_hash=values.source_hash,
        ),
        plan_row_id=values.plan_row_id,
        source_kind=values.source_kind,
        source_ref=values.source_ref,
        source_hash=values.source_hash,
        body_hash=body_hash,
        captured_at_utc=values.captured_at_utc,
        receipt_id=values.receipt_id,
        action_id=values.action_id,
        source_packet_id=values.source_packet_id,
        packet_expires_at_utc=values.packet_expires_at_utc,
        retention_status=retention_status,
        source_integrity_status=integrity_status,
        source_completeness_status=anchor_status.status,
        required_anchor_count=anchor_status.required_count,
        matched_anchor_count=anchor_status.matched_count,
        missing_required_anchors=anchor_status.missing_anchors,
        composition_disposition=values.composition_disposition,
        owning_mp_family=values.owning_mp_family,
        existing_owner_row_refs=values.existing_owner_row_refs,
        packet_binding_refs=values.packet_binding_refs,
        why_not_duplicate=values.why_not_duplicate,
        phase_allowed_to_block=values.phase_allowed_to_block,
        phase_allowed_to_mutate=values.phase_allowed_to_mutate,
        schema_limit_warning=values.schema_limit_warning,
        source_text=values.source_text,
        source_summary=_source_summary(values.source_text),
    )


def _source_summary(source_text: str) -> str:
    collapsed = " ".join(source_text.strip().split())
    if len(collapsed) <= 240:
        return collapsed
    return collapsed[:237].rstrip() + "..."


def _coerce_source_text(value: object) -> str:
    """Return retained source text without trimming significant whitespace."""
    return str(value) if value is not None else ""


__all__ = [
    "PLAN_SOURCE_SNAPSHOT_CONTRACT_ID",
    "PLAN_SOURCE_SNAPSHOT_STORE_REL",
    "PlanSourceSnapshot",
    "PlanSourceSnapshotInput",
    "build_plan_source_snapshot",
    "plan_source_body_hash",
    "plan_source_snapshot_id",
]
