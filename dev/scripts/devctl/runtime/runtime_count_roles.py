"""Shared participant-role helpers for runtime count reducers."""

from __future__ import annotations

from collections.abc import Mapping


def participant_role_provider_ids(
    live_participants: list[Mapping[str, object]],
    role_name: str,
    *,
    text_fn,
) -> tuple[str, ...]:
    """Return unique provider ids for one live participant role."""
    providers: list[str] = []
    for row in live_participants:
        if text_fn(row.get("role")) != role_name:
            continue
        provider = text_fn(row.get("provider") or row.get("agent_id"))
        if provider and provider not in providers:
            providers.append(provider)
    return tuple(providers)


__all__ = ["participant_role_provider_ids"]
