"""Typed packet-attention drain report for packet body observation."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING

from .value_coercion import coerce_int, coerce_string, coerce_string_items

if TYPE_CHECKING:
    from .packet_observation_receipt import PacketObservationReceipt
    from .reviewer_runtime_models import PacketAttentionState


PACKET_ATTENTION_DRAIN_REPORT_CONTRACT_ID = "PacketAttentionDrainReport"
PACKET_ATTENTION_DRAIN_REPORT_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class PacketAttentionDrainReport:
    """Proof that a packet observation changed the actor attention queue."""

    drain_report_id: str
    observer_actor_id: str
    observer_role_id: str
    observer_session_id: str
    generated_at_utc: str
    before_pending_packet_count: int
    before_unopened_packet_ids: tuple[str, ...]
    after_pending_packet_count: int
    after_unopened_packet_ids: tuple[str, ...]
    drained_packet_ids: tuple[str, ...]
    remaining_blocker_packet_id: str = ""
    remaining_required_action: str = ""
    observation_receipt_refs: tuple[str, ...] = ()
    source_receipts: tuple[PacketObservationReceipt, ...] = ()
    schema_version: int = PACKET_ATTENTION_DRAIN_REPORT_SCHEMA_VERSION
    contract_id: str = PACKET_ATTENTION_DRAIN_REPORT_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["before_unopened_packet_ids"] = list(self.before_unopened_packet_ids)
        payload["after_unopened_packet_ids"] = list(self.after_unopened_packet_ids)
        payload["drained_packet_ids"] = list(self.drained_packet_ids)
        payload["observation_receipt_refs"] = list(self.observation_receipt_refs)
        payload["source_receipts"] = [
            row.to_dict() if hasattr(row, "to_dict") else row
            for row in self.source_receipts
        ]
        return payload


def build_packet_attention_drain_report(
    *,
    observer_actor_id: str,
    observer_role_id: str,
    observer_session_id: str,
    generated_at_utc: str,
    before_attention: PacketAttentionState | Mapping[str, object],
    after_attention: PacketAttentionState | Mapping[str, object],
    observation_receipts: Sequence[PacketObservationReceipt | Mapping[str, object]] = (),
) -> PacketAttentionDrainReport:
    before = _attention_payload(before_attention)
    after = _attention_payload(after_attention)
    before_unopened = coerce_string_items(before.get("unopened_body_packet_ids"))
    after_unopened = coerce_string_items(after.get("unopened_body_packet_ids"))
    after_unopened_set = set(after_unopened)
    drained = tuple(
        packet_id
        for packet_id in before_unopened
        if packet_id not in after_unopened_set
    )
    receipt_refs = tuple(
        ref
        for ref in (
            coerce_string(_receipt_mapping(row).get("observation_receipt_id"))
            for row in observation_receipts
        )
        if ref
    )
    remaining_packet = (
        coerce_string(after.get("absorption_packet_id"))
        or coerce_string(after.get("semantic_ingestion_packet_id"))
        or coerce_string(after.get("body_open_packet_id"))
        or coerce_string(after.get("latest_attention_packet_id"))
    )
    remaining_action = _remaining_action(after)
    fingerprint_source = "\x00".join(
        (
            coerce_string(observer_actor_id),
            coerce_string(observer_role_id),
            coerce_string(observer_session_id),
            ",".join(before_unopened),
            ",".join(after_unopened),
            ",".join(drained),
            ",".join(receipt_refs),
            remaining_packet,
            remaining_action,
        )
    )
    fingerprint = hashlib.sha256(fingerprint_source.encode("utf-8")).hexdigest()[:16]
    return PacketAttentionDrainReport(
        drain_report_id=f"packet_attention_drain:{fingerprint}",
        observer_actor_id=coerce_string(observer_actor_id),
        observer_role_id=coerce_string(observer_role_id),
        observer_session_id=coerce_string(observer_session_id),
        generated_at_utc=coerce_string(generated_at_utc),
        before_pending_packet_count=coerce_int(before.get("pending_packet_count")),
        before_unopened_packet_ids=before_unopened,
        after_pending_packet_count=coerce_int(after.get("pending_packet_count")),
        after_unopened_packet_ids=after_unopened,
        drained_packet_ids=drained,
        remaining_blocker_packet_id=remaining_packet,
        remaining_required_action=remaining_action,
        observation_receipt_refs=receipt_refs,
    )


def packet_attention_drain_report_from_mapping(
    payload: Mapping[str, object],
) -> PacketAttentionDrainReport:
    return PacketAttentionDrainReport(
        drain_report_id=coerce_string(payload.get("drain_report_id")),
        observer_actor_id=coerce_string(payload.get("observer_actor_id")),
        observer_role_id=coerce_string(payload.get("observer_role_id")),
        observer_session_id=coerce_string(payload.get("observer_session_id")),
        generated_at_utc=coerce_string(payload.get("generated_at_utc")),
        before_pending_packet_count=coerce_int(
            payload.get("before_pending_packet_count")
        ),
        before_unopened_packet_ids=coerce_string_items(
            payload.get("before_unopened_packet_ids")
        ),
        after_pending_packet_count=coerce_int(payload.get("after_pending_packet_count")),
        after_unopened_packet_ids=coerce_string_items(
            payload.get("after_unopened_packet_ids")
        ),
        drained_packet_ids=coerce_string_items(payload.get("drained_packet_ids")),
        remaining_blocker_packet_id=coerce_string(
            payload.get("remaining_blocker_packet_id")
        ),
        remaining_required_action=coerce_string(
            payload.get("remaining_required_action")
        ),
        observation_receipt_refs=coerce_string_items(
            payload.get("observation_receipt_refs")
        ),
        schema_version=(
            coerce_int(payload.get("schema_version"))
            or PACKET_ATTENTION_DRAIN_REPORT_SCHEMA_VERSION
        ),
        contract_id=(
            coerce_string(payload.get("contract_id"))
            or PACKET_ATTENTION_DRAIN_REPORT_CONTRACT_ID
        ),
    )


def _attention_payload(
    attention: PacketAttentionState | Mapping[str, object],
) -> Mapping[str, object]:
    if isinstance(attention, Mapping):
        return attention
    return {
        "pending_packet_count": getattr(attention, "pending_packet_count", 0),
        "unopened_body_packet_ids": getattr(
            attention, "unopened_body_packet_ids", ()
        ),
        "body_open_packet_id": getattr(attention, "body_open_packet_id", ""),
        "semantic_ingestion_packet_id": getattr(
            attention, "semantic_ingestion_packet_id", ""
        ),
        "absorption_packet_id": getattr(attention, "absorption_packet_id", ""),
        "latest_attention_packet_id": getattr(
            attention, "latest_attention_packet_id", ""
        ),
        "body_open_required": getattr(attention, "body_open_required", False),
        "semantic_ingestion_required": getattr(
            attention, "semantic_ingestion_required", False
        ),
        "absorption_required": getattr(attention, "absorption_required", False),
    }


def _receipt_mapping(
    row: PacketObservationReceipt | Mapping[str, object],
) -> Mapping[str, object]:
    if isinstance(row, Mapping):
        return row
    if hasattr(row, "to_dict"):
        payload = row.to_dict()
        return payload if isinstance(payload, Mapping) else {}
    return {}


def _remaining_action(attention: Mapping[str, object]) -> str:
    if attention.get("absorption_required"):
        return "absorb_packet"
    if attention.get("semantic_ingestion_required"):
        return "ingest_packet_semantics"
    if attention.get("body_open_required"):
        return "open_packet_body"
    return ""


__all__ = [
    "PACKET_ATTENTION_DRAIN_REPORT_CONTRACT_ID",
    "PACKET_ATTENTION_DRAIN_REPORT_SCHEMA_VERSION",
    "PacketAttentionDrainReport",
    "build_packet_attention_drain_report",
    "packet_attention_drain_report_from_mapping",
]
