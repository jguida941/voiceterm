"""Shared payload helpers for derived-state invalidation producers."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field

DERIVED_STATE_INVALIDATION_SCHEMA_VERSION = 1
DERIVED_STATE_INVALIDATION_CONTRACT_ID = "DerivedStateInvalidation"
PACKET_ARRIVAL_DERIVED_STATE_INVALIDATION_CONTRACT_ID = (
    "PacketArrivalDerivedStateInvalidation"
)

PACKET_ARRIVAL_INVALIDATION_SOURCE = "packet_arrival_event"
PACKET_LIFECYCLE_TRANSITION_INVALIDATION_SOURCE = "packet_lifecycle_transition"
PACKET_DURABLE_INGESTION_INVALIDATION_SOURCE = "packet_durable_ingestion_event"
PLAN_INGESTION_INVALIDATION_SOURCE = "plan_ingestion_event"
SESSION_LIVENESS_INVALIDATION_SOURCE = "session_liveness_event"

REVIEW_CHANNEL_DERIVED_STATE_CONSUMERS = (
    "review_channel.state",
    "review_channel.projections.latest.review_state",
    "review_channel.projections.latest.compact",
    "review_channel.projections.latest.full",
    "review_channel.projections.latest.actions",
    "review_channel.packet_inbox",
    "review_channel.agent_work_board",
    "review_channel.agent_loop_decisions",
    "startup_context",
    "develop.next",
)

PLAN_INGESTION_DERIVED_STATE_CONSUMERS = (
    "master_plan.plan_index",
    "plan_intent_ingestion_receipts",
    "review_channel.packet_inbox",
    "review_channel.agent_work_board",
    "review_channel.agent_loop_decisions",
    "startup_context",
    "develop.next",
)


@dataclass(frozen=True)
class DerivedStateInvalidationInput:
    """Typed producer metadata for a derived-state invalidation payload."""

    source: str
    producer_id: str
    producer_kind: str
    invalidated_consumers: Iterable[str]
    next_consumer_action: str
    contract_id: str = DERIVED_STATE_INVALIDATION_CONTRACT_ID
    invalidated: bool = True
    source_event_id: str = ""
    source_ref: str = ""
    event_type: str = ""
    packet_id: str = ""
    receipt_id: str = ""
    action_id: str = ""
    row_ids: Iterable[str] = ()
    target_ref: str = ""
    status: str = ""
    store_statuses: Iterable[str] = ()
    projection_refresh_state: str = ""
    refreshed_at_utc: str = ""
    projection_refresh_seq: object = None
    source_latest_event_id: str = ""
    extra: Mapping[str, object] = field(default_factory=dict)


def derived_state_invalidation_payload(
    spec: DerivedStateInvalidationInput,
) -> dict[str, object]:
    """Return a normalized invalidation payload for existing evidence rows."""
    payload: dict[str, object] = {}
    payload["contract_id"] = spec.contract_id
    payload["schema_version"] = DERIVED_STATE_INVALIDATION_SCHEMA_VERSION
    payload["source"] = _text(spec.source)
    payload["producer_id"] = _text(spec.producer_id)
    payload["producer_kind"] = _text(spec.producer_kind)
    payload["invalidated"] = bool(spec.invalidated)
    payload["invalidated_consumers"] = _text_list(spec.invalidated_consumers)
    payload["next_consumer_action"] = _text(spec.next_consumer_action)
    _put_text(payload, "source_event_id", spec.source_event_id)
    _put_text(payload, "source_ref", spec.source_ref)
    _put_text(payload, "event_type", spec.event_type)
    _put_text(payload, "packet_id", spec.packet_id)
    _put_text(payload, "receipt_id", spec.receipt_id)
    _put_text(payload, "action_id", spec.action_id)
    row_id_list = _text_list(spec.row_ids)
    if row_id_list:
        payload["row_ids"] = row_id_list
    _put_text(payload, "target_ref", spec.target_ref)
    _put_text(payload, "status", spec.status)
    store_status_list = _text_list(spec.store_statuses)
    if store_status_list:
        payload["store_statuses"] = store_status_list
    _put_text(payload, "projection_refresh_state", spec.projection_refresh_state)
    _put_text(payload, "refreshed_at_utc", spec.refreshed_at_utc)
    if spec.projection_refresh_seq is not None:
        payload["projection_refresh_seq"] = spec.projection_refresh_seq
    _put_text(payload, "source_latest_event_id", spec.source_latest_event_id)
    if spec.extra:
        for key, value in spec.extra.items():
            text_key = _text(key)
            if text_key and value not in ("", None, (), []):
                payload[text_key] = value
    return payload


def _put_text(payload: dict[str, object], key: str, value: object) -> None:
    text = _text(value)
    if text:
        payload[key] = text


def _text_list(values: Iterable[object]) -> list[str]:
    return list(dict.fromkeys(_text(value) for value in values if _text(value)))


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = [
    "DERIVED_STATE_INVALIDATION_CONTRACT_ID",
    "DERIVED_STATE_INVALIDATION_SCHEMA_VERSION",
    "DerivedStateInvalidationInput",
    "PACKET_ARRIVAL_DERIVED_STATE_INVALIDATION_CONTRACT_ID",
    "PACKET_ARRIVAL_INVALIDATION_SOURCE",
    "PACKET_DURABLE_INGESTION_INVALIDATION_SOURCE",
    "PACKET_LIFECYCLE_TRANSITION_INVALIDATION_SOURCE",
    "PLAN_INGESTION_DERIVED_STATE_CONSUMERS",
    "PLAN_INGESTION_INVALIDATION_SOURCE",
    "REVIEW_CHANNEL_DERIVED_STATE_CONSUMERS",
    "SESSION_LIVENESS_INVALIDATION_SOURCE",
    "derived_state_invalidation_payload",
]
