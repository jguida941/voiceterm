"""Action-request lifecycle field derivation."""

from __future__ import annotations


def derive_action_request_lifecycle_fields(
    row: dict[str, object],
    *,
    acknowledged_events: list[dict[str, object]],
    acted_on_events: list[dict[str, object]],
) -> dict[str, object]:
    """Derive runtime fields from action-request lifecycle events."""
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
        event_action = _text(event.get("action"))
        event_kind = _text(event.get("event_kind"))
        if event_action == action or event_kind == action:
            return event
    return {}


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = ["derive_action_request_lifecycle_fields"]
