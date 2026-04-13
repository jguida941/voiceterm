"""Current-session resolution helpers for event-backed projections."""

from __future__ import annotations

from pathlib import Path

from .core import DEFAULT_BRIDGE_REL
from .handoff import extract_bridge_snapshot


def resolve_current_session(
    *,
    review_state: dict[str, object],
    repo_root: Path,
    prior_review_state,
    bridge_liveness: dict[str, object],
    build_event_current_session_fn,
    build_bridge_current_session_fn,
):
    """Prefer typed event state, but recover bridge instructions when focus is blank."""
    current_session = build_event_current_session_fn(
        review_state=review_state,
        bridge_liveness=bridge_liveness,
        prior_review_state=prior_review_state,
    )
    if current_session.current_instruction.strip() not in {"", "(missing)"}:
        return current_session
    try:
        bridge_snapshot = extract_bridge_snapshot(
            (repo_root / DEFAULT_BRIDGE_REL).read_text(encoding="utf-8")
        )
    except OSError:
        return current_session
    bridge_session = build_bridge_current_session_fn(
        bridge_snapshot,
        bridge_liveness,
        prior_review_state=prior_review_state,
    )
    if bridge_session.current_instruction.strip() not in {"", "(missing)"}:
        return bridge_session
    return current_session
