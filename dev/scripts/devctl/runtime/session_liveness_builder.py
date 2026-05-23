"""Build runtime-owned session liveness signals from status evidence."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from .session_liveness_signal import (
    SessionLivenessInputs,
    SessionLivenessSignal,
    classify_session_liveness,
)
from .role_profile import normalize_role_id, role_capability_classes


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
    role = _typed_role_for_provider(provider, bridge_liveness) or "unbound"
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
    if "review" not in role_capability_classes(
        _typed_role_for_provider(provider, bridge_liveness)
    ):
        return False
    return bool(bridge_liveness.get("reviewer_supervisor_running"))


def _typed_role_for_provider(
    provider: str,
    bridge_liveness: Mapping[str, object],
) -> str:
    normalized_provider = str(provider or "").strip().lower()
    for row in _explicit_role_rows(bridge_liveness):
        row_provider = str(row.get("provider") or row.get("actor_id") or "").strip().lower()
        role = _role_from_row(row)
        if row_provider == normalized_provider and role:
            return role
    for field_name in (
        "reviewer_capability",
        "implementer_capability",
        "operator_capability",
    ):
        capability = bridge_liveness.get(field_name)
        if not isinstance(capability, Mapping):
            continue
        capability_provider = str(capability.get("provider") or "").strip().lower()
        if capability_provider == normalized_provider:
            return normalize_role_id(
                capability.get("role")
                or capability.get("role_id")
                or capability.get("target_role")
            )
    return ""


def _explicit_role_rows(
    bridge_liveness: Mapping[str, object],
) -> tuple[Mapping[str, object], ...]:
    rows: list[Mapping[str, object]] = []
    for field_name in (
        "session_liveness_signals",
        "participant_liveness",
        "active_participants",
        "role_assignments",
    ):
        value = bridge_liveness.get(field_name)
        if not isinstance(value, (list, tuple)):
            continue
        rows.extend(row for row in value if isinstance(row, Mapping))
    collaboration = bridge_liveness.get("collaboration")
    if isinstance(collaboration, Mapping):
        value = collaboration.get("role_assignments")
        if isinstance(value, (list, tuple)):
            rows.extend(row for row in value if isinstance(row, Mapping))
    return tuple(rows)


def _role_from_row(row: Mapping[str, object]) -> str:
    role = normalize_role_id(
        row.get("role")
        or row.get("actor_role")
        or row.get("role_id")
        or row.get("role_preset")
        or row.get("target_role")
    )
    if role:
        if role == "lead_agent":
            return "orchestrator"
        if role == "review_agent":
            return "architecture_review"
        if role == "coding_agent":
            return "implementation"
        if role == "operator_agent":
            return "operator"
        return role
    return ""


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
    return _ordered_unique(
        list(_string_values(bridge_liveness.get("active_conductor_providers")))
    )


def _poll_age_for_provider(
    *,
    provider: str,
    role: str,
    bridge_liveness: Mapping[str, object],
) -> int | None:
    if "review" not in role_capability_classes(role):
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
