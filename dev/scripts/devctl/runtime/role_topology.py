"""Role-based live topology helpers.

Provider ids such as ``codex`` and ``claude`` are runtime adapter labels.
Authority decisions should derive from occupied roles and liveness evidence.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from .role_profile import TandemRole, default_provider_for_role, role_for_provider
from .session_liveness_signal import (
    LIVE_SESSION_LIVENESS_STATES,
    RUNTIME_PRESENT_LIVENESS_STATES,
)
from .value_coercion import coerce_bool


@dataclass(frozen=True, slots=True)
class LiveRoleTopology:
    """Live role counts and provider occupancy for one topology snapshot."""

    reviewer_provider: str
    implementer_providers: tuple[str, ...]
    live_reviewer_providers: tuple[str, ...]
    live_implementer_providers: tuple[str, ...]
    live_operator_providers: tuple[str, ...]
    active_providers: tuple[str, ...]

    @property
    def live_reviewer(self) -> bool:
        for _provider in self.live_reviewer_providers:
            return True
        return False

    @property
    def live_implementer(self) -> bool:
        for _provider in self.live_implementer_providers:
            return True
        return False

    @property
    def missing_required_roles(self) -> tuple[str, ...]:
        missing: list[str] = []
        if not self.live_reviewer:
            missing.append(TandemRole.REVIEWER.value)
        if not self.live_implementer:
            missing.append(TandemRole.IMPLEMENTER.value)
        return tuple(missing)

    def role_counts(self) -> dict[str, int]:
        return {
            "live_participants_total": len(
                set(
                    [
                        *self.live_reviewer_providers,
                        *self.live_implementer_providers,
                        *self.live_operator_providers,
                    ]
                )
            ),
            "live_reviewer_total": len(self.live_reviewer_providers),
            "live_implementer_total": len(self.live_implementer_providers),
        }


def resolve_role_topology(
    bridge_liveness: Mapping[str, object],
    *,
    include_runtime_presence: bool = False,
) -> LiveRoleTopology:
    """Resolve occupied runtime roles from typed liveness evidence."""
    live_states = (
        RUNTIME_PRESENT_LIVENESS_STATES
        if include_runtime_presence
        else LIVE_SESSION_LIVENESS_STATES
    )
    reviewer_provider = (
        _capability_provider(bridge_liveness, "reviewer_capability")
        or _first_signal_provider_for_role(
            bridge_liveness,
            TandemRole.REVIEWER.value,
            live_states=live_states,
        )
        or default_provider_for_role(TandemRole.REVIEWER)
    )
    implementer_providers = _implementer_providers(
        bridge_liveness,
        live_states=live_states,
    )
    active_providers = _active_providers(
        bridge_liveness,
        include_runtime_presence=include_runtime_presence,
    )
    reviewer_live: list[str] = []
    implementer_live: list[str] = []
    operator_live: list[str] = []
    for provider in active_providers:
        normalized_provider = str(provider or "").strip().lower()
        matched_explicit_role = False
        if normalized_provider == reviewer_provider:
            _append_unique(reviewer_live, provider)
            matched_explicit_role = True
        if normalized_provider in implementer_providers:
            _append_unique(implementer_live, provider)
            matched_explicit_role = True
        if matched_explicit_role:
            continue
        role = _role_for_provider(
            provider,
            bridge_liveness=bridge_liveness,
            reviewer_provider=reviewer_provider,
            implementer_providers=implementer_providers,
        )
        if role == TandemRole.OPERATOR.value:
            _append_unique(operator_live, provider)
        elif role == TandemRole.REVIEWER.value:
            _append_unique(reviewer_live, provider)
        elif role == TandemRole.IMPLEMENTER.value:
            _append_unique(implementer_live, provider)
    for provider, role in _live_signal_roles(
        bridge_liveness,
        live_states=live_states,
    ):
        if role == TandemRole.REVIEWER.value:
            _append_unique(reviewer_live, provider)
        elif role == TandemRole.IMPLEMENTER.value:
            _append_unique(implementer_live, provider)
        elif role == TandemRole.OPERATOR.value:
            _append_unique(operator_live, provider)
    return LiveRoleTopology(
        reviewer_provider=reviewer_provider,
        implementer_providers=implementer_providers,
        live_reviewer_providers=tuple(reviewer_live),
        live_implementer_providers=tuple(implementer_live),
        live_operator_providers=tuple(operator_live),
        active_providers=active_providers,
    )


def _implementer_providers(
    bridge_liveness: Mapping[str, object],
    *,
    live_states: frozenset[str],
) -> tuple[str, ...]:
    providers: list[str] = []
    provider = _capability_provider(bridge_liveness, "implementer_capability")
    if provider:
        providers.append(provider)
    for signal_provider, role in _live_signal_roles(
        bridge_liveness,
        live_states=live_states,
    ):
        if role == TandemRole.IMPLEMENTER.value:
            _append_unique(providers, signal_provider)
    if not providers:
        providers.append(default_provider_for_role(TandemRole.IMPLEMENTER))
    return tuple(providers)


def _active_providers(
    bridge_liveness: Mapping[str, object],
    *,
    include_runtime_presence: bool,
) -> tuple[str, ...]:
    providers: list[str] = []
    for provider in _string_values(bridge_liveness.get("active_conductor_providers")):
        _append_unique(providers, provider)
    if coerce_bool(bridge_liveness.get("codex_conductor_active")):
        _append_unique(providers, "codex")
    if coerce_bool(bridge_liveness.get("claude_conductor_active")):
        _append_unique(providers, "claude")
    if include_runtime_presence:
        for field_name in (
            "active_runtime_providers",
            "remote_control_active_providers",
            "packet_activity_active_providers",
        ):
            for provider in _string_values(bridge_liveness.get(field_name)):
                _append_unique(providers, provider)
        if coerce_bool(bridge_liveness.get("reviewer_activity_active")):
            provider = str(
                bridge_liveness.get("reviewer_activity_provider") or ""
            ).strip().lower()
            if provider:
                _append_unique(providers, provider)
    return tuple(providers)


def _live_signal_roles(
    bridge_liveness: Mapping[str, object],
    *,
    live_states: frozenset[str],
) -> tuple[tuple[str, str], ...]:
    rows = bridge_liveness.get("session_liveness_signals") or bridge_liveness.get(
        "participant_liveness"
    )
    if not isinstance(rows, (list, tuple)):
        return ()
    result: list[tuple[str, str]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        if str(row.get("state") or "").strip() not in live_states:
            continue
        provider = str(row.get("provider") or "").strip().lower()
        role = str(row.get("role") or "").strip().lower()
        if provider and role:
            result.append((provider, role))
    return tuple(result)


def _first_signal_provider_for_role(
    bridge_liveness: Mapping[str, object],
    role: str,
    *,
    live_states: frozenset[str],
) -> str:
    for provider, signal_role in _live_signal_roles(
        bridge_liveness,
        live_states=live_states,
    ):
        if signal_role == role:
            return provider
    return ""


def _role_for_provider(
    provider: str,
    *,
    bridge_liveness: Mapping[str, object],
    reviewer_provider: str,
    implementer_providers: tuple[str, ...],
) -> str:
    normalized = str(provider or "").strip().lower()
    if normalized == reviewer_provider:
        return TandemRole.REVIEWER.value
    if normalized in implementer_providers:
        return TandemRole.IMPLEMENTER.value
    for signal_provider, signal_role in _live_signal_roles(
        bridge_liveness,
        live_states=RUNTIME_PRESENT_LIVENESS_STATES,
    ):
        if signal_provider == normalized:
            return signal_role
    return role_for_provider(normalized).value


def _capability_provider(payload: Mapping[str, object], field_name: str) -> str:
    capability = payload.get(field_name)
    if not isinstance(capability, Mapping):
        return ""
    return str(capability.get("provider") or "").strip().lower()


def _string_values(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple, set, frozenset)):
        return ()
    return tuple(
        str(item or "").strip().lower()
        for item in value
        if str(item or "").strip()
    )


def _append_unique(values: list[str], value: str) -> None:
    normalized = str(value or "").strip().lower()
    if normalized and normalized not in values:
        values.append(normalized)


__all__ = [
    "LiveRoleTopology",
    "resolve_role_topology",
]
