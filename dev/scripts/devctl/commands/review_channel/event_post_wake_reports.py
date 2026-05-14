"""Wake report payload helpers for event-backed packet posts."""

from __future__ import annotations

from collections.abc import Mapping

PACKET_ARRIVAL_ATTENTION_SHAPE = "packet_arrival"
PACKET_ARRIVAL_INVALIDATION_SOURCE = "packet_arrival_event"
PACKET_WAKE_PIVOT_EVENT = "packet_wake_attempted"
PACKET_ARRIVAL_DERIVED_STATE_CONSUMERS = (
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


def wake_report_payload(
    status_snapshot: object,
    review_state_payload: Mapping[str, object],
) -> dict[str, object]:
    """Build the report payload expected by wake primitives."""
    report: dict[str, object] = {}
    report["bridge_liveness"] = dict(status_snapshot.bridge_liveness)
    report["packet_inbox"] = dict(review_state_payload.get("packet_inbox") or {})
    report["packets"] = list(review_state_payload.get("packets") or [])
    report["coordination"] = review_state_payload.get("coordination")
    report["coordination_state"] = review_state_payload.get("coordination_state")
    report["agent_sync"] = review_state_payload.get("agent_sync")
    report["agent_work_board"] = review_state_payload.get("agent_work_board")
    report["agent_loop_decisions"] = review_state_payload.get("agent_loop_decisions")
    report["reviewer_runtime"] = review_state_payload.get("reviewer_runtime")
    report["authority_snapshot"] = review_state_payload.get("authority_snapshot")
    return report


def wake_receipt_with_attention_decision(
    wake: dict[str, object],
) -> dict[str, object]:
    """Return a wake receipt payload annotated with attention metadata."""
    if not bool(wake.get("attempted")):
        return wake
    enriched = dict(wake)
    enriched.setdefault("attention_decision_shape", PACKET_ARRIVAL_ATTENTION_SHAPE)
    enriched.setdefault("next_pivot_event", PACKET_WAKE_PIVOT_EVENT)
    return enriched


def wake_error(
    *,
    packet: Mapping[str, object],
    reason: str,
    detail: str,
    target_agent: str = "",
) -> dict[str, object]:
    """Return a failed wake report."""
    report = _base_wake_report(packet=packet, attempted=True, reason=reason)
    if target_agent:
        report["target_agent"] = target_agent
    if detail:
        report["warnings"] = [detail]
    return report


def wake_skipped(
    *,
    packet: Mapping[str, object],
    reason: str,
) -> dict[str, object]:
    """Return a skipped wake report."""
    return _base_wake_report(packet=packet, attempted=False, reason=reason)


def packet_delivery_recorded_without_wake(
    *,
    packet: Mapping[str, object],
    target_agent: str,
    posted_review_state_payload: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Return the post-packet scheduling receipt.

    Packet delivery is communication and typed-state input. It must not become
    process authority; session start/rollover belongs to scheduler/runtime
    controllers that consume typed state after a task boundary.
    """
    report = _base_wake_report(
        packet=packet,
        attempted=False,
        reason="packet_delivery_records_typed_attention_only",
    )
    report["target_agent"] = target_agent
    report["target_role"] = _text(packet.get("target_role"))
    report["target_session_id"] = _text(packet.get("target_session_id"))
    report["attention_recorded"] = True
    report["wake_method"] = "none"
    report["derived_state_invalidated"] = True
    report["derived_state_invalidation"] = (
        packet_arrival_derived_state_invalidation(
            packet=packet,
            posted_review_state_payload=posted_review_state_payload,
        )
    )
    report["warnings"] = [
        "Packet delivery does not launch, replace, or externally wake agent "
        "sessions; scheduler/runtime controllers must consume typed packet "
        "state and decide session work at explicit task boundaries."
    ]
    return report


def packet_arrival_derived_state_invalidation(
    *,
    packet: Mapping[str, object],
    posted_review_state_payload: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Describe existing derived-state subscribers affected by packet arrival."""
    report: dict[str, object] = {
        "contract_id": "PacketArrivalDerivedStateInvalidation",
        "schema_version": 1,
        "source": PACKET_ARRIVAL_INVALIDATION_SOURCE,
        "invalidated": True,
        "packet_id": _text(packet.get("packet_id")),
        "source_event_id": _text(
            packet.get("latest_event_id") or packet.get("event_id")
        ),
        "invalidated_consumers": list(PACKET_ARRIVAL_DERIVED_STATE_CONSUMERS),
        "next_consumer_action": "reload_event_backed_review_state_before_work_decision",
    }
    if posted_review_state_payload is None:
        report["projection_refresh_state"] = "refresh_required_at_consumer_boundary"
        return report

    report["projection_refresh_state"] = "refreshed_by_packet_post_reducer"
    if posted_review_state_payload.get("timestamp"):
        report["refreshed_at_utc"] = _text(
            posted_review_state_payload.get("timestamp")
        )
    work_board = posted_review_state_payload.get("agent_work_board")
    if isinstance(work_board, Mapping):
        refresh_seq = work_board.get("projection_refresh_seq")
        if refresh_seq is not None:
            report["projection_refresh_seq"] = refresh_seq
        source_latest_event_id = _text(work_board.get("source_latest_event_id"))
        if source_latest_event_id:
            report["source_latest_event_id"] = source_latest_event_id
    return report


def wake_attention_recorded_without_conductor(
    *,
    packet: Mapping[str, object],
    target_agent: str,
) -> dict[str, object]:
    """Return the typed-attention fallback when no conductor wake occurred."""
    report = _base_wake_report(
        packet=packet,
        attempted=True,
        reason="packet_arrival_attention_recorded_without_conductor_wake",
    )
    report["wake_method"] = "typed_attention_event"
    report["target_agent"] = target_agent
    report["target_role"] = _text(packet.get("target_role"))
    report["target_session_id"] = _text(packet.get("target_session_id"))
    return report


def wake_target_session_binding_required(
    *,
    packet: Mapping[str, object],
    target_agent: str,
) -> dict[str, object]:
    """Return an attention-only receipt for unbound provider wake attempts."""
    report = _base_wake_report(
        packet=packet,
        attempted=True,
        reason="target_session_binding_required",
    )
    report["wake_method"] = "typed_attention_event"
    report["target_agent"] = target_agent
    report["target_role"] = _text(packet.get("target_role"))
    report["target_session_id"] = _text(packet.get("target_session_id"))
    report["visible_session_woke"] = False
    report["warnings"] = [
        "Provider wake suppressed: packet lacks actor role/session routing, "
        "so launching a fresh session would not prove the intended actor "
        "consumed it."
    ]
    return report


def _base_wake_report(
    *,
    packet: Mapping[str, object],
    attempted: bool,
    reason: str,
) -> dict[str, object]:
    return {
        "attempted": attempted,
        "woke": False,
        "reason": reason,
        "packet_id": _text(packet.get("packet_id")),
        "requested_action": _text(packet.get("requested_action")),
    }


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = [
    "PACKET_ARRIVAL_ATTENTION_SHAPE",
    "PACKET_ARRIVAL_DERIVED_STATE_CONSUMERS",
    "PACKET_ARRIVAL_INVALIDATION_SOURCE",
    "PACKET_WAKE_PIVOT_EVENT",
    "packet_arrival_derived_state_invalidation",
    "packet_delivery_recorded_without_wake",
    "wake_attention_recorded_without_conductor",
    "wake_error",
    "wake_receipt_with_attention_decision",
    "wake_report_payload",
    "wake_skipped",
    "wake_target_session_binding_required",
]
