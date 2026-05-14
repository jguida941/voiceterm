"""Shared payload helpers for derived-state invalidation producers."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

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


def derived_state_invalidation_payload(
    *,
    source: str,
    producer_id: str,
    producer_kind: str,
    invalidated_consumers: Iterable[str],
    next_consumer_action: str,
    contract_id: str = DERIVED_STATE_INVALIDATION_CONTRACT_ID,
    invalidated: bool = True,
    source_event_id: str = "",
    source_ref: str = "",
    event_type: str = "",
    packet_id: str = "",
    receipt_id: str = "",
    action_id: str = "",
    row_ids: Iterable[str] = (),
    target_ref: str = "",
    status: str = "",
    store_statuses: Iterable[str] = (),
    projection_refresh_state: str = "",
    refreshed_at_utc: str = "",
    projection_refresh_seq: object = None,
    source_latest_event_id: str = "",
    extra: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Return a normalized invalidation payload for existing evidence rows."""
    payload: dict[str, object] = {
        "contract_id": contract_id,
        "schema_version": DERIVED_STATE_INVALIDATION_SCHEMA_VERSION,
        "source": _text(source),
        "producer_id": _text(producer_id),
        "producer_kind": _text(producer_kind),
        "invalidated": bool(invalidated),
        "invalidated_consumers": _text_list(invalidated_consumers),
        "next_consumer_action": _text(next_consumer_action),
    }
    _put_text(payload, "source_event_id", source_event_id)
    _put_text(payload, "source_ref", source_ref)
    _put_text(payload, "event_type", event_type)
    _put_text(payload, "packet_id", packet_id)
    _put_text(payload, "receipt_id", receipt_id)
    _put_text(payload, "action_id", action_id)
    row_id_list = _text_list(row_ids)
    if row_id_list:
        payload["row_ids"] = row_id_list
    _put_text(payload, "target_ref", target_ref)
    _put_text(payload, "status", status)
    store_status_list = _text_list(store_statuses)
    if store_status_list:
        payload["store_statuses"] = store_status_list
    _put_text(payload, "projection_refresh_state", projection_refresh_state)
    _put_text(payload, "refreshed_at_utc", refreshed_at_utc)
    if projection_refresh_seq is not None:
        payload["projection_refresh_seq"] = projection_refresh_seq
    _put_text(payload, "source_latest_event_id", source_latest_event_id)
    if extra:
        for key, value in extra.items():
            text_key = _text(key)
            if text_key and value not in ("", None, (), []):
                payload[text_key] = value
    return payload


def packet_arrival_invalidation_payload(
    *,
    packet_id: str,
    source_event_id: str,
) -> dict[str, object]:
    """Return the packet-arrival invalidation payload used by post receipts."""
    return derived_state_invalidation_payload(
        contract_id=PACKET_ARRIVAL_DERIVED_STATE_INVALIDATION_CONTRACT_ID,
        source=PACKET_ARRIVAL_INVALIDATION_SOURCE,
        producer_id="review_channel.packet_arrival",
        producer_kind="review_channel_event",
        invalidated_consumers=REVIEW_CHANNEL_DERIVED_STATE_CONSUMERS,
        next_consumer_action="reload_event_backed_review_state_before_work_decision",
        packet_id=packet_id,
        source_event_id=source_event_id,
    )


def packet_lifecycle_transition_invalidation(
    *,
    event_type: str,
    packet_id: str,
    source_event_id: str,
    status: str,
    actor: str,
    target_ref: str = "",
) -> dict[str, object]:
    """Return invalidation metadata for ack/dismiss/apply transition events."""
    return derived_state_invalidation_payload(
        source=PACKET_LIFECYCLE_TRANSITION_INVALIDATION_SOURCE,
        producer_id="review_channel.packet_lifecycle_transition",
        producer_kind="review_channel_event",
        invalidated_consumers=REVIEW_CHANNEL_DERIVED_STATE_CONSUMERS,
        next_consumer_action="reload_event_backed_review_state_before_work_decision",
        event_type=event_type,
        packet_id=packet_id,
        source_event_id=source_event_id,
        status=status,
        target_ref=target_ref,
        extra={"actor": _text(actor)},
    )


def packet_durable_ingestion_invalidation(
    *,
    event_type: str,
    packet_id: str,
    source_event_id: str,
    status: str,
    receipt_id: str = "",
    target_ref: str = "",
) -> dict[str, object]:
    """Return invalidation metadata for packet-debt repair ingestion events."""
    return derived_state_invalidation_payload(
        source=PACKET_DURABLE_INGESTION_INVALIDATION_SOURCE,
        producer_id="review_channel.packet_durable_ingestion",
        producer_kind="review_channel_event",
        invalidated_consumers=REVIEW_CHANNEL_DERIVED_STATE_CONSUMERS,
        next_consumer_action="reload_packet_debt_and_work_board_before_work_decision",
        event_type=event_type,
        packet_id=packet_id,
        source_event_id=source_event_id,
        status=status,
        receipt_id=receipt_id,
        target_ref=target_ref,
    )


def plan_ingestion_invalidation_payload(
    *,
    source_ref: str,
    receipt_id: str,
    action_id: str,
    row_ids: Iterable[str],
    target_ref: str,
    status: str,
    store_statuses: Iterable[str],
    packet_id: str = "",
    invalidated: bool = True,
) -> dict[str, object]:
    """Return invalidation metadata for PlanIntentIngestionReceipt rows."""
    return derived_state_invalidation_payload(
        source=PLAN_INGESTION_INVALIDATION_SOURCE,
        producer_id="develop.plan_ingestion",
        producer_kind="typed_receipt",
        invalidated=invalidated,
        invalidated_consumers=PLAN_INGESTION_DERIVED_STATE_CONSUMERS,
        next_consumer_action="reload_plan_authority_and_ingestion_receipts_before_work_decision",
        source_ref=source_ref,
        packet_id=packet_id,
        receipt_id=receipt_id,
        action_id=action_id,
        row_ids=row_ids,
        target_ref=target_ref,
        status=status,
        store_statuses=store_statuses,
    )


def session_liveness_invalidation_payload(
    *,
    provider: str,
    session_name: str,
    source_event_id: str,
    status: str,
) -> dict[str, object]:
    """Return invalidation metadata for participant liveness events."""
    return derived_state_invalidation_payload(
        source=SESSION_LIVENESS_INVALIDATION_SOURCE,
        producer_id="review_channel.session_liveness",
        producer_kind="review_channel_event",
        invalidated_consumers=REVIEW_CHANNEL_DERIVED_STATE_CONSUMERS,
        next_consumer_action="reload_session_liveness_before_work_decision",
        source_event_id=source_event_id,
        source_ref=f"session:{provider}:{session_name}",
        status=status,
    )


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
    "PACKET_ARRIVAL_DERIVED_STATE_INVALIDATION_CONTRACT_ID",
    "PACKET_ARRIVAL_INVALIDATION_SOURCE",
    "PACKET_DURABLE_INGESTION_INVALIDATION_SOURCE",
    "PACKET_LIFECYCLE_TRANSITION_INVALIDATION_SOURCE",
    "PLAN_INGESTION_DERIVED_STATE_CONSUMERS",
    "PLAN_INGESTION_INVALIDATION_SOURCE",
    "REVIEW_CHANNEL_DERIVED_STATE_CONSUMERS",
    "SESSION_LIVENESS_INVALIDATION_SOURCE",
    "derived_state_invalidation_payload",
    "packet_arrival_invalidation_payload",
    "packet_durable_ingestion_invalidation",
    "packet_lifecycle_transition_invalidation",
    "plan_ingestion_invalidation_payload",
    "session_liveness_invalidation_payload",
]
