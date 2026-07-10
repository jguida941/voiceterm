"""Read-model helpers for runtime session liveness signals."""

from __future__ import annotations

from collections.abc import Mapping

from .session_liveness_signal import (
    LIVE_SESSION_LIVENESS_STATES,
    RUNTIME_PRESENT_LIVENESS_STATES,
)


def provider_liveness_state(rows: object, provider_name: str) -> str | None:
    """Return the typed liveness state for one provider, when present."""
    provider = provider_name.strip().lower()
    for row in _signal_rows(rows):
        if str(row.get("provider") or "").strip().lower() != provider:
            continue
        state = str(row.get("state") or "").strip()
        return state or None
    return None


def provider_has_live_session(rows: object, provider_name: str) -> bool | None:
    """Return whether typed liveness proves a live provider session."""
    state = provider_liveness_state(rows, provider_name)
    if state is None:
        return None
    return state in LIVE_SESSION_LIVENESS_STATES


def provider_has_runtime_presence(rows: object, provider_name: str) -> bool | None:
    """Return whether typed liveness proves any runtime presence."""
    state = provider_liveness_state(rows, provider_name)
    if state is None:
        return None
    return state in RUNTIME_PRESENT_LIVENESS_STATES


def live_session_provider_count(rows: object) -> int | None:
    """Count unique providers with a live typed session."""
    signals = _signal_rows(rows)
    if not signals:
        return None
    providers = {
        str(row.get("provider") or "").strip().lower()
        for row in signals
        if str(row.get("state") or "").strip() in LIVE_SESSION_LIVENESS_STATES
        and str(row.get("provider") or "").strip()
    }
    return len(providers)


def live_session_role_counts(rows: object) -> dict[str, int] | None:
    """Return live participant totals grouped by tandem role."""
    signals = _signal_rows(rows)
    if not signals:
        return None
    live_rows = [
        row
        for row in signals
        if str(row.get("state") or "").strip() in LIVE_SESSION_LIVENESS_STATES
    ]
    return {
        "live_participants_total": len(
            {
                str(row.get("provider") or "").strip().lower()
                for row in live_rows
                if str(row.get("provider") or "").strip()
            }
        ),
        "live_reviewer_total": _live_role_count(live_rows, "reviewer"),
        "live_implementer_total": _live_role_count(live_rows, "implementer"),
    }


def _live_role_count(rows: list[Mapping[str, object]], role_name: str) -> int:
    providers = {
        str(row.get("provider") or "").strip().lower()
        for row in rows
        if str(row.get("role") or "").strip().lower() == role_name
        and str(row.get("provider") or "").strip()
    }
    return len(providers)


def _signal_rows(rows: object) -> list[Mapping[str, object]]:
    if not isinstance(rows, (list, tuple)):
        return []
    return [row for row in rows if isinstance(row, Mapping)]


__all__ = [
    "live_session_provider_count",
    "live_session_role_counts",
    "provider_has_live_session",
    "provider_has_runtime_presence",
    "provider_liveness_state",
]
