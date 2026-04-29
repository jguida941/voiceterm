"""Lifecycle/disposition projection for event-backed review packets."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass

PACKET_LIFECYCLE_HISTORY_CONTRACT_ID = "PacketLifecycleHistory"
PACKET_DISPOSITION_CONTRACT_ID = "PacketDisposition"

_ACK_EVENT_TYPE = "packet_acked"
_ACTION_BY_EVENT_TYPE = {
    "packet_applied": "applied",
    "packet_dismissed": "dismissed",
    "packet_expired": "archived",
    "action_request_execution_failed": "failed",
    "action_request_apply_pending_after_execution": "apply_pending_after_execution",
}
ACTION_REQUEST_LIFECYCLE_EVENT_TYPES = frozenset(
    {
        "action_request_execution_failed",
        "action_request_apply_pending_after_execution",
    }
)


@dataclass(frozen=True, slots=True)
class PacketLifecycleEvent:
    """One packet acknowledgement or acted-on lifecycle event."""

    event_id: str
    at_utc: str
    by_agent: str
    reason: str
    event_kind: str = ""
    action: str = ""
    target_anchor: str = ""
    guard_attestation: dict[str, object] | None = None


@dataclass(frozen=True, slots=True)
class PacketDisposition:
    """Typed disposition sink for a review packet."""

    sink: str
    status: str
    resolution_anchor: str
    reason: str
    schema_version: int = 1
    contract_id: str = PACKET_DISPOSITION_CONTRACT_ID
    plan_target: str = ""
    next_slice_target: str = ""
    archive_classification: str = ""


@dataclass(frozen=True, slots=True)
class PacketLifecycleHistory:
    """Reduced lifecycle history attached to every packet row."""

    posted_at: str
    posted_by: str
    acknowledged_events: list[dict[str, object]]
    acted_on_events: list[dict[str, object]]
    current_state: str
    resolution_anchor: str
    schema_version: int = 1
    contract_id: str = PACKET_LIFECYCLE_HISTORY_CONTRACT_ID


def project_packet_lifecycle(
    packet: Mapping[str, object],
    *,
    stale_pending: bool = False,
) -> dict[str, object]:
    """Return packet fields enriched with lifecycle and disposition state."""
    row = dict(packet)
    acknowledged_events = _dict_rows(row.get("acknowledged_events"))
    acted_on_events = _dict_rows(row.get("acted_on_events"))
    row = _derive_action_request_lifecycle_fields(
        row,
        acknowledged_events=acknowledged_events,
        acted_on_events=acted_on_events,
    )

    if stale_pending and not acted_on_events:
        acted_on_events = [_clock_expired_action(row)]

    disposition = _disposition_for_packet(
        row,
        acted_on_events=acted_on_events,
        stale_pending=stale_pending,
    )
    current_state = _current_state(
        row,
        acknowledged_events=acknowledged_events,
        acted_on_events=acted_on_events,
    )
    resolution_anchor = _text(disposition.get("resolution_anchor"))

    row["acknowledged_events"] = acknowledged_events
    row["acted_on_events"] = acted_on_events
    row["lifecycle_current_state"] = current_state
    row["resolution_anchor"] = resolution_anchor
    row["disposition"] = disposition
    row["lifecycle_history"] = asdict(
        PacketLifecycleHistory(
            posted_at=_text(row.get("posted_at")),
            posted_by=_text(row.get("from_agent")),
            acknowledged_events=acknowledged_events,
            acted_on_events=acted_on_events,
            current_state=current_state,
            resolution_anchor=resolution_anchor,
        )
    )
    return row


def apply_lifecycle_transition(
    packet: Mapping[str, object],
    event: Mapping[str, object],
) -> dict[str, object]:
    """Append lifecycle event rows for one packet transition event."""
    row = dict(packet)
    event_type = _text(event.get("event_type"))

    if event_type == _ACK_EVENT_TYPE:
        row["acknowledged_events"] = [
            *_dict_rows(row.get("acknowledged_events")),
            *_ack_events(event, row),
        ]
    elif event_type in _ACTION_BY_EVENT_TYPE:
        row["acted_on_events"] = [
            *_dict_rows(row.get("acted_on_events")),
            _action_event(event, row),
        ]

    return project_packet_lifecycle(row)


def _ack_events(
    event: Mapping[str, object],
    packet: Mapping[str, object],
) -> list[dict[str, object]]:
    actor = _actor(event) or _text(packet.get("to_agent"))
    at_utc = _event_time(event)
    rows = [
        _drop_empty_fields(
            asdict(
                PacketLifecycleEvent(
                    event_id=_text(event.get("event_id")),
                    at_utc=at_utc,
                    by_agent=actor,
                    reason="packet_acknowledged",
                    event_kind="ack",
                )
            )
        )
    ]
    if _text(packet.get("kind")) == "action_request":
        rows.append(
            _drop_empty_fields(
                asdict(
                    PacketLifecycleEvent(
                        event_id=_text(event.get("event_id")),
                        at_utc=at_utc,
                        by_agent=actor,
                        reason="action_request_execution_started",
                        event_kind="execution_started",
                        action="execution_started",
                        target_anchor=f"packet:{_text(packet.get('packet_id'))}",
                    )
                )
            )
        )
    return rows


def _action_event(
    event: Mapping[str, object],
    packet: Mapping[str, object],
) -> dict[str, object]:
    action = _ACTION_BY_EVENT_TYPE[_text(event.get("event_type"))]
    return _drop_empty_fields(
        asdict(
            PacketLifecycleEvent(
                event_id=_text(event.get("event_id")),
                at_utc=_text(event.get("timestamp_utc")),
                by_agent=_actor(event) or _text(packet.get("to_agent")),
                event_kind=action,
                action=action,
                target_anchor=_target_anchor(action=action, packet=packet),
                reason=_action_reason(action, event=event),
                guard_attestation=_guard_attestation(event) if action == "applied" else None,
            )
        )
    )


def _clock_expired_action(packet: Mapping[str, object]) -> dict[str, object]:
    return _drop_empty_fields(
        asdict(
            PacketLifecycleEvent(
                event_id="",
                at_utc=_text(packet.get("expires_at_utc")),
                by_agent="system",
                action="archived",
                target_anchor="archive_classification:clock_expired_without_disposition",
                reason="packet TTL elapsed before an explicit disposition event",
            )
        )
    )


def _disposition_for_packet(
    packet: Mapping[str, object],
    *,
    acted_on_events: list[dict[str, object]],
    stale_pending: bool,
) -> dict[str, object]:
    action_event = acted_on_events[-1] if acted_on_events else None
    if action_event is not None:
        return _acted_on_disposition(packet, action_event)

    status = _text(packet.get("status")) or "pending"
    if status == "expired":
        return _archive_disposition(
            status="archived",
            classification="clock_expired_without_disposition",
            reason="Expired packet status is archived for audit until explicit resolution lands.",
        )
    if _text(packet.get("kind")) == "action_request":
        recovery_disposition = _action_request_recovery_disposition(packet)
        if recovery_disposition:
            return recovery_disposition
    if stale_pending:
        return _archive_disposition(
            status="archived",
            classification="clock_expired_without_disposition",
            reason="Clock-expired pending packet is archived for audit until explicit resolution lands.",
        )

    target = _text(packet.get("to_agent")) or "unassigned"
    return asdict(
        PacketDisposition(
            sink="queued",
            status=status,
            resolution_anchor=f"slice_target:{target}_packet_queue",
            next_slice_target=f"{target}_packet_queue",
            reason="Packet remains queued until an acted-on lifecycle event resolves it.",
        )
    )


def _action_request_recovery_disposition(
    packet: Mapping[str, object],
) -> dict[str, object]:
    packet_id = _text(packet.get("packet_id"))
    if _text(packet.get("apply_pending_after_execution_at_utc")):
        return asdict(
            PacketDisposition(
                sink="recovery_required",
                status="apply_pending_after_execution",
                resolution_anchor=f"packet:{packet_id}",
                reason=(
                    _text(packet.get("apply_pending_after_execution_reason"))
                    or "Commit execution completed but packet apply remains pending."
                ),
                next_slice_target="fresh_action_request_or_explicit_recovery",
            )
        )
    if _text(packet.get("execution_failed_at_utc")):
        return asdict(
            PacketDisposition(
                sink="recovery_required",
                status="failed",
                resolution_anchor=f"packet:{packet_id}",
                reason=(
                    _text(packet.get("execution_failed_reason"))
                    or "Action-request execution failed before resolution."
                ),
                next_slice_target="fresh_action_request",
            )
        )
    return {}


def _acted_on_disposition(
    packet: Mapping[str, object],
    action_event: Mapping[str, object],
) -> dict[str, object]:
    action = _text(action_event.get("action"))
    target_anchor = _text(action_event.get("target_anchor"))

    if action == "failed":
        return asdict(
            PacketDisposition(
                sink="recovery_required",
                status="failed",
                resolution_anchor=target_anchor or f"packet:{_text(packet.get('packet_id'))}",
                reason=(
                    _text(action_event.get("reason"))
                    or "Action-request execution failed before resolution."
                ),
                next_slice_target="fresh_action_request",
            )
        )

    if action == "apply_pending_after_execution":
        return asdict(
            PacketDisposition(
                sink="recovery_required",
                status="apply_pending_after_execution",
                resolution_anchor=target_anchor or f"packet:{_text(packet.get('packet_id'))}",
                reason=(
                    _text(action_event.get("reason"))
                    or "Commit execution completed but packet apply remains pending."
                ),
                next_slice_target="fresh_action_request_or_explicit_recovery",
            )
        )

    if action == "applied" and _text(packet.get("target_kind")) == "plan":
        return asdict(
            PacketDisposition(
                sink="plan_integrated",
                status="applied",
                resolution_anchor=target_anchor,
                plan_target=target_anchor,
                reason="Applied packet targeted a canonical plan artifact.",
            )
        )

    if action == "applied":
        return _archive_disposition(
            status="applied",
            classification="applied_to_target",
            reason="Packet was acted on and resolved against its target.",
            anchor=target_anchor,
        )

    if action == "dismissed":
        return _archive_disposition(
            status="dismissed",
            classification="dismissed_with_actor",
            reason="Packet was explicitly dismissed by the addressed actor.",
            anchor=target_anchor,
        )

    return _archive_disposition(
        status="archived",
        classification="clock_expired_without_disposition",
        reason="Packet entered archive because an expiry event was recorded.",
        anchor=target_anchor,
    )


def _archive_disposition(
    *,
    status: str,
    classification: str,
    reason: str,
    anchor: str = "",
) -> dict[str, object]:
    resolution_anchor = anchor or f"archive_classification:{classification}"
    return asdict(
        PacketDisposition(
            sink="archived",
            status=status,
            resolution_anchor=resolution_anchor,
            archive_classification=classification,
            reason=reason,
        )
    )


def _current_state(
    packet: Mapping[str, object],
    *,
    acknowledged_events: list[dict[str, object]],
    acted_on_events: list[dict[str, object]],
) -> str:
    if acted_on_events:
        action = _text(acted_on_events[-1].get("action"))
        if action == "archived":
            return "archived"
        return action or _text(packet.get("status")) or "acted_on"
    if _text(packet.get("status")) == "expired":
        return "archived"
    if _text(packet.get("kind")) == "action_request":
        return _action_request_current_state(
            packet,
            acknowledged_events=acknowledged_events,
        )
    if acknowledged_events:
        return "acknowledged"
    return _text(packet.get("status")) or "pending"


def _action_request_current_state(
    packet: Mapping[str, object],
    *,
    acknowledged_events: list[dict[str, object]],
) -> str:
    if _text(packet.get("apply_pending_after_execution_at_utc")):
        return "apply_pending_after_execution"
    if _text(packet.get("execution_failed_at_utc")):
        return "failed"
    if _text(packet.get("applied_at_utc")) or _text(packet.get("status")) == "applied":
        return "applied"
    if _text(packet.get("execution_started_at_utc")):
        return "in_progress"
    if _text(packet.get("acked_at_utc")) or acknowledged_events:
        return "acknowledged"
    if _text(packet.get("delivery_observed_at_utc")):
        return "execution_pending"
    return "delivery_pending"


def _target_anchor(*, action: str, packet: Mapping[str, object]) -> str:
    if action == "dismissed":
        return "archive_classification:dismissed_with_actor"
    if action == "archived":
        return "archive_classification:clock_expired_without_disposition"
    if action in {"failed", "apply_pending_after_execution", "execution_started"}:
        return f"packet:{_text(packet.get('packet_id'))}"

    target_kind = _text(packet.get("target_kind"))
    target_ref = _text(packet.get("target_ref"))
    target_revision = _text(packet.get("target_revision"))
    if target_kind == "plan" and target_ref:
        suffix = f"@{target_revision}" if target_revision else ""
        return f"plan_target:{target_ref}{suffix}"
    if target_kind and target_ref:
        suffix = f"@{target_revision}" if target_revision else ""
        return f"{target_kind}:{target_ref}{suffix}"
    return f"packet:{_text(packet.get('packet_id'))}"


def _action_reason(action: str, *, event: Mapping[str, object]) -> str:
    metadata = event.get("metadata")
    reason = ""
    if isinstance(metadata, Mapping):
        reason = _text(metadata.get("reason"))
    if reason:
        return reason
    if action == "applied":
        return "packet_applied"
    if action == "dismissed":
        return "packet_dismissed"
    if action == "failed":
        return "action_request_execution_failed"
    if action == "apply_pending_after_execution":
        return "packet_apply_failed_after_commit"
    return "packet_expired"


def _actor(event: Mapping[str, object]) -> str:
    metadata = event.get("metadata")
    if not isinstance(metadata, Mapping):
        return _text(
            event.get("actor")
            or event.get("execution_started_by")
            or event.get("acked_by")
        )
    return _text(metadata.get("actor"))


def _event_time(event: Mapping[str, object]) -> str:
    return _text(
        event.get("timestamp_utc")
        or event.get("acked_at_utc")
        or event.get("execution_started_at_utc")
        or event.get("applied_at_utc")
    )


def _guard_attestation(event: Mapping[str, object]) -> dict[str, object] | None:
    metadata = event.get("metadata")
    if not isinstance(metadata, Mapping):
        return None
    attestation = metadata.get("guard_attestation")
    if not isinstance(attestation, Mapping):
        return None
    return dict(attestation)


def _derive_action_request_lifecycle_fields(
    row: dict[str, object],
    *,
    acknowledged_events: list[dict[str, object]],
    acted_on_events: list[dict[str, object]],
) -> dict[str, object]:
    if _text(row.get("kind")) != "action_request":
        return row
    derived = dict(row)
    started = _last_event_with_action(acknowledged_events, "execution_started")
    failed = _last_event_with_action(acted_on_events, "failed")
    apply_pending = _last_event_with_action(
        acted_on_events,
        "apply_pending_after_execution",
    )
    if started:
        derived["execution_started_at_utc"] = _text(started.get("at_utc"))
        derived["execution_started_by"] = _text(started.get("by_agent"))
    if failed:
        derived["execution_failed_at_utc"] = _text(failed.get("at_utc"))
        derived["execution_failed_by"] = _text(failed.get("by_agent"))
        derived["execution_failed_reason"] = _text(failed.get("reason"))
    if apply_pending:
        derived["apply_pending_after_execution_at_utc"] = _text(
            apply_pending.get("at_utc")
        )
        derived["apply_pending_after_execution_by"] = _text(
            apply_pending.get("by_agent")
        )
        derived["apply_pending_after_execution_reason"] = _text(
            apply_pending.get("reason")
        )
    return derived


def _last_event_with_action(
    events: list[dict[str, object]],
    action: str,
) -> dict[str, object]:
    for event in reversed(events):
        if _text(event.get("action")) == action or _text(event.get("event_kind")) == action:
            return event
    return {}


def _dict_rows(value: object) -> list[dict[str, object]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _drop_empty_fields(payload: dict[str, object]) -> dict[str, object]:
    return {key: value for key, value in payload.items() if value}


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = [
    "ACTION_REQUEST_LIFECYCLE_EVENT_TYPES",
    "PACKET_DISPOSITION_CONTRACT_ID",
    "PACKET_LIFECYCLE_HISTORY_CONTRACT_ID",
    "apply_lifecycle_transition",
    "project_packet_lifecycle",
]
