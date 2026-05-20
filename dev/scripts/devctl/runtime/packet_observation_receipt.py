"""Typed packet observation receipt for review-channel packet bodies."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from typing import TYPE_CHECKING

from .correlation_spine import CorrelationContext, correlation_context_from_mapping
from .value_coercion import coerce_bool, coerce_int, coerce_string, coerce_string_items

if TYPE_CHECKING:
    from .packet_attention_drain_report import PacketAttentionDrainReport


PACKET_OBSERVATION_RECEIPT_CONTRACT_ID = "PacketObservationReceipt"
PACKET_OBSERVATION_RECEIPT_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class PacketObservationReceipt:
    """Proof that one actor/session opened and hashed a packet body."""

    observation_receipt_id: str
    observed_packet_id: str
    observed_body_sha256: str
    observer_actor_id: str
    observer_role_id: str
    observer_session_id: str
    observed_at_utc: str
    observed_body_length: int
    source_observation_event_id: str = ""
    source_packet_event_id: str = ""
    source_action: str = ""
    attention_scope: str = "packet_body"
    attention_cleared: bool = False
    drain_report_ref: str = ""
    evidence_refs: tuple[str, ...] = ()
    drain_report: PacketAttentionDrainReport | None = None
    correlation_context: CorrelationContext = field(default_factory=CorrelationContext)
    schema_version: int = PACKET_OBSERVATION_RECEIPT_SCHEMA_VERSION
    contract_id: str = PACKET_OBSERVATION_RECEIPT_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["evidence_refs"] = list(self.evidence_refs)
        if self.drain_report is not None and hasattr(self.drain_report, "to_dict"):
            payload["drain_report"] = self.drain_report.to_dict()
        payload["correlation_id"] = self.correlation_context.correlation_id
        payload["causation_id"] = self.correlation_context.causation_id
        payload["run_id"] = self.correlation_context.run_id
        return payload


def build_packet_observation_receipt(
    *,
    observed_packet_id: str,
    observed_body_sha256: str,
    observer_actor_id: str,
    observer_role_id: str,
    observer_session_id: str,
    observed_at_utc: str,
    observed_body_length: int = 0,
    source_observation_event_id: str = "",
    source_packet_event_id: str = "",
    source_action: str = "",
    attention_scope: str = "packet_body",
    attention_cleared: bool = False,
    drain_report_ref: str = "",
    evidence_refs: tuple[str, ...] = (),
    correlation_id: str = "",
    causation_id: str = "",
    run_id: str = "",
) -> PacketObservationReceipt:
    evidence = _unique_strings(
        (
            *evidence_refs,
            _ref("packet", observed_packet_id),
            _ref("event", source_observation_event_id),
            _ref("event", source_packet_event_id),
        )
    )
    fingerprint_source = "\x00".join(
        (
            coerce_string(observed_packet_id),
            coerce_string(observed_body_sha256),
            coerce_string(observer_actor_id),
            coerce_string(observer_role_id),
            coerce_string(observer_session_id),
            coerce_string(source_observation_event_id),
            coerce_string(source_packet_event_id),
            coerce_string(attention_scope),
        )
    )
    fingerprint = hashlib.sha256(fingerprint_source.encode("utf-8")).hexdigest()[:16]
    correlation_context = correlation_context_from_mapping(
        {
            "correlation_id": correlation_id,
            "causation_id": causation_id,
            "run_id": run_id,
        }
    )
    return PacketObservationReceipt(
        observation_receipt_id=f"packet_observation:{coerce_string(observed_packet_id)}:{fingerprint}",
        observed_packet_id=coerce_string(observed_packet_id),
        observed_body_sha256=coerce_string(observed_body_sha256),
        observer_actor_id=coerce_string(observer_actor_id),
        observer_role_id=coerce_string(observer_role_id),
        observer_session_id=coerce_string(observer_session_id),
        observed_at_utc=coerce_string(observed_at_utc),
        observed_body_length=int(observed_body_length or 0),
        source_observation_event_id=coerce_string(source_observation_event_id),
        source_packet_event_id=coerce_string(source_packet_event_id),
        source_action=coerce_string(source_action),
        attention_scope=coerce_string(attention_scope) or "packet_body",
        attention_cleared=bool(attention_cleared),
        drain_report_ref=coerce_string(drain_report_ref),
        evidence_refs=evidence,
        correlation_context=correlation_context,
    )


def packet_observation_receipt_from_mapping(
    payload: Mapping[str, object],
) -> PacketObservationReceipt:
    return PacketObservationReceipt(
        observation_receipt_id=coerce_string(payload.get("observation_receipt_id")),
        observed_packet_id=coerce_string(payload.get("observed_packet_id")),
        observed_body_sha256=coerce_string(payload.get("observed_body_sha256")),
        observer_actor_id=coerce_string(payload.get("observer_actor_id")),
        observer_role_id=coerce_string(payload.get("observer_role_id")),
        observer_session_id=coerce_string(payload.get("observer_session_id")),
        observed_at_utc=coerce_string(payload.get("observed_at_utc")),
        observed_body_length=coerce_int(payload.get("observed_body_length")),
        source_observation_event_id=coerce_string(
            payload.get("source_observation_event_id")
        ),
        source_packet_event_id=coerce_string(payload.get("source_packet_event_id")),
        source_action=coerce_string(payload.get("source_action")),
        attention_scope=coerce_string(payload.get("attention_scope")) or "packet_body",
        attention_cleared=coerce_bool(payload.get("attention_cleared")),
        drain_report_ref=coerce_string(payload.get("drain_report_ref")),
        evidence_refs=coerce_string_items(payload.get("evidence_refs")),
        correlation_context=correlation_context_from_mapping(
            payload.get("correlation_context") or payload
        ),
        schema_version=(
            coerce_int(payload.get("schema_version"))
            or PACKET_OBSERVATION_RECEIPT_SCHEMA_VERSION
        ),
        contract_id=(
            coerce_string(payload.get("contract_id"))
            or PACKET_OBSERVATION_RECEIPT_CONTRACT_ID
        ),
    )


def _unique_strings(values) -> tuple[str, ...]:
    rows: list[str] = []
    for value in values:
        text = coerce_string(value)
        if text and text not in rows:
            rows.append(text)
    return tuple(rows)


def _ref(kind: str, value: str) -> str:
    text = coerce_string(value)
    return f"{kind}:{text}" if text else ""


__all__ = [
    "PACKET_OBSERVATION_RECEIPT_CONTRACT_ID",
    "PACKET_OBSERVATION_RECEIPT_SCHEMA_VERSION",
    "PacketObservationReceipt",
    "build_packet_observation_receipt",
    "packet_observation_receipt_from_mapping",
]
