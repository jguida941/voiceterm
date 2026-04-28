"""Bridge-liveness count helpers for observed control topology."""

from __future__ import annotations

from collections.abc import Mapping

from .session_liveness_counts import (
    live_session_provider_count,
    live_session_role_counts,
)


def active_conductor_count(
    *,
    bridge: Mapping[str, object],
    live_participants: list[Mapping[str, object]],
) -> int:
    """Return live conductor count from bridge evidence, falling back to participants."""
    signal_count = live_session_provider_count(
        bridge.get("session_liveness_signals") or bridge.get("participant_liveness")
    )
    if signal_count is not None:
        return signal_count
    providers = bridge.get("active_conductor_providers")
    if isinstance(providers, (list, tuple)):
        normalized = {
            str(provider).strip()
            for provider in providers
            if str(provider).strip()
        }
        if normalized:
            return len(normalized)
    codex_live = bool_or_none(bridge.get("codex_conductor_active"))
    claude_live = bool_or_none(bridge.get("claude_conductor_active"))
    if codex_live is not None or claude_live is not None:
        return int(bool(codex_live)) + int(bool(claude_live))
    return len(live_participants)


def bridge_role_counts(bridge: Mapping[str, object]) -> dict[str, int]:
    """Return live reviewer/implementer counts from bridge liveness."""
    signal_counts = live_session_role_counts(
        bridge.get("session_liveness_signals") or bridge.get("participant_liveness")
    )
    if signal_counts is not None:
        return signal_counts
    codex_live = bool_or_none(bridge.get("codex_conductor_active"))
    claude_live = bool_or_none(bridge.get("claude_conductor_active"))
    if codex_live is not None or claude_live is not None:
        return {
            "live_participants_total": int(bool(codex_live)) + int(bool(claude_live)),
            "live_reviewer_total": int(bool(codex_live)),
            "live_implementer_total": int(bool(claude_live)),
        }
    providers = bridge.get("active_conductor_providers")
    if isinstance(providers, (list, tuple)):
        normalized = [
            str(provider).strip().lower()
            for provider in providers
            if str(provider).strip()
        ]
        return {
            "live_participants_total": len(normalized),
            "live_reviewer_total": sum(1 for provider in normalized if provider == "codex"),
            "live_implementer_total": sum(
                1 for provider in normalized if provider == "claude"
            ),
        }
    return {
        "live_participants_total": 0,
        "live_reviewer_total": 0,
        "live_implementer_total": 0,
    }


def bridge_provider_count(bridge: Mapping[str, object], provider_name: str) -> int:
    """Count live provider entries in bridge liveness."""
    providers = bridge.get("active_conductor_providers")
    if not isinstance(providers, (list, tuple)):
        return 0
    provider = provider_name.strip().lower()
    return sum(
        1
        for item in providers
        if str(item or "").strip().lower() == provider
    )


def bool_or_none(value: object) -> bool | None:
    """Normalize explicit bridge booleans while preserving missing evidence."""
    if value is None:
        return None
    return boolish(value)


def boolish(value: object) -> bool:
    """Normalize loose bool values used in runtime projections."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)
