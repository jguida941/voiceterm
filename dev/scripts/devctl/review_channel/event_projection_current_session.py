"""Current-session resolution helpers for event-backed projections."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from .core import DEFAULT_BRIDGE_REL
from .current_session_attention import codex_packet_attention_requires_clear
from .current_session_projection import (
    build_bridge_current_session,
    build_event_current_session,
)
from .handoff import extract_bridge_snapshot


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
    """Prefer typed event state, but recover bridge instructions when focus is blank."""
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
    if current_session.current_instruction.strip() not in {"", "(missing)"}:
        return current_session
    if _event_session_has_packet_attention(current_session):
        return current_session
    if codex_packet_attention_requires_clear(review_state):
        return current_session
    try:
        bridge_snapshot = extract_bridge_snapshot(
            (repo_root / DEFAULT_BRIDGE_REL).read_text(encoding="utf-8")
        )
    except OSError:
        return current_session
    bridge_session = active_resolvers.build_bridge_current_session_fn(
        bridge_snapshot,
        bridge_liveness,
        prior_review_state=prior_review_state,
    )
    if bridge_session.current_instruction.strip() not in {"", "(missing)"}:
        return bridge_session
    return current_session


def _event_session_has_packet_attention(current_session) -> bool:
    open_findings = str(getattr(current_session, "open_findings", "") or "").strip().lower()
    return open_findings not in {"", "none"}
