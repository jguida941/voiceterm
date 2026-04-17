"""Current-session resolution helpers for event-backed projections."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from .current_session_attention import codex_packet_attention_requires_clear
from .current_session_projection import (
    build_bridge_current_session,
    build_event_current_session,
)


@dataclass(frozen=True, slots=True)
class CurrentSessionResolvers:
    """Override hooks for event-backed current-session resolution."""

    build_event_current_session_fn: object = build_event_current_session
    build_bridge_current_session_fn: object = build_bridge_current_session


def resolve_current_session(
    review_state: dict[str, object],
    *,
    repo_root: Path | None = None,
    prior_review_state=None,
    context=None,
    bridge_liveness: dict[str, object],
    resolvers: CurrentSessionResolvers | None = None,
):
    """Resolve current-session authority from typed event state only."""
    if context is not None:
        repo_root = context.repo_root
        prior_review_state = context.prior_review_state
    if repo_root is None:
        raise ValueError("resolve_current_session requires repo_root or context")
    active_resolvers = resolvers or CurrentSessionResolvers()

    current_session = active_resolvers.build_event_current_session_fn(
        review_state=review_state,
        bridge_liveness=bridge_liveness,
        prior_review_state=prior_review_state,
    )
    if codex_packet_attention_requires_clear(review_state):
        current_session = replace(
            current_session,
            current_instruction="",
            current_instruction_revision="",
        )
    return current_session
