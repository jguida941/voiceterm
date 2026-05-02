"""Session coverage helpers for `/develop` peer-mind context."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from .runtime_rows_common import text, work_board_rows

_AGENT_MIND_PROVIDER_IDS = frozenset(("codex", "claude", "cursor"))


def provider_session_counts(review_state: Mapping[str, object]) -> dict[str, int]:
    """Count typed work-board and agent-loop sessions per provider."""
    sessions: dict[str, set[str]] = {}
    for row in work_board_rows(review_state):
        _add_session(
            sessions,
            provider=text(row.get("provider") or row.get("actor_id")),
            session_id=text(row.get("session_id")),
        )
    for row in agent_loop_rows(review_state):
        _add_session(
            sessions,
            provider=text(row.get("actor_id")),
            session_id=text(row.get("session_id")),
        )
    return {provider: len(session_ids) for provider, session_ids in sessions.items()}


def agent_loop_rows(
    review_state: Mapping[str, object],
) -> tuple[Mapping[str, object], ...]:
    rows = review_state.get("agent_loop_decisions")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        return ()
    return tuple(row for row in rows if isinstance(row, Mapping))


def append_provider(providers: list[str], provider: str) -> None:
    """Append a supported provider id once."""
    normalized = provider.strip().lower()
    if normalized in _AGENT_MIND_PROVIDER_IDS and normalized not in providers:
        providers.append(normalized)


def _add_session(
    sessions: dict[str, set[str]],
    *,
    provider: str,
    session_id: str,
) -> None:
    normalized = provider.strip().lower()
    if normalized not in _AGENT_MIND_PROVIDER_IDS or not session_id:
        return
    sessions.setdefault(normalized, set()).add(session_id)


__all__ = ["agent_loop_rows", "append_provider", "provider_session_counts"]
