"""Shared conductor-authority predicates for review-loop recovery decisions."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from ..runtime.role_topology import resolve_role_topology


def normalize_provider_names(value: object) -> tuple[str, ...]:
    """Return stable lower-case provider names from a runtime provider list."""
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes)):
        return ()
    providers: list[str] = []
    for item in value:
        provider = str(item or "").strip().lower()
        if provider and provider not in providers:
            providers.append(provider)
    return tuple(providers)


def live_reviewer_conductor_present(
    bridge_liveness: Mapping[str, object],
    *,
    reviewer_provider: str = "codex",
) -> bool:
    """Return True when typed state proves the repo-owned reviewer conductor."""
    if "reviewer_conductor_active" in bridge_liveness:
        return bool(bridge_liveness.get("reviewer_conductor_active"))
    topology = resolve_role_topology(bridge_liveness)
    if topology.live_reviewer:
        return True
    provider = (reviewer_provider or "codex").strip().lower()
    if not provider:
        return False
    explicit_key = f"{provider}_conductor_active"
    if bool(bridge_liveness.get(explicit_key)):
        return True
    return provider in normalize_provider_names(
        bridge_liveness.get("active_conductor_providers")
    )


def live_implementer_conductor_present(
    bridge_liveness: Mapping[str, object],
) -> bool:
    """Return True when typed state proves any repo-owned implementer conductor."""
    if "implementer_conductor_active" in bridge_liveness:
        return bool(bridge_liveness.get("implementer_conductor_active"))
    return resolve_role_topology(bridge_liveness).live_implementer


def conductor_signal_present(bridge_liveness: Mapping[str, object]) -> bool:
    """Return True when conductor liveness was probed for this snapshot."""
    return any(
        key in bridge_liveness
        for key in (
            "active_conductor_providers",
            "reviewer_conductor_active",
            "implementer_conductor_active",
            "codex_conductor_active",
            "claude_conductor_active",
        )
    )
