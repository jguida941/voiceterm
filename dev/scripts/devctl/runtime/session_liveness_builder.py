"""Build runtime-owned session liveness signals from status evidence."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from .role_profile import role_for_provider
from .session_liveness_signal import (
    SessionLivenessInputs,
    SessionLivenessSignal,
    classify_session_liveness,
)


def build_session_liveness_signals(
    *,
    bridge_liveness: Mapping[str, object],
    active_providers: Sequence[str],
) -> list[SessionLivenessSignal]:
    """Return one canonical liveness signal for each observed provider."""
    providers = _ordered_unique(
        [
            *active_providers,
            *_runtime_provider_set(bridge_liveness),
            *_bridge_active_provider_set(bridge_liveness),
        ]
    )
    return [
        _signal_for_provider(
            provider=provider,
            bridge_liveness=bridge_liveness,
            active_providers=active_providers,
        )
        for provider in providers
    ]


def session_liveness_rows(
    signals: Sequence[SessionLivenessSignal],
) -> list[dict[str, object]]:
    """Serialize liveness signals for review-state and dashboard payloads."""
    return [signal.to_dict() for signal in signals]


def _signal_for_provider(
    *,
    provider: str,
    bridge_liveness: Mapping[str, object],
    active_providers: Sequence[str],
) -> SessionLivenessSignal:
    role = role_for_provider(provider).value
    return classify_session_liveness(
        SessionLivenessInputs(
            provider=provider,
            role=role,
            publisher_running=bool(bridge_liveness.get("publisher_running")),
            reviewer_supervisor_running=_reviewer_daemon_running(
                provider=provider,
                bridge_liveness=bridge_liveness,
            ),
            conductor_active=(
                provider in active_providers
                or bool(bridge_liveness.get(f"{provider}_conductor_active"))
            ),
            runtime_activity_active=provider in _runtime_provider_set(bridge_liveness),
            poll_age_seconds=_poll_age_for_provider(
                provider=provider,
                role=role,
                bridge_liveness=bridge_liveness,
            ),
        ),
    )


def _reviewer_daemon_running(
    *,
    provider: str,
    bridge_liveness: Mapping[str, object],
) -> bool:
    if role_for_provider(provider).value != "reviewer":
        return False
    return bool(bridge_liveness.get("reviewer_supervisor_running"))


def _runtime_provider_set(bridge_liveness: Mapping[str, object]) -> tuple[str, ...]:
    return _ordered_unique(
        [
            *_string_values(bridge_liveness.get("active_runtime_providers")),
            *_string_values(bridge_liveness.get("remote_control_active_providers")),
            *_string_values(bridge_liveness.get("packet_activity_active_providers")),
        ]
    )


def _bridge_active_provider_set(
    bridge_liveness: Mapping[str, object],
) -> tuple[str, ...]:
    providers = list(_string_values(bridge_liveness.get("active_conductor_providers")))
    if bool(bridge_liveness.get("codex_conductor_active")):
        providers.append("codex")
    if bool(bridge_liveness.get("claude_conductor_active")):
        providers.append("claude")
    return _ordered_unique(providers)


def _poll_age_for_provider(
    *,
    provider: str,
    role: str,
    bridge_liveness: Mapping[str, object],
) -> int | None:
    if provider != "codex" and role != "reviewer":
        return None
    return _int_or_none(
        bridge_liveness.get("last_reviewer_poll_age_seconds")
        or bridge_liveness.get("last_codex_poll_age_seconds")
    )


def _string_values(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple, set, frozenset)):
        return ()
    return tuple(
        str(item).strip().lower()
        for item in value
        if str(item or "").strip()
    )


def _ordered_unique(values: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        normalized = str(value or "").strip().lower()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return tuple(ordered)


def _int_or_none(value: object) -> int | None:
    try:
        return int(value) if value is not None and str(value).strip() else None
    except (TypeError, ValueError):
        return None


__all__ = [
    "build_session_liveness_signals",
    "session_liveness_rows",
]
