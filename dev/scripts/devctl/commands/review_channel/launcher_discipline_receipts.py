"""Event-store persistence for launcher-discipline bypass receipts."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from ...review_channel.event_store import append_event, idempotency_key, load_events
from ...time_utils import utc_timestamp

_BYPASS_EVENT_TYPE = "launcher_discipline_bypassed"


def persist_launcher_discipline_bypass_receipt(
    *,
    artifact_paths: object,
    receipt: dict[str, object] | None,
) -> dict[str, object] | None:
    """Persist a launcher-discipline bypass receipt once."""
    if receipt is None:
        return None
    event_log_path = _bypass_event_log_path(artifact_paths)
    if event_log_path is None:
        raise ValueError(
            "Launcher discipline bypass requires review-channel artifact paths "
            "so the override can be audited."
        )
    existing_events = load_events(event_log_path)
    key = _bypass_idempotency_key(receipt)
    existing = _existing_bypass_event(existing_events, key)
    if existing is not None:
        return existing
    event = dict(
        receipt,
        schema_version=1,
        event_type=_BYPASS_EVENT_TYPE,
        timestamp_utc=utc_timestamp(),
        source="launcher_discipline",
        idempotency_key=key,
    )
    try:
        return append_event(event_log_path, event, existing_events=existing_events)
    except ValueError as exc:
        if "Duplicate review-channel idempotency_key" not in str(exc):
            raise
        return _existing_bypass_event(load_events(event_log_path), key)


def _bypass_idempotency_key(receipt: Mapping[str, object]) -> str:
    return idempotency_key(
        receipt.get("bypass_reason", ""),
        receipt.get("terminal_arg", ""),
        receipt.get("interaction_mode", ""),
    )


def _bypass_event_log_path(artifact_paths: object) -> Path | None:
    if artifact_paths is None:
        return None
    raw_path = (
        artifact_paths.get("event_log_path")
        if isinstance(artifact_paths, Mapping)
        else getattr(artifact_paths, "event_log_path", None)
    )
    return Path(raw_path) if raw_path else None


def _existing_bypass_event(
    events: list[dict[str, object]],
    key: str,
) -> dict[str, object] | None:
    for event in events:
        if (
            str(event.get("event_type") or "") == _BYPASS_EVENT_TYPE
            and str(event.get("idempotency_key") or "") == key
        ):
            return event
    return None


__all__ = ["persist_launcher_discipline_bypass_receipt"]
