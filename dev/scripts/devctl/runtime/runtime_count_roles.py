"""Shared participant-role helpers for runtime count reducers."""

from __future__ import annotations

from collections.abc import Mapping


def participant_role_provider_ids(
    live_participants: list[Mapping[str, object] | object],
    role_name: str,
    *,
    text_fn,
) -> tuple[str, ...]:
    """Return unique provider ids for one live participant role."""
    providers: list[str] = []
    for row in live_participants:
        if text_fn(_field(row, "role")) != role_name:
            continue
        provider = text_fn(_field(row, "provider") or _field(row, "agent_id"))
        if provider and provider not in providers:
            providers.append(provider)
    return tuple(providers)


def provider_has_only_non_tandem_presence(
    live_participants: list[Mapping[str, object] | object],
    provider: str,
    *,
    text_fn,
) -> bool:
    """Return True when a provider is live only outside reviewer/implementer roles."""
    normalized_provider = text_fn(provider)
    if not normalized_provider:
        return False
    saw_provider = False
    saw_tandem_role = False
    for row in live_participants:
        row_provider = text_fn(_field(row, "provider") or _field(row, "agent_id"))
        if row_provider != normalized_provider:
            continue
        saw_provider = True
        if text_fn(_field(row, "role")) in {"reviewer", "implementer"}:
            saw_tandem_role = True
            break
    return saw_provider and not saw_tandem_role


def _field(row: Mapping[str, object] | object, key: str) -> object:
    if isinstance(row, Mapping):
        return row.get(key)
    return getattr(row, key, None)


__all__ = [
    "participant_role_provider_ids",
    "provider_has_only_non_tandem_presence",
]
